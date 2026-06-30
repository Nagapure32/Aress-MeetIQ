import asyncio
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.auth.authorization import require_transcript_access
from app.auth.current_user import CurrentUser

from app.core.config import settings
from app.db.supabase import supabase_gateway
from app.services.meeting_settings import get_dev_user_id
from app.services.transcript_security import decrypt_transcript_segments

MAX_CHUNK_CHARS = 1800
SEARCH_TOP_K = 6
MEETING_WIDE_SOURCE_CHARS = 3600
MEETING_WIDE_CONTEXT_CHARS = 14000
QUERY_STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "asked",
    "ai",
    "by",
    "chat",
    "chats",
    "chatting",
    "did",
    "for",
    "how",
    "in",
    "it",
    "me",
    "meet",
    "meeting",
    "mentioned",
    "of",
    "on",
    "said",
    "say",
    "session",
    "tell",
    "the",
    "this",
    "to",
    "was",
    "were",
    "what",
    "which",
    "who",
}
SPEAKER_TURN_RE = re.compile(
    r"(?:^|(?<=[\s-]))([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,3}):\s*"
)
VALID_CHAT_INTENTS = {
    "agenda",
    "discussion",
    "person_task",
    "specific_fact",
    "summary",
    "task",
    "unknown",
}
VALID_CHAT_RETRIEVALS = {"meeting_wide", "person_focused", "semantic_search"}
VECTOR_STORE_PROVIDER_AZURE = "azure"
VECTOR_STORE_PROVIDER_CHROMA = "chroma"


@dataclass(frozen=True)
class MeetingChatRoute:
    intent: str
    retrieval: str
    person: str | None
    normalized_question: str


