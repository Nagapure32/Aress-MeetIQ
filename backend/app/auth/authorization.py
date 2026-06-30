from fastapi import HTTPException, status

from app.auth.current_user import CurrentUser
from app.auth.roles import TRANSCRIPT_READ_ALL_ROLES
from app.db.supabase import supabase_gateway
from app.services.audit import record_transcript_access


def _normalize(value: str | None) -> str | None:
    cleaned = (value or "").strip().lower()
    return cleaned or None


async def require_transcript_access(current_user: CurrentUser, meeting_id: str) -> None:
    if TRANSCRIPT_READ_ALL_ROLES.intersection(current_user.roles):
        return

    participants = await supabase_gateway.get(
        "meeting_participants",
        {
            "select": "meeting_id,user_id,aad_user_id,email,user_principal_name",
            "meeting_id": f"eq.{meeting_id}",
            "limit": "1000",
        },
    )
    if any(_participant_matches_user(participant, current_user) for participant in participants):
        return

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