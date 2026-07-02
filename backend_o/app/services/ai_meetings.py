import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.db.supabase import supabase_gateway
from app.services.assignee_resolution import is_first_person_assignee, resolve_assignee
from app.services.task_email import TaskEmailResult, send_task_assignment_email

VALID_PRIORITIES = {"low", "medium", "high", "urgent"}


@dataclass(frozen=True)
class MeetingAITask:
    title: str
    description: str | None = None
    priority: str = "medium"
    due_date: str | None = None
    assignee_name: str | None = None
    evidence_segment_sequence: int | None = None


@dataclass(frozen=True)
class MeetingAIResult:
    summary: str
    key_points: list[str]
    decisions: list[str]
    tasks: list[MeetingAITask]


async def generate_meeting_intelligence(meeting_id: str) -> dict[str, Any]:
    meeting = await _get_meeting_for_ai(meeting_id)
    transcript_segments = await _get_transcript_segments(meeting_id)
    if not transcript_segments:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Meeting has no transcript segments to analyze.",
        )

    ai_result = _run_agno_meeting_agent(meeting, transcript_segments)
    participants = await _get_meeting_participants(meeting_id)
    profiles = await _get_profiles_for_participants(participants)
    summary = await _store_summary(meeting_id, ai_result)
    action_items, created_count, skipped_action_items_count = await _store_action_items(
        meeting,
        transcript_segments,
        ai_result.tasks,
        participants,
        profiles,
    )
    tasks, skipped_tasks_count = await _store_tasks_for_calendar_user(meeting, action_items)

    return {
        "meeting_id": meeting_id,
        "summary": summary,
        "generated_tasks_count": len(ai_result.tasks),
        "created_action_items_count": created_count,
        "skipped_action_items_count": skipped_action_items_count,
        "created_tasks_count": len(tasks),
        "skipped_tasks_count": skipped_tasks_count,
        "tasks": tasks,
    }


async def _get_meeting_for_ai(meeting_id: str) -> dict[str, Any]:
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
    meeting = rows[0]
    if not meeting.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Meeting is missing a calendar user.",
        )
    return meeting


async def _get_transcript_segments(meeting_id: str) -> list[dict[str, Any]]:
    return await supabase_gateway.get(
        "transcript_segments",
        {
            "select": (
                "id,sequence,speaker,source_id,speaker_participant_id,speaker_aad_user_id,"
                "speaker_email,speaker_user_principal_name,text,created_at,started_at,ended_at"
            ),
            "meeting_id": f"eq.{meeting_id}",
            "order": "sequence.asc.nullslast,started_at.asc.nullslast,created_at.asc",
            "limit": "1000",
        },
    )


def _run_agno_meeting_agent(
    meeting: dict[str, Any],
    transcript_segments: list[dict[str, Any]],
) -> MeetingAIResult:
    if not settings.enable_ai_summaries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI summaries are disabled. Set ENABLE_AI_SUMMARIES=true.",
        )
    if (
        not settings.azure_openai_api_key
        or not settings.azure_openai_endpoint
        or not settings.azure_openai_deployment
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Azure OpenAI is not configured.",
        )
    try:
        from agno.agent import Agent
        from agno.models.azure import AzureOpenAI
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agno is not installed. Install backend AI dependencies first.",
        ) from exc

    agent = Agent(
        model=AzureOpenAI(
            id=settings.azure_openai_deployment,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
            azure_deployment=settings.azure_openai_deployment,
        ),
        instructions=[
            "You identify meeting outcomes for a productivity app.",
            "Return only valid JSON with keys: summary, key_points, decisions, tasks.",
            (
                "tasks must be an array of objects with title, description, priority, "
                "due_date, assignee_name, evidence_segment_sequence."
            ),
            (
                "assignee_name must be the person who accepted or was assigned the work. "
                "Use I/me when the speaker assigned work to themselves."
            ),
            (
                "evidence_segment_sequence must be the transcript segment sequence number "
                "that proves the assignment."
            ),
            (
                "Do not invent assignees. Use null for assignee_name when the transcript "
                "does not say who owns the work."
            ),
            "priority must be one of low, medium, high, urgent.",
            "Use null for due_date unless the transcript gives a clear date.",
        ],
    )
    try:
        response = agent.run(_meeting_prompt(meeting, transcript_segments))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Azure OpenAI request failed. Check AZURE_OPENAI_ENDPOINT, "
                "AZURE_OPENAI_DEPLOYMENT, and AZURE_OPENAI_API_VERSION. "
                f"Configured deployment: {settings.azure_openai_deployment}. "
                f"Provider error: {exc}"
            ),
        ) from exc

    content = getattr(response, "content", response)
    if not content or str(content).strip().lower() in {"none", "null"}:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Azure OpenAI did not return usable content. Check that "
                f"deployment '{settings.azure_openai_deployment}' exists on "
                "the configured Azure OpenAI endpoint."
            ),
        )
    return _parse_ai_result(str(content))