class AzureMeetingSearchClient:
    async def upload_documents(self, documents: list[dict[str, Any]]) -> None:
        if not documents:
            return

        await self._ensure_index()
        texts = [document["chunk_text"] for document in documents]
        embeddings = await self._embed_texts(texts)
        upload_documents = [
            {
                "@search.action": "mergeOrUpload",
                **document,
                "content_vector": embeddings[index],
            }
            for index, document in enumerate(documents)
        ]
        await self._post_search(
            f"/indexes/{settings.azure_ai_search_index}/docs/index",
            {"value": upload_documents},
        )

    async def search_meeting_chunks(
        self,
        *,
        meeting_id: str,
        user_id: str,
        query: str,
        top: int,
    ) -> list[dict[str, Any]]:
        vector = (await self._embed_texts([query]))[0]
        payload = {
            "search": query,
            "top": top,
            "filter": (
                f"meeting_id eq '{_escape_odata_string(meeting_id)}' "
                f"and user_id eq '{_escape_odata_string(user_id)}'"
            ),
            "select": "id,meeting_id,user_id,chunk_text,speaker,started_at,ended_at,source_segment_ids",
            "vectorQueries": [
                {
                    "kind": "vector",
                    "vector": vector,
                    "fields": "content_vector",
                    "k": top,
                }
            ],
        }
        data = await self._post_search(
            f"/indexes/{settings.azure_ai_search_index}/docs/search",
            payload,
        )
        return data.get("value", []) if isinstance(data, dict) else []

    async def _ensure_index(self) -> None:
        existing_index = await self._get_search(f"/indexes/{settings.azure_ai_search_index}")
        if existing_index:
            return

        payload = {
            "name": settings.azure_ai_search_index,
            "fields": [
                {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
                {"name": "meeting_id", "type": "Edm.String", "filterable": True},
                {"name": "user_id", "type": "Edm.String", "filterable": True},
                {"name": "chunk_text", "type": "Edm.String", "searchable": True},
                {"name": "speaker", "type": "Edm.String", "filterable": True, "facetable": True},
                {"name": "started_at", "type": "Edm.DateTimeOffset", "filterable": True},
                {"name": "ended_at", "type": "Edm.DateTimeOffset", "filterable": True},
                {"name": "source_segment_ids", "type": "Collection(Edm.String)", "filterable": True},
                {
                    "name": "content_vector",
                    "type": "Collection(Edm.Single)",
                    "searchable": True,
                    "dimensions": settings.azure_openai_embedding_dimensions,
                    "vectorSearchProfile": "meeting-vector-profile",
                },
            ],
            "vectorSearch": {
                "algorithms": [
                    {
                        "name": "meeting-hnsw",
                        "kind": "hnsw",
                    }
                ],
                "profiles": [
                    {
                        "name": "meeting-vector-profile",
                        "algorithm": "meeting-hnsw",
                    }
                ],
            },
        }
        await self._put_search(f"/indexes/{settings.azure_ai_search_index}", payload)

    async def _get_search(self, path: str) -> dict[str, Any] | None:
        url = _azure_search_url(path)
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url, headers=_search_headers())
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return None
        _raise_provider_error(response, "Azure AI Search index lookup failed.")
        return response.json()

    async def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await _embed_texts(texts)

    async def _post_search(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = _azure_search_url(path)
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=_search_headers(), json=payload)
        _raise_provider_error(response, "Azure AI Search request failed.")
        return response.json()

    async def _put_search(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = _azure_search_url(path)
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.put(url, headers=_search_headers(), json=payload)
        _raise_provider_error(response, "Azure AI Search index setup failed.")
        return response.json()


class ChromaMeetingSearchClient:
    def __init__(self) -> None:
        self._collection: Any | None = None

    async def upload_documents(self, documents: list[dict[str, Any]]) -> None:
        if not documents:
            return

        texts = [document["chunk_text"] for document in documents]
        embeddings = await self._embed_texts(texts)
        collection = self._get_collection()

        await asyncio.to_thread(
            collection.upsert,
            ids=[document["id"] for document in documents],
            documents=texts,
            embeddings=embeddings,
            metadatas=[_to_chroma_metadata(document) for document in documents],
        )

    async def search_meeting_chunks(
        self,
        *,
        meeting_id: str,
        user_id: str,
        query: str,
        top: int,
    ) -> list[dict[str, Any]]:
        vector = (await self._embed_texts([query]))[0]
        collection = self._get_collection()
        data = await asyncio.to_thread(
            collection.query,
            query_embeddings=[vector],
            n_results=top,
            where={"$and": [{"meeting_id": meeting_id}, {"user_id": user_id}]},
            include=["documents", "metadatas"],
        )
        return _from_chroma_query_result(data)

    async def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await _embed_texts(texts)

    def _get_collection(self) -> Any:
        if self._collection is not None:
            return self._collection

        try:
            import chromadb
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ChromaDB is not installed. Install the chromadb package.",
            ) from exc

        client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            ssl=settings.chroma_ssl,
        )
        self._collection = client.get_or_create_collection(name=settings.chroma_collection)
        return self._collection


def _get_search_client() -> AzureMeetingSearchClient | ChromaMeetingSearchClient:
    provider = settings.vector_store_provider.strip().lower()
    if provider == VECTOR_STORE_PROVIDER_CHROMA:
        return ChromaMeetingSearchClient()
    return AzureMeetingSearchClient()


search_client = _get_search_client()


async def index_meeting_transcript(
    meeting_id: str,
    user_id: str | None = None,
    current_user: CurrentUser | None = None,
) -> dict[str, Any]:
    _ensure_ai_chat_enabled()
    if current_user is not None:
        await require_transcript_access(current_user, meeting_id)
        user_id = current_user.user_id
        meeting = await _get_meeting(meeting_id)
    else:
        user_id = user_id or get_dev_user_id()
        meeting = await _get_owned_meeting(meeting_id, user_id)
    segments = await _get_transcript_segments(meeting_id)
    if not segments:
        result = await _store_index_status(
            meeting_id,
            user_id,
            "empty",
            indexed_chunk_count=0,
            transcript_segment_count=0,
            error_message="Meeting has no transcript segments to index.",
        )
        return result

    chunks = _build_transcript_chunks(meeting, segments)
    now = datetime.now(UTC).isoformat()
    documents = [
        {
            "id": f"{meeting_id}-{index:04d}",
            "meeting_id": meeting_id,
            "user_id": user_id,
            "chunk_text": chunk["chunk_text"],
            "speaker": chunk.get("speaker"),
            "started_at": chunk.get("started_at"),
            "ended_at": chunk.get("ended_at"),
            "source_segment_ids": chunk["source_segment_ids"],
        }
        for index, chunk in enumerate(chunks)
    ]

    await _store_index_status(
        meeting_id,
        user_id,
        "indexing",
        indexed_chunk_count=0,
        transcript_segment_count=len(segments),
    )
    try:
        await search_client.upload_documents(documents)
    except Exception as exc:
        await _store_index_status(
            meeting_id,
            user_id,
            "failed",
            indexed_chunk_count=0,
            transcript_segment_count=len(segments),
            error_message=str(exc),
        )
        raise

    return await _store_index_status(
        meeting_id,
        user_id,
        "ready",
        indexed_chunk_count=len(documents),
        transcript_segment_count=len(segments),
        indexed_at=now,
    )


