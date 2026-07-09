from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TranscriptResolution:
    requested_meeting_id: str
    transcript_meeting_id: str
    transcript_segment_count: int
    meeting_instance_id: str | None = None
    sibling_meeting_ids: tuple[str, ...] = ()
    user_intent: dict[str, Any] | None = None
    user_intent_allowed: bool = False


def is_allowed_transcript_intent_status(value: Any) -> bool:
    normalized = "".join(
        char for char in str(value or "").strip().lower() if char.isalnum()
    )
    return normalized in {"approved", "notrequired", "notrequested"}


async def resolve_transcript_source(
    gateway: Any,
    meeting_id: str,
    *,
    user_id: str | None = None,
) -> TranscriptResolution:
    direct_counts = await count_transcript_segments(gateway, [meeting_id])
    direct_count = direct_counts.get(meeting_id, 0)
    intents = await _safe_get(
        gateway,
        "meeting_user_intents",
        {
            "select": (
                "id,meeting_instance_id,user_id,meeting_id,approval_status,"
                "calendar_email"
            ),
            "meeting_id": f"eq.{meeting_id}",
            "limit": "1",
        },
    )
    if not intents:
        return TranscriptResolution(
            requested_meeting_id=meeting_id,
            transcript_meeting_id=meeting_id,
            transcript_segment_count=direct_count,
        )

    instance_id = str(intents[0].get("meeting_instance_id") or "")
    if not instance_id:
        return TranscriptResolution(
            requested_meeting_id=meeting_id,
            transcript_meeting_id=meeting_id,
            transcript_segment_count=direct_count,
        )

    instance_intents = await get_instance_intents(gateway, instance_id)
    sibling_ids = tuple(
        dict.fromkeys(
            str(intent.get("meeting_id"))
            for intent in instance_intents
            if intent.get("meeting_id")
        )
    )
    candidate_ids = sibling_ids or (meeting_id,)
    shared_counts = await count_transcript_segments(gateway, candidate_ids)
    source_id = meeting_id
    source_count = direct_count
    for candidate_id in candidate_ids:
        candidate_count = shared_counts.get(candidate_id, 0)
        if candidate_count > source_count:
            source_id = candidate_id
            source_count = candidate_count

    user_intent = None
    if user_id:
        user_intent = next(
            (
                intent
                for intent in instance_intents
                if str(intent.get("user_id") or "") == user_id
            ),
            None,
        )

    return TranscriptResolution(
        requested_meeting_id=meeting_id,
        transcript_meeting_id=source_id,
        transcript_segment_count=source_count,
        meeting_instance_id=instance_id,
        sibling_meeting_ids=candidate_ids,
        user_intent=user_intent,
        user_intent_allowed=(
            is_allowed_transcript_intent_status(user_intent.get("approval_status"))
            if user_intent
            else False
        ),
    )


async def get_instance_intents(gateway: Any, meeting_instance_id: str) -> list[dict[str, Any]]:
    return await _safe_get(
        gateway,
        "meeting_user_intents",
        {
            "select": (
                "id,meeting_instance_id,user_id,meeting_id,approval_status,"
                "calendar_email"
            ),
            "meeting_instance_id": f"eq.{meeting_instance_id}",
            "limit": "1000",
        },
    )


async def count_transcript_segments(
    gateway: Any,
    meeting_ids: list[str] | tuple[str, ...],
) -> dict[str, int]:
    ids = [meeting_id for meeting_id in dict.fromkeys(meeting_ids) if meeting_id]
    if not ids:
        return {}

    rows = await _safe_get(
        gateway,
        "transcript_segments",
        {
            "select": "meeting_id",
            "meeting_id": f"in.({','.join(ids)})",
        },
    )
    counts: dict[str, int] = {}
    for row in rows:
        row_meeting_id = str(row.get("meeting_id") or "")
        if row_meeting_id:
            counts[row_meeting_id] = counts.get(row_meeting_id, 0) + 1
    return counts


async def _safe_get(gateway: Any, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return await gateway.get(path, params=params)
    except Exception:
        return []
