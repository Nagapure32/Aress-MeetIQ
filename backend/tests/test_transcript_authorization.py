import asyncio

import pytest
from fastapi import HTTPException

from app.auth.current_user import CurrentUser


class FakeSupabaseGateway:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict]] = {
            "meetings": [],
            "meeting_user_intents": [],
            "meeting_participants": [],
            "transcript_segments": [],
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
            if isinstance(value, str) and value.startswith("in.("):
                expected_values = value[4:-1].split(",")
                rows = [row for row in rows if str(row.get(key)) in expected_values]

        if params.get("limit"):
            rows = rows[: int(params["limit"])]
        return rows


def run(coro):
    return asyncio.run(coro)


def user(user_id: str) -> CurrentUser:
    return CurrentUser(user_id=user_id, email=f"{user_id}@example.com", auth_source="supabase")


async def noop_record_transcript_access(**_kwargs):
    return None


def test_approved_shared_intent_can_access_canonical_transcript(monkeypatch):
    from app.auth import authorization

    fake = FakeSupabaseGateway()
    fake.tables["meeting_user_intents"] = [
        {
            "meeting_instance_id": "instance-1",
            "meeting_id": "approved-sibling",
            "user_id": "user-1",
            "approval_status": "Approved",
        },
        {
            "meeting_instance_id": "instance-1",
            "meeting_id": "transcript-owner",
            "user_id": "user-2",
            "approval_status": "Approved",
        },
    ]
    fake.tables["transcript_segments"] = [
        {"id": "segment-1", "meeting_id": "transcript-owner"},
    ]
    monkeypatch.setattr(authorization, "supabase_gateway", fake)
    monkeypatch.setattr(
        authorization,
        "record_transcript_access",
        noop_record_transcript_access,
    )

    result = run(authorization.require_transcript_access(user("user-1"), "approved-sibling"))

    assert result == "transcript-owner"


def test_expired_shared_intent_cannot_access_sibling_transcript(monkeypatch):
    from app.auth import authorization

    fake = FakeSupabaseGateway()
    fake.tables["meeting_user_intents"] = [
        {
            "meeting_instance_id": "instance-1",
            "meeting_id": "expired-sibling",
            "user_id": "user-1",
            "approval_status": "Expired",
        },
        {
            "meeting_instance_id": "instance-1",
            "meeting_id": "transcript-owner",
            "user_id": "user-2",
            "approval_status": "Approved",
        },
    ]
    fake.tables["transcript_segments"] = [
        {"id": "segment-1", "meeting_id": "transcript-owner"},
    ]
    monkeypatch.setattr(authorization, "supabase_gateway", fake)
    monkeypatch.setattr(
        authorization,
        "record_transcript_access",
        noop_record_transcript_access,
    )

    with pytest.raises(HTTPException) as exc:
        run(authorization.require_transcript_access(user("user-1"), "expired-sibling"))

    assert exc.value.status_code == 403


def test_direct_meeting_owner_can_access_own_transcript(monkeypatch):
    from app.auth import authorization

    fake = FakeSupabaseGateway()
    fake.tables["meetings"] = [{"id": "meeting-1", "user_id": "user-1"}]
    fake.tables["transcript_segments"] = [
        {"id": "segment-1", "meeting_id": "meeting-1"},
    ]
    monkeypatch.setattr(authorization, "supabase_gateway", fake)
    monkeypatch.setattr(
        authorization,
        "record_transcript_access",
        noop_record_transcript_access,
    )

    result = run(authorization.require_transcript_access(user("user-1"), "meeting-1"))

    assert result == "meeting-1"
