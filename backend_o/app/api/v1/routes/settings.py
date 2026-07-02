from fastapi import APIRouter

from app.api.v1.schemas import MeetingAssistantSettings, TranscriptionSettings
from app.services.meeting_settings import (
    get_meeting_assistant_settings as load_meeting_assistant_settings,
)
from app.services.meeting_settings import (
    update_meeting_assistant_settings as save_meeting_assistant_settings,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/meeting-assistant", response_model=MeetingAssistantSettings)
async def get_meeting_assistant_settings() -> MeetingAssistantSettings:
    return await load_meeting_assistant_settings()


@router.put("/meeting-assistant", response_model=MeetingAssistantSettings)
async def update_meeting_assistant_settings(
    payload: MeetingAssistantSettings,
) -> MeetingAssistantSettings:
    return await save_meeting_assistant_settings(payload)


@router.get("/transcription", response_model=TranscriptionSettings)
async def get_transcription_settings() -> TranscriptionSettings:
    # TODO: Load user/org transcription settings from Supabase.
    return TranscriptionSettings()


@router.put("/transcription", response_model=TranscriptionSettings)
async def update_transcription_settings(payload: TranscriptionSettings) -> TranscriptionSettings:
    # TODO: Persist user/org transcription settings to Supabase.
    return payload