def _meeting_prompt(meeting: dict[str, Any], transcript_segments: list[dict[str, Any]]) -> str:
    transcript = "\n".join(
        (
            f"[{segment.get('sequence')}] "
            f"{segment.get('speaker') or 'Unknown speaker'}: {segment.get('text') or ''}"
        )
        for segment in transcript_segments
    )
    return (
        f"Meeting subject: {meeting.get('subject') or 'Untitled meeting'}\n\n"
        "Transcript:\n"
        f"{transcript}"
    )


def _parse_ai_result(content: str) -> MeetingAIResult:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        preview = cleaned[:240] if cleaned else "<empty>"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "AI response was not valid JSON. Check the Azure OpenAI deployment "
                f"and model output. Response preview: {preview}"
            ),
        ) from exc
    tasks = [
        MeetingAITask(
            title=str(task.get("title", "")).strip(),
            description=task.get("description"),
            priority=_normalize_priority(task.get("priority")),
            due_date=task.get("due_date"),
            assignee_name=task.get("assignee_name"),
            evidence_segment_sequence=_parse_optional_int(task.get("evidence_segment_sequence")),
        )
        for task in data.get("tasks", [])
        if str(task.get("title", "")).strip()
    ]
    return MeetingAIResult(
        summary=str(data.get("summary") or ""),
        key_points=[str(item) for item in data.get("key_points", [])],
        decisions=[str(item) for item in data.get("decisions", [])],
        tasks=tasks,
    )


async def _store_summary(meeting_id: str, ai_result: MeetingAIResult) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    rows = await supabase_gateway.upsert(
        "meeting_summaries",
        {
            "meeting_id": meeting_id,
            "summary": ai_result.summary,
            "key_points": ai_result.key_points,
            "decisions": ai_result.decisions,
            "model": f"agno:{settings.azure_openai_deployment}",
            "updated_at": now,
        },
        on_conflict="meeting_id",
    )
    return rows[0] if rows else {"meeting_id": meeting_id, "summary": ai_result.summary}


async def _store_action_items(
    meeting: dict[str, Any],
    transcript_segments: list[dict[str, Any]],
    ai_tasks: list[MeetingAITask],
    participants: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, int]:
    if not ai_tasks:
        return [], 0, 0

    existing_by_title = await _existing_by_title("action_items", meeting["id"])
    payloads = []
    action_items = []
    skipped_count = 0
    for task in ai_tasks:
        existing = existing_by_title.get(_normalize_title(task.title))
        if existing:
            enriched_existing = await _enrich_action_item_assignee(
                existing,
                task,
                transcript_segments,
                participants,
                profiles,
            )
            action_items.append(enriched_existing)
            skipped_count += 1
            continue
        evidence_segment, resolution = _resolve_task_assignee(
            task,
            transcript_segments,
            participants,
            profiles,
        )
        payloads.append(
            {
                "meeting_id": meeting["id"],
                "assignee_user_id": resolution.user_id,
                "assignee_display_name": resolution.display_name or task.assignee_name,
                "assignee_email": resolution.email,
                "assignee_resolution_status": resolution.status,
                "assignee_resolution_confidence": resolution.confidence,
                "assignee_resolution_reason": resolution.reason,
                "title": task.title,
                "description": task.description,
                "status": "open",
                "priority": _normalize_priority(task.priority),
                "due_date": task.due_date,
                "source_transcript_segment_id": (
                    evidence_segment.get("id") if evidence_segment else None
                ),
            }
        )
    created = await supabase_gateway.insert("action_items", payloads) if payloads else []
    return [*action_items, *created], len(created), skipped_count


