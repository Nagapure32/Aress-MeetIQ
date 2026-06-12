import asyncio


class FakeSupabaseGateway:
    def __init__(self) -> None:
        self.upserts: list[tuple[str, dict, str | None]] = []
        self.tables: dict[str, list[dict]] = {"meeting_settings": []}

    async def get(self, path: str, params: dict | None = None) -> list[dict]:
        rows = [row.copy() for row in self.tables[path]]
        if params and "user_id" in params:
            expected = params["user_id"].removeprefix("eq.")
            rows = [row for row in rows if row.get("user_id") == expected]
        return rows[: int(params.get("limit", len(rows)))] if params else rows

    async def upsert(
        self,
        path: str,
        payload: dict,
        on_conflict: str | None = None,
    ) -> list[dict]:
        self.upserts.append((path, payload.copy(), on_conflict))
        return [payload.copy()]


def run(coro):
    return asyncio.run(coro)


def test_ensure_user_workspace_upserts_profile_calendar_connection_and_settings(monkeypatch):
    from app.services import user_bootstrap

    fake = FakeSupabaseGateway()
    monkeypatch.setattr(user_bootstrap, "supabase_gateway", fake)

    result = run(
        user_bootstrap.ensure_user_workspace(
            user_id="auth-user-id",
            email="person@example.com",
            tenant_id="tenant-1",
            aad_user_id="aad-user-1",
        )
    )

    assert result == {
        "user_id": "auth-user-id",
        "calendar_connection_status": "connected",
    }
    assert fake.upserts == [
        (
            "profiles",
            {
                "id": "auth-user-id",
                "email": "person@example.com",
            },
            "id",
        ),
        (
            "meeting_settings",
            {
                "user_id": "auth-user-id",
                "auto_join_enabled": False,
                "require_approval": True,
                "approval_lead_minutes": 2,
                "look_ahead_minutes": 15,
                "join_early_seconds": 0,
                "max_late_join_minutes": 10,
                "leave_grace_minutes": 2,
                "use_service_hosted_media": False,
            },
            "user_id",
        ),
        (
            "calendar_connections",
            {
                "user_id": "auth-user-id",
                "provider": "microsoft",
                "tenant_id": "tenant-1",
                "aad_user_id": "aad-user-1",
                "email": "person@example.com",
                "enabled": True,
                "connection_status": "connected",
            },
            "user_id,provider",
        ),
    ]


def test_ensure_user_workspace_keeps_calendar_pending_without_email(monkeypatch):
    from app.services import user_bootstrap

    fake = FakeSupabaseGateway()
    monkeypatch.setattr(user_bootstrap, "supabase_gateway", fake)

    result = run(user_bootstrap.ensure_user_workspace(user_id="auth-user-id", email=None))

    assert result == {
        "user_id": "auth-user-id",
        "calendar_connection_status": "pending",
    }
    calendar_payload = fake.upserts[2][1]
    assert calendar_payload["email"] == "auth-user-id"
    assert calendar_payload["enabled"] is False
    assert calendar_payload["connection_status"] == "pending"


def test_ensure_user_workspace_preserves_existing_auto_join_setting(monkeypatch):
    from app.services import user_bootstrap

    fake = FakeSupabaseGateway()
    fake.tables["meeting_settings"] = [
        {
            "user_id": "auth-user-id",
            "auto_join_enabled": True,
            "require_approval": False,
            "look_ahead_minutes": 45,
        }
    ]
    monkeypatch.setattr(user_bootstrap, "supabase_gateway", fake)

    run(
        user_bootstrap.ensure_user_workspace(
            user_id="auth-user-id",
            email="person@example.com",
        )
    )

    meeting_settings_payload = fake.upserts[1][1]
    assert meeting_settings_payload["auto_join_enabled"] is True
    assert meeting_settings_payload["require_approval"] is False
    assert meeting_settings_payload["look_ahead_minutes"] == 45
    assert meeting_settings_payload["approval_lead_minutes"] == 2