async def get_meeting_chat_messages(
    meeting_id: str,
    user_id: str | None = None,
    current_user: CurrentUser | None = None,
) -> list[dict[str, Any]]:
    if current_user is not None:
        await require_transcript_access(current_user, meeting_id)
        user_id = current_user.user_id
    else:
        user_id = user_id or get_dev_user_id()
        await _get_owned_meeting(meeting_id, user_id)
    rows = await supabase_gateway.get(
        "ai_chat_messages",
        {
            "select": "id,meeting_id,user_id,role,content,sources,created_at",
            "meeting_id": f"eq.{meeting_id}",
            "user_id": f"eq.{user_id}",
            "order": "created_at.asc",
            "limit": "200",
        },
    )
    return [_hide_message_sources(row) for row in rows]


async def get_meeting_chat_index_status(
    meeting_id: str,
    user_id: str | None = None,
    current_user: CurrentUser | None = None,
) -> dict[str, Any]:
    if current_user is not None:
        await require_transcript_access(current_user, meeting_id)
        user_id = current_user.user_id
    else:
        user_id = user_id or get_dev_user_id()
        await _get_owned_meeting(meeting_id, user_id)
    rows = await supabase_gateway.get(
        "meeting_ai_indexes",
        {
            "select": "*",
            "meeting_id": f"eq.{meeting_id}",
            "limit": "1",
        },
    )
    if rows:
        return rows[0]
    return {
        "meeting_id": meeting_id,
        "user_id": user_id,
        "status": "not_indexed",
        "indexed_chunk_count": 0,
        "transcript_segment_count": 0,
        "error_message": None,
    }


async def chat_with_meeting_transcript(
    meeting_id: str,
    message: str,
    user_id: str | None = None,
    current_user: CurrentUser | None = None,
) -> dict[str, Any]:
    _ensure_ai_chat_enabled()
    question = " ".join(message.split())
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty.",
        )

    if current_user is not None:
        await require_transcript_access(current_user, meeting_id)
        user_id = current_user.user_id
        meeting = await _get_meeting(meeting_id)
    else:
        user_id = user_id or get_dev_user_id()
        meeting = await _get_owned_meeting(meeting_id, user_id)
    route = _route_meeting_chat_question(question)
    routed_question = route.normalized_question or question
    if route.retrieval == "meeting_wide":
        segments = await _get_transcript_segments(meeting_id)
        focused_sources = _build_meeting_wide_sources(segments)
    elif route.retrieval == "person_focused":
        segments = await _get_transcript_segments(meeting_id)
        focused_sources = _build_person_focused_sources(route, segments)
    else:
        sources = await search_client.search_meeting_chunks(
            meeting_id=meeting_id,
            user_id=user_id,
            query=routed_question,
            top=SEARCH_TOP_K,
        )
        normalized_sources = [_normalize_source(source) for source in sources]
        focused_sources = _focus_sources_on_question(routed_question, normalized_sources)
    if focused_sources:
        try:
            answer = _run_chat_completion(meeting, routed_question, focused_sources)
        except HTTPException as exc:
            if not _is_azure_content_filter_error(exc):
                raise
            answer = _build_content_filter_fallback_answer(routed_question, focused_sources)
    else:
        answer = "I could not find transcript context for this meeting that answers that question."

    await _save_chat_message(meeting_id, user_id, "user", question, [])
    await _save_chat_message(meeting_id, user_id, "assistant", answer, [])

    return {
        "meeting_id": meeting_id,
        "answer": answer,
        "sources": [],
    }


