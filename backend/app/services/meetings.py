from typing import Any

from app.auth.authorization import require_transcript_access
from app.auth.current_user import CurrentUser

from app.db.supabase import supabase_gateway
from app.services.meeting_content_security import (
    decrypt_meeting_summary_content,
    decrypt_task_contents,
)
from app.services.meeting_settings import get_dev_user_id
from app.services.shared_transcripts import (
    count_transcript_segments,
    is_allowed_transcript_intent_status,
    resolve_transcript_source,
)
from app.services.transcript_security import decrypt_transcript_segments


async def list_user_meetings(
    transcript_ready: bool = False,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    user_id = user_id or get_dev_user_id()
    meetings = await _safe_get(
        "meetings",
        {
            "select": (
                "id,graph_event_id,subject,organizer_email,join_url,start_time,end_time,"
                "status,bot_status,approval_status,source_type,processing_status,"
                "uploaded_media_url,created_at,updated_at"
            ),
            "user_id": f"eq.{user_id}",
            "order": "start_time.desc",
            "limit": "100",
        },
    )
    meetings_with_counts = await _with_transcript_counts(meetings)
    if transcript_ready:
        return [
            meeting
            for meeting in meetings_with_counts
            if meeting.get("transcript_segment_count", 0) > 0
        ]
    return meetings_with_counts


async def get_user_meeting(meeting_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    user_id = user_id or get_dev_user_id()
    rows = await _safe_get(
        "meetings",
        {
            "select": (
                "id,graph_event_id,subject,organizer_email,join_url,start_time,end_time,"
                "status,bot_status,approval_status,source_type,processing_status,"
                "uploaded_media_url,created_at,updated_at"
            ),
            "id": f"eq.{meeting_id}",
            "user_id": f"eq.{user_id}",
            "limit": "1",
        },
    )
    return rows[0] if rows else None


async def list_meeting_transcript(
    meeting_id: str,
    user_id: str | None = None,
    current_user: CurrentUser | None = None,
) -> list[dict[str, Any]]:
    if current_user is not None:
        transcript_meeting_id = await require_transcript_access(current_user, meeting_id)
    elif not await get_user_meeting(meeting_id, user_id):
        return []
    else:
        resolution = await resolve_transcript_source(
            supabase_gateway,
            meeting_id,
            user_id=user_id or get_dev_user_id(),
        )
        transcript_meeting_id = resolution.transcript_meeting_id
    rows = await _safe_get(
        "transcript_segments",
        {
            "select": (
                "id,sequence,speaker,source_id,language,text,encrypted_text,encryption_alg,"
                "encryption_key_id,started_at,ended_at,created_at"
            ),
            "meeting_id": f"eq.{transcript_meeting_id}",
            "order": "sequence.asc.nullslast,started_at.asc.nullslast,created_at.asc",
            "limit": "1000",
        },
    )
    return decrypt_transcript_segments(rows)


async def get_meeting_summary(
    meeting_id: str,
    user_id: str | None = None,
    current_user: CurrentUser | None = None,
) -> dict[str, Any] | None:
    if current_user is not None:
        transcript_meeting_id = await require_transcript_access(current_user, meeting_id)
    elif not await get_user_meeting(meeting_id, user_id):
        return None
    else:
        resolution = await resolve_transcript_source(
            supabase_gateway,
            meeting_id,
            user_id=user_id or get_dev_user_id(),
        )
        transcript_meeting_id = resolution.transcript_meeting_id
    rows = await _safe_get(
        "meeting_summaries",
        {
            "select": (
                "id,summary,key_points,decisions,encrypted_summary,encrypted_key_points,"
                "encrypted_decisions,encryption_alg,encryption_key_id,model,created_at,updated_at"
            ),
            "meeting_id": f"eq.{meeting_id}",
            "limit": "1",
        },
    )
    if rows:
        return decrypt_meeting_summary_content(rows[0])
    if transcript_meeting_id == meeting_id:
        return None

    rows = await _safe_get(
        "meeting_summaries",
        {
            "select": (
                "id,summary,key_points,decisions,encrypted_summary,encrypted_key_points,"
                "encrypted_decisions,encryption_alg,encryption_key_id,model,created_at,updated_at"
            ),
            "meeting_id": f"eq.{transcript_meeting_id}",
            "limit": "1",
        },
    )
    return decrypt_meeting_summary_content(rows[0]) if rows else None


async def list_meeting_tasks(
    meeting_id: str,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    user_id = user_id or get_dev_user_id()
    rows = await _safe_get(
        "tasks",
        {
            "select": (
                "id,title,description,encrypted_title,encrypted_description,encryption_alg,"
                "encryption_key_id,title_lookup_hash,title_lookup_hash_alg,status,priority,"
                "due_date,meeting_id,action_item_id,created_at,updated_at"
            ),
            "meeting_id": f"eq.{meeting_id}",
            "owner_user_id": f"eq.{user_id}",
            "order": "created_at.desc",
        },
    )
    return decrypt_task_contents(rows)


async def _safe_get(path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return await supabase_gateway.get(path, params=params)
    except Exception:
        return []


async def _with_transcript_counts(meetings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not meetings:
        return []

    meeting_ids = [str(meeting["id"]) for meeting in meetings if meeting.get("id")]
    if not meeting_ids:
        return [{**meeting, "transcript_segment_count": 0} for meeting in meetings]

    direct_counts = await count_transcript_segments(supabase_gateway, meeting_ids)
    user_intents = await _safe_get(
        "meeting_user_intents",
        {
            "select": "meeting_instance_id,meeting_id,approval_status",
            "meeting_id": f"in.({','.join(meeting_ids)})",
            "limit": "1000",
        },
    )
    intents_by_meeting_id = {
        str(intent.get("meeting_id")): intent
        for intent in user_intents
        if intent.get("meeting_id")
    }
    instance_ids = sorted(
        {
            str(intent.get("meeting_instance_id"))
            for intent in user_intents
            if intent.get("meeting_instance_id")
        }
    )
    instance_counts: dict[str, int] = {}
    if instance_ids:
        sibling_intents = await _safe_get(
            "meeting_user_intents",
            {
                "select": "meeting_instance_id,meeting_id",
                "meeting_instance_id": f"in.({','.join(instance_ids)})",
                "limit": "1000",
            },
        )
        sibling_ids = [
            str(intent.get("meeting_id"))
            for intent in sibling_intents
            if intent.get("meeting_id")
        ]
        sibling_counts = await count_transcript_segments(supabase_gateway, sibling_ids)
        for intent in sibling_intents:
            instance_id = str(intent.get("meeting_instance_id") or "")
            sibling_meeting_id = str(intent.get("meeting_id") or "")
            if not instance_id or not sibling_meeting_id:
                continue
            instance_counts[instance_id] = max(
                instance_counts.get(instance_id, 0),
                sibling_counts.get(sibling_meeting_id, 0),
            )

    return [
        {
            **meeting,
            "transcript_segment_count": _meeting_transcript_count(
                str(meeting.get("id") or ""),
                direct_counts,
                intents_by_meeting_id,
                instance_counts,
            ),
        }
        for meeting in meetings
    ]


def _meeting_transcript_count(
    meeting_id: str,
    direct_counts: dict[str, int],
    intents_by_meeting_id: dict[str, dict[str, Any]],
    instance_counts: dict[str, int],
) -> int:
    direct_count = direct_counts.get(meeting_id, 0)
    intent = intents_by_meeting_id.get(meeting_id)
    if not intent or not is_allowed_transcript_intent_status(intent.get("approval_status")):
        return direct_count
    instance_id = str(intent.get("meeting_instance_id") or "")
    return max(direct_count, instance_counts.get(instance_id, 0))
