import asyncio

import pytest
from fastapi import HTTPException


class FakeSupabaseGateway:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict]] = {
            "meetings": [],
            "transcript_segments": [],
            "ai_chat_messages": [],
            "meeting_ai_indexes": [],
        }

    async def get(self, path: str, params: dict | None = None) -> list[dict]:
        rows = [row.copy() for row in self.tables[path]]
        if not params:
            return rows

        for key, value in params.items():
            if key in {"select", "order", "limit"}:
                continue
            if isinstance(value, str) and value.startswith("eq."):
                expected = value[3:]
                rows = [row for row in rows if str(row.get(key)) == expected]

        if params.get("limit"):
            rows = rows[: int(params["limit"])]
        return rows

    async def insert(self, path: str, payload: dict | list[dict]) -> list[dict]:
        payloads = payload if isinstance(payload, list) else [payload]
        rows = []
        for item in payloads:
            row = item.copy()
            row.setdefault("id", f"{path}-{len(self.tables[path]) + 1}")
            self.tables[path].append(row)
            rows.append(row.copy())
        return rows

    async def upsert(
        self,
        path: str,
        payload: dict,
        on_conflict: str | None = None,
    ) -> list[dict]:
        if on_conflict:
            existing = [
                row for row in self.tables[path] if row.get(on_conflict) == payload.get(on_conflict)
            ]
            if existing:
                existing[0].update(payload)
                return [existing[0].copy()]
        return await self.insert(path, payload)


class FakeSearchClient:
    def __init__(self) -> None:
        self.uploaded_documents: list[dict] = []
        self.search_calls: list[dict] = []
        self.results: list[dict] = []

    async def upload_documents(self, documents: list[dict]) -> None:
        self.uploaded_documents.extend(documents)

    async def search_meeting_chunks(
        self,
        *,
        meeting_id: str,
        user_id: str,
        query: str,
        top: int,
    ) -> list[dict]:
        self.search_calls.append(
            {
                "meeting_id": meeting_id,
                "user_id": user_id,
                "query": query,
                "top": top,
            }
        )
        return self.results


def run(coro):
    return asyncio.run(coro)


def test_index_meeting_transcript_uploads_meeting_scoped_chunks(monkeypatch):
    from app.services import meeting_chat

    fake_db = FakeSupabaseGateway()
    fake_search = FakeSearchClient()
    fake_db.tables["meetings"] = [
        {
            "id": "meeting-1",
            "user_id": "user-1",
            "subject": "Launch sync",
        }
    ]
    fake_db.tables["transcript_segments"] = [
        {
            "id": "segment-1",
            "meeting_id": "meeting-1",
            "speaker": "Asha",
            "text": "The launch stays on Friday.",
            "created_at": "2026-05-20T10:00:00Z",
        },
        {
            "id": "segment-2",
            "meeting_id": "meeting-1",
            "speaker": "Ravi",
            "text": "Ravi will send the customer email.",
            "created_at": "2026-05-20T10:01:00Z",
        },
    ]
    monkeypatch.setattr(meeting_chat, "supabase_gateway", fake_db)
    monkeypatch.setattr(meeting_chat, "get_dev_user_id", lambda: "user-1")
    monkeypatch.setattr(meeting_chat, "search_client", fake_search)
    monkeypatch.setattr(meeting_chat, "_ensure_ai_chat_enabled", lambda: None)

    result = run(meeting_chat.index_meeting_transcript("meeting-1"))

    assert result["status"] == "ready"
    assert result["indexed_chunk_count"] == 1
    assert fake_search.uploaded_documents[0]["meeting_id"] == "meeting-1"
    assert fake_search.uploaded_documents[0]["user_id"] == "user-1"
    assert fake_search.uploaded_documents[0]["source_segment_ids"] == ["segment-1", "segment-2"]
    assert fake_db.tables["meeting_ai_indexes"][0]["status"] == "ready"


def test_chat_with_meeting_transcript_saves_history_and_sources(monkeypatch):
    from app.services import meeting_chat

    fake_db = FakeSupabaseGateway()
    fake_search = FakeSearchClient()
    fake_db.tables["meetings"] = [
        {
            "id": "meeting-1",
            "user_id": "user-1",
            "subject": "Launch sync",
        }
    ]
    fake_search.results = [
        {
            "id": "meeting-1-000",
            "meeting_id": "meeting-1",
            "chunk_text": "Asha: The launch stays on Friday.",
            "speaker": "Asha",
            "source_segment_ids": ["segment-1"],
            "started_at": "2026-05-20T10:00:00Z",
            "ended_at": "2026-05-20T10:00:00Z",
        }
    ]
    monkeypatch.setattr(meeting_chat, "supabase_gateway", fake_db)
    monkeypatch.setattr(meeting_chat, "get_dev_user_id", lambda: "user-1")
    monkeypatch.setattr(meeting_chat, "search_client", fake_search)
    monkeypatch.setattr(meeting_chat, "_ensure_ai_chat_enabled", lambda: None)
    monkeypatch.setattr(
        meeting_chat,
        "_run_chat_completion",
        lambda meeting, question, sources: "The launch stays on Friday.",
    )

    result = run(meeting_chat.chat_with_meeting_transcript("meeting-1", "When is launch?"))

    assert result["answer"] == "The launch stays on Friday."
    assert result["sources"][0]["source_segment_ids"] == ["segment-1"]
    assert fake_search.search_calls[0]["meeting_id"] == "meeting-1"
    assert fake_search.search_calls[0]["user_id"] == "user-1"
    assert fake_db.tables["ai_chat_messages"][0]["role"] == "user"
    assert fake_db.tables["ai_chat_messages"][0]["meeting_id"] == "meeting-1"
    assert fake_db.tables["ai_chat_messages"][1]["role"] == "assistant"
    assert fake_db.tables["ai_chat_messages"][1]["sources"] == result["sources"]


def test_chat_rejects_meeting_for_different_user(monkeypatch):
    from app.services import meeting_chat

    fake_db = FakeSupabaseGateway()
    fake_db.tables["meetings"] = [
        {
            "id": "meeting-1",
            "user_id": "other-user",
            "subject": "Private sync",
        }
    ]
    monkeypatch.setattr(meeting_chat, "supabase_gateway", fake_db)
    monkeypatch.setattr(meeting_chat, "get_dev_user_id", lambda: "user-1")
    monkeypatch.setattr(meeting_chat, "_ensure_ai_chat_enabled", lambda: None)

    with pytest.raises(HTTPException) as exc:
        run(meeting_chat.chat_with_meeting_transcript("meeting-1", "What happened?"))

    assert exc.value.status_code == 404
