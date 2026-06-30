import asyncio

import pytest
from fastapi import HTTPException

from app.auth.current_user import CurrentUser
from app.auth.roles import ORG_ADMIN, SUPER_ADMIN


class FakeSupabaseGateway:
    def __init__(self) -> None:
        self.tables = {"meeting_participants": []}
        self.get_calls = []

    async def get(self, path: str, params: dict | None = None) -> list[dict]:
        self.get_calls.append((path, params))
        rows = [row.copy() for row in self.tables[path]]
        if not params:
            return rows
        for key, value in params.items():
            if key in {"select", "order", "limit"}:
                continue
            if isinstance(value, str) and value.startswith("eq."):
                expected = value[3:]
                rows = [row for row in rows if str(row.get(key)) == expected]
        return rows[: int(params.get("limit", len(rows)))]


def run(coro):
    return asyncio.run(coro)


def test_participant_user_id_can_read_transcript(monkeypatch):
    from app.auth import authorization

    fake = FakeSupabaseGateway()
    fake.tables["meeting_participants"] = [
        {"meeting_id": "meeting-1", "user_id": "user-1"}
    ]
    monkeypatch.setattr(authorization, "supabase_gateway", fake)

    run(
        authorization.require_transcript_access(
            CurrentUser(user_id="user-1", auth_source="supabase"),
            "meeting-1",
        )
    )


@pytest.mark.parametrize(
    "participant,user",
    [
        ({"meeting_id": "meeting-1", "email": "asha@example.com"}, CurrentUser(user_id="u-1", email="asha@example.com", auth_source="supabase")),
        ({"meeting_id": "meeting-1", "user_principal_name": "asha@example.com"}, CurrentUser(user_id="u-1", email="asha@example.com", auth_source="supabase")),
        ({"meeting_id": "meeting-1", "aad_user_id": "aad-1"}, CurrentUser(user_id="u-1", aad_user_id="aad-1", auth_source="supabase")),
    ],
)
def test_participant_identity_fields_can_read_transcript(monkeypatch, participant, user):
    from app.auth import authorization

    fake = FakeSupabaseGateway()
    fake.tables["meeting_participants"] = [participant]
    monkeypatch.setattr(authorization, "supabase_gateway", fake)

    run(authorization.require_transcript_access(user, "meeting-1"))


def test_non_participant_is_denied_transcript(monkeypatch):
    from app.auth import authorization

    fake = FakeSupabaseGateway()
    fake.tables["meeting_participants"] = [
        {"meeting_id": "meeting-1", "user_id": "user-1"}
    ]
    monkeypatch.setattr(authorization, "supabase_gateway", fake)

    with pytest.raises(HTTPException) as exc:
        run(
            authorization.require_transcript_access(
                CurrentUser(user_id="user-2", auth_source="supabase"),
                "meeting-1",
            )
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "You do not have access to this transcript."


def test_org_admin_is_denied_when_not_participant(monkeypatch):
    from app.auth import authorization

    fake = FakeSupabaseGateway()
    fake.tables["meeting_participants"] = []
    monkeypatch.setattr(authorization, "supabase_gateway", fake)

    with pytest.raises(HTTPException) as exc:
        run(
            authorization.require_transcript_access(
                CurrentUser(user_id="admin-1", roles=[ORG_ADMIN], auth_source="supabase"),
                "meeting-1",
            )
        )

    assert exc.value.status_code == 403


def test_super_admin_can_read_any_transcript(monkeypatch):
    from app.auth import authorization

    fake = FakeSupabaseGateway()
    monkeypatch.setattr(authorization, "supabase_gateway", fake)

    run(
        authorization.require_transcript_access(
            CurrentUser(user_id="super-1", roles=[SUPER_ADMIN], auth_source="supabase"),
            "meeting-1",
        )
    )

    assert fake.get_calls == []