def _resolve_task_assignee(
    task: MeetingAITask,
    transcript_segments: list[dict[str, Any]],
    participants: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    assignee_name_override: str | None = None,
) -> tuple[dict[str, Any] | None, Any]:
    assignee_name = assignee_name_override or task.assignee_name
    evidence_segment = _find_evidence_segment(
        transcript_segments,
        task.evidence_segment_sequence,
        allow_missing_sequence_fallback=not is_first_person_assignee(assignee_name),
    )
    resolution = resolve_assignee(
        assignee_name,
        evidence_segment,
        participants,
        profiles,
    )
    return evidence_segment, resolution


async def _enrich_action_item_assignee(
    action_item: dict[str, Any],
    task: MeetingAITask,
    transcript_segments: list[dict[str, Any]],
    participants: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
) -> dict[str, Any]:
    if action_item.get("assignee_email"):
        return action_item

    assignee_name = task.assignee_name or action_item.get("assignee_display_name")
    if not assignee_name:
        return action_item

    _, resolution = _resolve_task_assignee(
        task,
        transcript_segments,
        participants,
        profiles,
        assignee_name_override=assignee_name,
    )
    if not resolution.email:
        return action_item

    update_payload = {
        "assignee_user_id": resolution.user_id,
        "assignee_display_name": resolution.display_name or assignee_name,
        "assignee_email": resolution.email,
        "assignee_resolution_status": resolution.status,
        "assignee_resolution_confidence": resolution.confidence,
        "assignee_resolution_reason": resolution.reason,
    }
    rows = await supabase_gateway.patch(
        "action_items",
        update_payload,
        params={"id": f"eq.{action_item['id']}", "limit": "1"},
    )
    if rows:
        return rows[0]
    action_item.update(update_payload)
    return action_item