def _run_chat_completion(
    meeting: dict[str, Any],
    question: str,
    sources: list[dict[str, Any]],
) -> str:
    _ensure_ai_chat_enabled()
    context = "\n\n".join(
        (
            f"Source {index + 1}\n"
            f"Speaker: {source.get('speaker') or 'Unknown speaker'}\n"
            f"Time: {source.get('started_at') or 'unknown'}\n"
            f"Text: {source.get('chunk_text') or ''}"
        )
        for index, source in enumerate(sources)
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You answer questions about one selected meeting transcript. "
                "Use only the provided transcript sources. If the sources do not answer the question, "
                "say that the transcript does not contain enough information. Keep the answer to one "
                "or two short sentences. Do not include source numbers or long transcript quotes unless "
                "the user asks for exact wording. For agenda, discussion, summary, or task questions, "
                "infer the answer from the transcript even when the transcript does not literally use "
                "those words. Mention responsible people when the transcript indicates them. For task "
                "questions, list the concrete tasks or say no task was clearly assigned."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Meeting: {meeting.get('subject') or 'Untitled meeting'}\n\n"
                f"Transcript sources:\n{context}\n\n"
                f"Question: {question}"
            ),
        },
    ]
    url = _azure_openai_url(settings.azure_openai_deployment, "chat/completions")
    with httpx.Client(timeout=60) as client:
        response = client.post(
            url,
            headers={"api-key": settings.azure_openai_api_key},
            json={"messages": messages, "temperature": 0.2},
        )
    _raise_provider_error(response, "Azure OpenAI chat request failed.")
    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Azure OpenAI returned an unexpected chat response.",
        ) from exc
    return str(content).strip()


def _build_content_filter_fallback_answer(question: str, sources: list[dict[str, Any]]) -> str:
    evidence = _matching_source_evidence(question, sources)
    if evidence:
        speaker_text = _format_speaker_list([item["speaker"] for item in evidence])
        transcript_lines = "\n".join(
            f"- {item['speaker']}: {item['text']}" for item in evidence[:3]
        )
        return (
            "Azure OpenAI content policy filtered the generated answer, so I answered directly "
            f"from the matching transcript lines. {speaker_text} mentioned it.\n\n"
            f"{transcript_lines}"
        )
    return (
        "Azure OpenAI content policy filtered the generated answer for this transcript context. "
        "I found related transcript sources, but could not identify a speaker from them."
    )


def _matching_source_speakers(question: str, sources: list[dict[str, Any]]) -> list[str]:
    return [item["speaker"] for item in _matching_source_evidence(question, sources)]


def _route_meeting_chat_question(question: str) -> MeetingChatRoute:
    try:
        from agno.agent import Agent
        from agno.models.azure import AzureOpenAI
    except ImportError:
        return _semantic_search_route(question)

    agent = Agent(
        model=AzureOpenAI(
            id=settings.azure_openai_deployment,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
            azure_deployment=settings.azure_openai_deployment,
        ),
        instructions=[
            "You route meeting transcript chat questions for retrieval.",
            "Return only valid JSON with keys: intent, retrieval, person, normalized_question.",
            "intent must be one of: agenda, discussion, person_task, specific_fact, summary, task, unknown.",
            "retrieval must be one of: meeting_wide, person_focused, semantic_search.",
            "Use meeting_wide for agenda, summary, discussion, topics, overall meeting, and general task/action-item questions.",
            "Use person_focused when the question asks what a named person said, did, owns, or was assigned.",
            "Use semantic_search for narrow factual questions.",
            "person must be the named person if present, otherwise null.",
            "normalized_question should fix spelling and grammar while preserving meaning.",
        ],
    )
    try:
        response = agent.run(
            "Route this meeting transcript question.\n\n"
            f"Question: {question}\n\n"
            "Return JSON only."
        )
    except Exception:
        return _semantic_search_route(question)

    return _parse_chat_route(str(getattr(response, "content", response)), question)


