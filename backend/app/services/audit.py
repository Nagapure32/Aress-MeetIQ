from datetime import UTC, datetime

from app.db.supabase import supabase_gateway


async def record_transcript_access(
    *,
    meeting_id: str,
    user_id: str | None,
    role: str | None,
    action: str,
    access_result: str,
    reason: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    payload = {
        "meeting_id": meeting_id,
        "user_id": user_id,
        "role": role,
        "action": action,
        "access_result": access_result,
        "reason": reason,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "created_at": datetime.now(UTC).isoformat(),
    }
    try:
        await supabase_gateway.insert("transcript_access_audit", payload)
    except Exception:
        return