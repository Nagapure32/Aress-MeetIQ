import asyncio

import pytest
from fastapi import HTTPException


class FakeSupabaseGateway:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict]] = {
            "meetings": [],
            "transcript_segments": [],
            "meeting_summaries": [],
            "action_items": [],
            "tasks": [],
            "task_assignees": [],
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

        return rows

    async def insert(self, path: str, payload: dict | list[dict]) -> list[dict]:
        payloads = payload if isinstance(payload, list) else [payload]
        rows = []
        for item in payloads:
            row = item.copy()
            row.setdefault("id", f"{path}-{len(self.tables[path]) + 1}")
            self.tables[path].append(row)
            rows.append(row.copy())
        return rows

    async def upsert(
        self,
        path: str,
        payload: dict,
        on_conflict: str | None = None,
    ) -> list[dict]:
        if on_conflict:
            existing = [
                row
                for row in self.tables[path]
                if row.get(on_conflict) == payload.get(on_conflict)
            ]
            if existing:
                existing[0].update(payload)
                return [existing[0].copy()]
        return await self.insert(path, payload)


def run(coro):
    return asyncio.run(coro)


def test_generate_meeting_intelligence_creates_tasks_for_calendar_user(monkeypatch):
    from app.services import ai_meetings

    fake = FakeSupabaseGateway()
    fake.tables["meetings"] = [
        {
            "id": "meeting-1",
            "user_id": "calendar-user-1",
            "subject": "Roadmap sync",
        }
    ]
    fake.tables["transcript_segments"] = [
        {
            "id": "segment-1",
            "speaker": "Asha",
            "text": "Ravi will send the pricing notes tomorrow.",
            "created_at": "2026-05-20T10:00:00Z",
        }
    ]
    ai_result = ai_meetings.MeetingAIResult(
        summary="The team agreed to send pricing notes.",
        key_points=["Pricing follow-up is needed."],
        decisions=["Send pricing notes to the client."],
        tasks=[
            ai_meetings.MeetingAITask(
                title="Send pricing notes",
                description="Send the pricing notes discussed in Roadmap sync.",
                priority="high",
                due_date=None,
            )
        ],
    )
    monkeypatch.setattr(ai_meetings, "supabase_gateway", fake)
    monkeypatch.setattr(ai_meetings, "_run_agno_meeting_agent", lambda *_: ai_result)

    result = run(ai_meetings.generate_meeting_intelligence("meeting-1"))

    assert result["created_tasks_count"] == 1
    assert fake.tables["meeting_summaries"][0]["summary"] == ai_result.summary
    assert fake.tables["action_items"][0]["assignee_user_id"] == "calendar-user-1"
    assert fake.tables["tasks"][0]["owner_user_id"] == "calendar-user-1"
    assert fake.tables["tasks"][0]["assignee_user_id"] == "calendar-user-1"
    assert fake.tables["tasks"][0]["meeting_id"] == "meeting-1"
    assert fake.tables["task_assignees"][0]["user_id"] == "calendar-user-1"


def test_generate_meeting_intelligence_reports_duplicate_tasks(monkeypatch):
    from app.services import ai_meetings

    fake = FakeSupabaseGateway()
    fake.tables["meetings"] = [
        {
            "id": "meeting-1",
            "user_id": "calendar-user-1",
            "subject": "Roadmap sync",
        }
    ]
    fake.tables["transcript_segments"] = [
        {
            "id": "segment-1",
            "speaker": "Asha",
            "text": "Ravi will send the pricing notes tomorrow.",
            "created_at": "2026-05-20T10:00:00Z",
        }
    ]
    fake.tables["action_items"] = [
        {
            "id": "action_items-1",
            "meeting_id": "meeting-1",
            "assignee_user_id": "calendar-user-1",
            "title": "Send pricing notes",
            "description": "Send the pricing notes discussed in Roadmap sync.",
            "priority": "high",
            "due_date": None,
        }
    ]
    fake.tables["tasks"] = [
        {
            "id": "tasks-1",
            "owner_user_id": "calendar-user-1",
            "assignee_user_id": "calendar-user-1",
            "meeting_id": "meeting-1",
            "action_item_id": "action_items-1",
            "title": "Send pricing notes",
            "description": "Send the pricing notes discussed in Roadmap sync.",
            "status": "todo",
            "priority": "high",
            "due_date": None,
        }
    ]
    ai_result = ai_meetings.MeetingAIResult(
        summary="The team agreed to send pricing notes.",
        key_points=["Pricing follow-up is needed."],
        decisions=["Send pricing notes to the client."],
        tasks=[
            ai_meetings.MeetingAITask(
                title="Send pricing notes",
                description="Send the pricing notes discussed in Roadmap sync.",
                priority="high",
                due_date=None,
            )
        ],
    )
    monkeypatch.setattr(ai_meetings, "supabase_gateway", fake)
    monkeypatch.setattr(ai_meetings, "_run_agno_meeting_agent", lambda *_: ai_result)

    result = run(ai_meetings.generate_meeting_intelligence("meeting-1"))

    assert result["created_action_items_count"] == 0
    assert result["skipped_action_items_count"] == 1
    assert result["created_tasks_count"] == 0
    assert result["skipped_tasks_count"] == 1
    assert len(fake.tables["action_items"]) == 1
    assert len(fake.tables["tasks"]) == 1


def test_parse_ai_result_rejects_non_json_response():
    from app.services import ai_meetings

    with pytest.raises(HTTPException) as exc:
        ai_meetings._parse_ai_result("None")

    assert exc.value.status_code == 502
    assert "valid JSON" in exc.value.detail
