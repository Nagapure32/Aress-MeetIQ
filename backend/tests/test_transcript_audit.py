import asyncio


class FakeSupabaseGateway:
    def __init__(self) -> None:
        self.insert_calls = []

    async def insert(self, path, payload):
        self.insert_calls.append((path, payload))
        return [payload]


def run(coro):
    return asyncio.run(coro)


def test_record_transcript_access_writes_audit_row(monkeypatch):
    from app.services import audit

    fake = FakeSupabaseGateway()
    monkeypatch.setattr(audit, "supabase_gateway", fake)

    run(
        audit.record_transcript_access(
            meeting_id="meeting-1",
            user_id="user-1",
            role="meeting_participant",
            action="transcript_read",
            access_result="allowed",
        )
    )

    path, payload = fake.insert_calls[0]
    assert path == "transcript_access_audit"
    assert payload["meeting_id"] == "meeting-1"
    assert payload["user_id"] == "user-1"
    assert payload["role"] == "meeting_participant"
    assert payload["action"] == "transcript_read"
    assert payload["access_result"] == "allowed"
    assert payload["created_at"]