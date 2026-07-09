from fastapi import HTTPException, status

from app.auth.current_user import CurrentUser
from app.auth.roles import TRANSCRIPT_READ_ALL_ROLES
from app.db.supabase import supabase_gateway
from app.services.audit import record_transcript_access
from app.services.shared_transcripts import resolve_transcript_source


def _normalize(value: str | None) -> str | None:
    cleaned = (value or "").strip().lower()
    return cleaned or None


async def require_transcript_access(current_user: CurrentUser, meeting_id: str) -> str:
    resolution = await resolve_transcript_source(
        supabase_gateway,
        meeting_id,
        user_id=current_user.user_id,
    )
    if TRANSCRIPT_READ_ALL_ROLES.intersection(current_user.roles):
        return resolution.transcript_meeting_id

    if resolution.meeting_instance_id and resolution.user_intent_allowed:
        await record_transcript_access(
            meeting_id=resolution.transcript_meeting_id,
            user_id=current_user.user_id,
            role=",".join(current_user.roles) or None,
            action="read_transcript",
            access_result="allowed",
            reason="shared_intent",
        )
        return resolution.transcript_meeting_id

    if not resolution.meeting_instance_id and await _user_owns_meeting(
        current_user.user_id,
        meeting_id,
    ):
        await record_transcript_access(
            meeting_id=meeting_id,
            user_id=current_user.user_id,
            role=",".join(current_user.roles) or None,
            action="read_transcript",
            access_result="allowed",
            reason="owner",
        )
        return resolution.transcript_meeting_id

    candidate_ids = [
        value
        for value in dict.fromkeys([meeting_id, resolution.transcript_meeting_id])
        if value
    ]
    for candidate_id in candidate_ids:
        participants = await supabase_gateway.get(
            "meeting_participants",
            {
                "select": "meeting_id,user_id,aad_user_id,email,user_principal_name",
                "meeting_id": f"eq.{candidate_id}",
                "limit": "1000",
            },
        )
        if any(_participant_matches_user(participant, current_user) for participant in participants):
            await record_transcript_access(
                meeting_id=resolution.transcript_meeting_id,
                user_id=current_user.user_id,
                role=",".join(current_user.roles) or None,
                action="read_transcript",
                access_result="allowed",
                reason="participant",
            )
            return resolution.transcript_meeting_id

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this transcript.",
    )


def _participant_matches_user(participant: dict, current_user: CurrentUser) -> bool:
    if participant.get("user_id") and str(participant["user_id"]) == current_user.user_id:
        return True
    if current_user.aad_user_id and participant.get("aad_user_id") == current_user.aad_user_id:
        return True

    user_email = _normalize(current_user.email)
    if not user_email:
        return False
    return user_email in {
        _normalize(participant.get("email")),
        _normalize(participant.get("user_principal_name")),
    }


async def _user_owns_meeting(user_id: str, meeting_id: str) -> bool:
    rows = await supabase_gateway.get(
        "meetings",
        {
            "select": "id",
            "id": f"eq.{meeting_id}",
            "user_id": f"eq.{user_id}",
            "limit": "1",
        },
    )
    return bool(rows)