def _parse_chat_route(content: str, original_question: str) -> MeetingChatRoute:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(cleaned)
    except (TypeError, json.JSONDecodeError):
        return _semantic_search_route(original_question)
    if not isinstance(data, dict):
        return _semantic_search_route(original_question)

    intent = str(data.get("intent") or "unknown").strip().lower()
    retrieval = str(data.get("retrieval") or "semantic_search").strip().lower()
    if intent not in VALID_CHAT_INTENTS:
        intent = "unknown"
    if retrieval not in VALID_CHAT_RETRIEVALS:
        retrieval = "semantic_search"

    person_value = data.get("person")
    person = str(person_value).strip() if person_value else None
    if retrieval == "person_focused" and not person:
        retrieval = "meeting_wide"
    normalized_question = str(data.get("normalized_question") or original_question).strip()
    return MeetingChatRoute(
        intent=intent,
        retrieval=retrieval,
        person=person,
        normalized_question=normalized_question or original_question,
    )


def _semantic_search_route(question: str) -> MeetingChatRoute:
    return MeetingChatRoute(
        intent="specific_fact",
        retrieval="semantic_search",
        person=None,
        normalized_question=question,
    )


def _build_meeting_wide_sources(
    segments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lines = _meeting_wide_lines(segments)
    return _build_sources_from_lines(lines)


def _build_sources_from_lines(lines: list[tuple[str, str]]) -> list[dict[str, Any]]:
    if not lines:
        return []

    sources: list[dict[str, Any]] = []
    current_lines: list[str] = []
    current_ids: list[str] = []
    current_length = 0
    total_length = 0

    def flush() -> None:
        nonlocal current_lines, current_ids, current_length
        if not current_lines:
            return
        sources.append(
            {
                "id": f"meeting-wide-{len(sources):03d}",
                "chunk_text": "\n".join(current_lines),
                "speaker": None,
                "started_at": None,
                "ended_at": None,
                "source_segment_ids": current_ids,
            }
        )
        current_lines = []
        current_ids = []
        current_length = 0

    for segment_id, line in lines:
        if total_length >= MEETING_WIDE_CONTEXT_CHARS:
            break
        line_length = len(line) + 1
        if current_lines and current_length + line_length > MEETING_WIDE_SOURCE_CHARS:
            flush()
        current_lines.append(line)
        current_ids.append(segment_id)
        current_length += line_length
        total_length += line_length

    flush()
    return sources


def _build_person_focused_sources(
    route: MeetingChatRoute,
    segments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    person = (route.person or "").lower()
    lines = _meeting_wide_lines(segments)
    if not person:
        return _build_meeting_wide_sources(segments)
    selected_indexes: set[int] = set()
    for index, (_segment_id, line) in enumerate(lines):
        if person in line.lower():
            selected_indexes.update(
                nearby_index
                for nearby_index in range(max(0, index - 1), min(len(lines), index + 2))
            )

    if not selected_indexes:
        return _build_meeting_wide_sources(segments)
    selected_lines = [line for index, line in enumerate(lines) if index in selected_indexes]
    return _build_sources_from_lines(selected_lines)


def _meeting_wide_lines(
    segments: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    return [
        (
            str(segment.get("id") or ""),
            f"{segment.get('speaker') or 'Unknown speaker'}: {str(segment.get('text') or '').strip()}",
        )
        for segment in segments
        if str(segment.get("text") or "").strip()
    ]


def _focus_sources_on_question(
    question: str,
    sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    terms = _query_terms(question)
    if not terms:
        return sources

    focused_sources: list[dict[str, Any]] = []
    for source in sources:
        turns = _source_turns(str(source.get("chunk_text") or ""))
        matching_turns = [turn for turn in turns if _line_matches_terms(turn["line"], terms)]
        if not matching_turns:
            focused_sources.append(source)
            continue

        speakers = [turn["speaker"] for turn in matching_turns if turn["speaker"]]
        focused_source = {
            **source,
            "chunk_text": "\n".join(turn["line"] for turn in matching_turns),
        }
        unique_speakers = list(dict.fromkeys(speakers))
        if len(unique_speakers) == 1:
            focused_source["speaker"] = unique_speakers[0]
        focused_sources.append(focused_source)

    return focused_sources


def _matching_source_evidence(question: str, sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    terms = _query_terms(question)
    evidence: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for source in sources:
        text = str(source.get("chunk_text") or "")
        speaker = source.get("speaker")
        if terms:
            matching_turns = [
                turn for turn in _source_turns(text) if _line_matches_terms(turn["line"], terms)
            ]
        else:
            matching_turns = _source_turns(text)
        if not matching_turns and speaker and (not terms or _line_matches_terms(text, terms)):
            matching_turns = [{"speaker": str(speaker), "text": text, "line": text}]
        for turn in matching_turns:
            candidate = turn["speaker"] or (str(speaker) if speaker else None)
            if not candidate:
                continue
            cleaned_text = _clean_transcript_text(turn["text"] or turn["line"])
            key = (candidate, cleaned_text)
            if cleaned_text and key not in seen:
                seen.add(key)
                evidence.append({"speaker": candidate, "text": cleaned_text})
    return evidence


def _query_terms(question: str) -> list[str]:
    return [
        term
        for term in re.findall(r"[a-z0-9]+", question.lower())
        if len(term) > 2 and term not in QUERY_STOPWORDS
    ]


def _line_speaker(line: str) -> str | None:
    speaker, _text = _split_transcript_line(line)
    return speaker


def _hide_message_sources(message: dict[str, Any]) -> dict[str, Any]:
    return {**message, "sources": []}


def _source_turns(text: str) -> list[dict[str, str]]:
    turns: list[dict[str, str]] = []
    for line in text.splitlines() or [text]:
        line_turns = _split_speaker_turns(line)
        if line_turns:
            turns.extend(line_turns)
            continue
        speaker, line_text = _split_transcript_line(line)
        turns.append({"speaker": speaker or "", "text": line_text, "line": line.strip()})
    return [turn for turn in turns if str(turn.get("line") or "").strip()]


def _split_speaker_turns(text: str) -> list[dict[str, str]]:
    matches = list(SPEAKER_TURN_RE.finditer(text))
    if not matches:
        return []

    turns: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        speaker = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        turn_text = text[start:end].strip()
        if turn_text:
            turns.append(
                {
                    "speaker": speaker,
                    "text": turn_text,
                    "line": f"{speaker}: {turn_text}",
                }
            )
    return turns


def _split_transcript_line(line: str) -> tuple[str | None, str]:
    speaker, separator, text = line.partition(":")
    if not separator:
        return None, line.strip()
    speaker = speaker.strip()
    return speaker or None, text.strip()


def _line_matches_terms(line: str, terms: list[str]) -> bool:
    line_text = line.lower()
    return any(term in line_text for term in terms)


def _clean_transcript_text(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= 260:
        return cleaned
    return f"{cleaned[:257].rstrip()}..."


def _format_speaker_list(speakers: list[str]) -> str:
    unique_speakers = list(dict.fromkeys(speakers))
    if not unique_speakers:
        return "The matching transcript lines"
    if len(unique_speakers) == 1:
        return unique_speakers[0]
    if len(unique_speakers) == 2:
        return f"{unique_speakers[0]} and {unique_speakers[1]}"
    return f"{', '.join(unique_speakers[:-1])}, and {unique_speakers[-1]}"



async def _get_meeting(meeting_id: str) -> dict[str, Any]:
    rows = await supabase_gateway.get(
        "meetings",
        {
            "select": "id,user_id,subject,start_time,end_time,organizer_email",
            "id": f"eq.{meeting_id}",
            "limit": "1",
        },
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found.")
    return rows[0]
async def _get_owned_meeting(meeting_id: str, user_id: str) -> dict[str, Any]:
    rows = await supabase_gateway.get(
        "meetings",
        {
            "select": "id,user_id,subject,start_time,end_time,organizer_email",
            "id": f"eq.{meeting_id}",
            "user_id": f"eq.{user_id}",
            "limit": "1",
        },
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found.")
    return rows[0]


async def _get_transcript_segments(meeting_id: str) -> list[dict[str, Any]]:
    rows = await supabase_gateway.get(
        "transcript_segments",
        {
            "select": (
                "id,sequence,speaker,source_id,language,text,encrypted_text,encryption_alg,"
                "encryption_key_id,started_at,ended_at,created_at"
            ),
            "meeting_id": f"eq.{meeting_id}",
            "order": "sequence.asc.nullslast,started_at.asc.nullslast,created_at.asc",
            "limit": "1000",
        },
    )
    return decrypt_transcript_segments(rows)


def _build_transcript_chunks(
    meeting: dict[str, Any],
    segments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_lines: list[str] = []
    current_ids: list[str] = []
    current_speaker: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    current_length = 0

    def flush() -> None:
        nonlocal current_lines, current_ids, current_speaker, started_at, ended_at, current_length
        if not current_lines:
            return
        chunks.append(
            {
                "chunk_text": "\n".join(current_lines),
                "speaker": current_speaker,
                "started_at": started_at,
                "ended_at": ended_at,
                "source_segment_ids": current_ids,
            }
        )
        current_lines = []
        current_ids = []
        current_speaker = None
        started_at = None
        ended_at = None
        current_length = 0

    for segment in segments:
        text = str(segment.get("text") or "").strip()
        if not text:
            continue
        speaker = str(segment.get("speaker") or "Unknown speaker")
        line = f"{speaker}: {text}"
        if current_lines and current_length + len(line) + 1 > MAX_CHUNK_CHARS:
            flush()
        if not current_lines:
            current_speaker = speaker
            started_at = segment.get("started_at") or segment.get("created_at")
        current_lines.append(line)
        current_ids.append(str(segment.get("id")))
        ended_at = segment.get("ended_at") or segment.get("created_at")
        current_length += len(line) + 1

    flush()
    return chunks


async def _save_chat_message(
    meeting_id: str,
    user_id: str,
    role: str,
    content: str,
    sources: list[dict[str, Any]],
) -> None:
    await supabase_gateway.insert(
        "ai_chat_messages",
        {
            "meeting_id": meeting_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "sources": sources,
        },
    )


async def _store_index_status(
    meeting_id: str,
    user_id: str,
    status_value: str,
    *,
    indexed_chunk_count: int,
    transcript_segment_count: int,
    error_message: str | None = None,
    indexed_at: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    payload = {
        "meeting_id": meeting_id,
        "user_id": user_id,
        "status": status_value,
        "indexed_chunk_count": indexed_chunk_count,
        "transcript_segment_count": transcript_segment_count,
        "error_message": error_message,
        "updated_at": now,
    }
    if indexed_at:
        payload["indexed_at"] = indexed_at
    rows = await supabase_gateway.upsert(
        "meeting_ai_indexes",
        payload,
        on_conflict="meeting_id",
    )
    return rows[0] if rows else payload


def _normalize_source(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(source.get("id") or ""),
        "chunk_text": str(source.get("chunk_text") or ""),
        "speaker": source.get("speaker"),
        "started_at": source.get("started_at"),
        "ended_at": source.get("ended_at"),
        "source_segment_ids": list(source.get("source_segment_ids") or []),
    }


async def _embed_texts(texts: list[str]) -> list[list[float]]:
    _ensure_ai_chat_enabled()
    url = _azure_openai_url(settings.azure_openai_embedding_deployment, "embeddings")
    payload = {
        "input": texts,
        "dimensions": settings.azure_openai_embedding_dimensions,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            url,
            headers={"api-key": settings.azure_openai_api_key},
            json=payload,
        )
    _raise_provider_error(response, "Azure OpenAI embedding request failed.")
    data = response.json()
    embeddings = [
        item.get("embedding")
        for item in sorted(data.get("data", []), key=lambda item: item.get("index", 0))
    ]
    if len(embeddings) != len(texts) or any(not isinstance(item, list) for item in embeddings):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Azure OpenAI returned an unexpected embedding response.",
        )
    return embeddings


def _to_chroma_metadata(document: dict[str, Any]) -> dict[str, str]:
    metadata: dict[str, str] = {
        "meeting_id": str(document.get("meeting_id") or ""),
        "user_id": str(document.get("user_id") or ""),
        "source_segment_ids_json": json.dumps(document.get("source_segment_ids") or []),
    }
    for key in ("speaker", "started_at", "ended_at"):
        value = document.get(key)
        if value is not None:
            metadata[key] = str(value)
    return metadata


def _from_chroma_query_result(data: dict[str, Any]) -> list[dict[str, Any]]:
    ids = _first_chroma_result_group(data.get("ids"))
    documents = _first_chroma_result_group(data.get("documents"))
    metadatas = _first_chroma_result_group(data.get("metadatas"))
    results: list[dict[str, Any]] = []

    for index, metadata in enumerate(metadatas):
        if not isinstance(metadata, dict):
            metadata = {}
        source_segment_ids = _parse_chroma_source_segment_ids(
            metadata.get("source_segment_ids_json")
        )
        results.append(
            {
                "id": str(ids[index] if index < len(ids) else ""),
                "meeting_id": str(metadata.get("meeting_id") or ""),
                "user_id": str(metadata.get("user_id") or ""),
                "chunk_text": str(documents[index] if index < len(documents) else ""),
                "speaker": metadata.get("speaker") or None,
                "started_at": metadata.get("started_at") or None,
                "ended_at": metadata.get("ended_at") or None,
                "source_segment_ids": source_segment_ids,
            }
        )
    return results


def _first_chroma_result_group(value: Any) -> list[Any]:
    if not isinstance(value, list) or not value:
        return []
    first = value[0]
    return first if isinstance(first, list) else []


def _parse_chroma_source_segment_ids(value: Any) -> list[str]:
    if not isinstance(value, str) or not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _ensure_ai_chat_enabled() -> None:
    if not settings.enable_ai_chat:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI chat is disabled. Set ENABLE_AI_CHAT=true.",
        )
    missing = [
        name
        for name, value in {
            "AZURE_OPENAI_ENDPOINT": settings.azure_openai_endpoint,
            "AZURE_OPENAI_API_KEY": settings.azure_openai_api_key,
            "AZURE_OPENAI_DEPLOYMENT": settings.azure_openai_deployment,
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": settings.azure_openai_embedding_deployment,
        }.items()
        if not value
    ]
    provider = settings.vector_store_provider.strip().lower()
    if provider == VECTOR_STORE_PROVIDER_AZURE:
        missing.extend(
            name
            for name, value in {
                "AZURE_AI_SEARCH_ENDPOINT": settings.azure_ai_search_endpoint,
                "AZURE_AI_SEARCH_API_KEY": settings.azure_ai_search_api_key,
                "AZURE_AI_SEARCH_INDEX": settings.azure_ai_search_index,
            }.items()
            if not value
        )
    elif provider == VECTOR_STORE_PROVIDER_CHROMA:
        missing.extend(
            name
            for name, value in {
                "CHROMA_HOST": settings.chroma_host,
                "CHROMA_COLLECTION": settings.chroma_collection,
            }.items()
            if not value
        )
    else:
        missing.append("VECTOR_STORE_PROVIDER must be azure or chroma")
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI chat is missing configuration: {', '.join(missing)}.",
        )


def _azure_openai_url(deployment: str, operation: str) -> str:
    endpoint = settings.azure_openai_endpoint.rstrip("/")
    return (
        f"{endpoint}/openai/deployments/{deployment}/{operation}"
        f"?api-version={settings.azure_openai_api_version}"
    )


def _azure_search_url(path: str) -> str:
    endpoint = settings.azure_ai_search_endpoint.rstrip("/")
    separator = "&" if "?" in path else "?"
    return f"{endpoint}{path}{separator}api-version={settings.azure_ai_search_api_version}"


def _search_headers() -> dict[str, str]:
    return {
        "api-key": settings.azure_ai_search_api_key,
        "Content-Type": "application/json",
    }


def _raise_provider_error(response: httpx.Response, message: str) -> None:
    if response.status_code < 400:
        return
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "message": message,
            "status_code": response.status_code,
            "response": response.text,
        },
    )


def _is_azure_content_filter_error(exc: HTTPException) -> bool:
    detail = exc.detail
    if not isinstance(detail, dict):
        return False
    response_text = str(detail.get("response") or "")
    return (
        str(detail.get("message") or "") == "Azure OpenAI chat request failed."
        and (
            "content_filter" in response_text
            or "ResponsibleAIPolicyViolation" in response_text
        )
    )


def _escape_odata_string(value: str) -> str:
    return value.replace("'", "''")