async def _store_tasks_for_calendar_user(
    meeting: dict[str, Any],
    action_items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    if not action_items:
        return [], 0

    existing_by_title = await _existing_by_title("tasks", meeting["id"])
    now = datetime.now(UTC).isoformat()
    task_payloads = []
    assignee_names_by_action_item_id = {}
    skipped_count = 0
    for action_item in action_items:
        existing_task = existing_by_title.get(_normalize_title(action_item["title"]))
        if existing_task:
            await _enrich_existing_task_assignment(existing_task, action_item, meeting)
            skipped_count += 1
            continue
        action_item_id = action_item.get("id")
        if action_item_id:
            assignee_names_by_action_item_id[action_item_id] = action_item.get(
                "assignee_display_name"
            )
        task_payloads.append(
            {
                "owner_user_id": meeting["user_id"],
                "assignee_user_id": action_item.get("assignee_user_id"),
                "assignee_email": action_item.get("assignee_email"),
                "assignment_source": action_item.get("assignee_resolution_reason"),
                "notification_status": "not_sent",
                "meeting_id": meeting["id"],
                "action_item_id": action_item_id,
                "title": action_item["title"],
                "description": action_item.get("description"),
                "status": "todo",
                "priority": _normalize_priority(action_item.get("priority")),
                "due_date": action_item.get("due_date"),
                "created_at": now,
                "updated_at": now,
            }
        )
    tasks = await supabase_gateway.insert("tasks", task_payloads) if task_payloads else []
    if tasks:
        task_assignees = [
            {
                "task_id": task["id"],
                "user_id": task["assignee_user_id"],
                "role": "primary",
                "created_at": now,
            }
            for task in tasks
            if task.get("assignee_user_id")
        ]
        if task_assignees:
            await supabase_gateway.insert("task_assignees", task_assignees)
        for task in tasks:
            await _send_task_email_if_needed(
                task,
                meeting,
                assignee_names_by_action_item_id.get(task.get("action_item_id")),
            )
    return tasks, skipped_count


async def _enrich_existing_task_assignment(
    task: dict[str, Any],
    action_item: dict[str, Any],
    meeting: dict[str, Any],
) -> None:
    update_payload = {}
    if not task.get("assignee_user_id") and action_item.get("assignee_user_id"):
        update_payload["assignee_user_id"] = action_item.get("assignee_user_id")
    if not task.get("assignee_email") and action_item.get("assignee_email"):
        update_payload["assignee_email"] = action_item.get("assignee_email")
    if not task.get("assignment_source") and action_item.get("assignee_resolution_reason"):
        update_payload["assignment_source"] = action_item.get("assignee_resolution_reason")

    if update_payload:
        rows = await supabase_gateway.patch(
            "tasks",
            update_payload,
            params={"id": f"eq.{task['id']}", "limit": "1"},
        )
        task.update(rows[0] if rows else update_payload)

    await _send_task_email_if_needed(
        task,
        meeting,
        action_item.get("assignee_display_name"),
    )


async def _send_task_email_if_needed(
    task: dict[str, Any],
    meeting: dict[str, Any],
    assignee_name: str | None,
) -> None:
    if not task.get("assignee_email"):
        return
    if task.get("notification_status") == "sent":
        return

    email_result: TaskEmailResult = send_task_assignment_email(
        to_email=task.get("assignee_email"),
        assignee_name=assignee_name or task.get("assignee_email"),
        task=task,
        meeting=meeting,
    )
    update_payload = {
        "notification_status": "sent" if email_result.sent else email_result.reason,
        "notification_error": email_result.error,
    }
    if email_result.sent:
        update_payload["notification_sent_at"] = datetime.now(UTC).isoformat()
    await supabase_gateway.patch(
        "tasks",
        update_payload,
        params={"id": f"eq.{task['id']}", "limit": "1"},
    )
    task.update(update_payload)


async def _existing_by_title(path: str, meeting_id: str) -> dict[str, dict[str, Any]]:
    rows = await supabase_gateway.get(
        path,
        {
            "select": "*",
            "meeting_id": f"eq.{meeting_id}",
        },
    )
    return {_normalize_title(row.get("title")): row for row in rows if row.get("title")}


def _normalize_title(value: str | None) -> str:
    return " ".join((value or "").lower().split())


def _normalize_priority(value: Any) -> str:
    priority = str(value or "medium").lower()
    return priority if priority in VALID_PRIORITIES else "medium"


async def _get_meeting_participants(meeting_id: str) -> list[dict[str, Any]]:
    return await supabase_gateway.get(
        "meeting_participants",
        {"select": "*", "meeting_id": f"eq.{meeting_id}"},
    )


async def _get_profiles_for_participants(
    participants: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    emails = sorted(
        {
            (
                participant.get("email") or participant.get("user_principal_name") or ""
            ).strip().lower()
            for participant in participants
            if participant.get("email") or participant.get("user_principal_name")
        }
    )
    if not emails:
        return []
    return await supabase_gateway.get(
        "profiles",
        {"select": "id,display_name,email", "email": f"in.({','.join(emails)})"},
    )


def _find_evidence_segment(
    transcript_segments: list[dict[str, Any]],
    sequence: int | None,
    allow_missing_sequence_fallback: bool = True,
) -> dict[str, Any] | None:
    if sequence is None:
        if allow_missing_sequence_fallback:
            return transcript_segments[-1] if transcript_segments else None
        return None
    return next(
        (segment for segment in transcript_segments if segment.get("sequence") == sequence),
        None,
    )


def _parse_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
