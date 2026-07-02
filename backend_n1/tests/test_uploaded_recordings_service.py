import asyncio


class FakeUploadFile:
    def __init__(self, filename: str, content: bytes, content_type: str) -> None:
        self.filename = filename
        self.content = content
        self.content_type = content_type

    async def read(self) -> bytes:
        return self.content


class FakeSupabaseGateway:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict]] = {
            "meetings": [],
            "meeting_upload_jobs": [],
            "transcript_segments": [],
        }
        self.patches: list[tuple[str, dict, dict]] = []

    async def insert(self, path: str, payload: dict | list[dict]) -> list[dict]:
        payloads = payload if isinstance(payload, list) else [payload]
        rows = []
        for item in payloads:
            row = item.copy()
            row.setdefault("id", f"{path}-{len(self.tables[path]) + 1}")
            self.tables[path].append(row)
            rows.append(row.copy())
        return rows

    async def patch(self, path: str, payload: dict, params: dict) -> list[dict]:
        self.patches.append((path, payload.copy(), params.copy()))
        rows = self.tables[path]
        matched_rows = rows
        for key, value in params.items():
            if key == "limit":
                continue
            if isinstance(value, str) and value.startswith("eq."):
                expected = value[3:]
                matched_rows = [row for row in matched_rows if str(row.get(key)) == expected]
        for row in matched_rows:
            row.update(payload)
        return [row.copy() for row in matched_rows]


def run(coro):
    return asyncio.run(coro)


def test_create_uploaded_recording_creates_meeting_job_and_segments(monkeypatch, tmp_path):
    from app.services import uploaded_recordings

    fake = FakeSupabaseGateway()
    intelligence_calls = []
    index_calls = []

    async def fake_generate_meeting_intelligence(meeting_id, user_id=None):
        intelligence_calls.append((meeting_id, user_id))
        return {"meeting_id": meeting_id}

    async def fake_index_meeting_transcript(meeting_id, user_id=None):
        index_calls.append((meeting_id, user_id))
        return {"meeting_id": meeting_id, "status": "ready"}

    monkeypatch.setattr(uploaded_recordings, "supabase_gateway", fake)
    monkeypatch.setattr(
        uploaded_recordings,
        "generate_meeting_intelligence",
        fake_generate_meeting_intelligence,
    )
    monkeypatch.setattr(
        uploaded_recordings,
        "index_meeting_transcript",
        fake_index_meeting_transcript,
    )
    monkeypatch.setattr(uploaded_recordings.settings, "uploaded_recordings_dir", str(tmp_path))

    result = run(
        uploaded_recordings.create_uploaded_recording(
            user_id="user-1",
            title="Uploaded client sync",
            meeting_date="2026-05-29T10:00:00Z",
            file=FakeUploadFile("client-sync.mp3", b"audio-bytes", "audio/mpeg"),
            transcript_text="Ravi: Send proposal.\nPriya: Review pricing.",
        )
    )

    assert result["status"] == "ready"
    assert result["meeting"]["source_type"] == "uploaded_recording"
    assert result["job"]["status"] == "ready"
    assert fake.tables["meetings"][0]["graph_event_id"].startswith("upload:")
    assert fake.tables["meeting_upload_jobs"][0]["original_filename"] == "client-sync.mp3"
    assert [row["text"] for row in fake.tables["transcript_segments"]] == [
        "Send proposal.",
        "Review pricing.",
    ]
    assert intelligence_calls == [("meetings-1", "user-1")]
    assert index_calls == [("meetings-1", "user-1")]


def test_create_uploaded_recording_without_transcript_transcribes_media(
    monkeypatch,
    tmp_path,
):
    from app.services import uploaded_recordings

    fake = FakeSupabaseGateway()
    intelligence_calls = []
    index_calls = []
    transcribed_files = []

    async def fake_transcribe_uploaded_file(stored_file_path, original_filename, content_type):
        transcribed_files.append((stored_file_path, original_filename, content_type))
        return "Speaker 1: Review the launch plan.\nSpeaker 2: Send the client summary."

    async def fake_generate_meeting_intelligence(meeting_id, user_id=None):
        intelligence_calls.append((meeting_id, user_id))
        return {"meeting_id": meeting_id}

    async def fake_index_meeting_transcript(meeting_id, user_id=None):
        index_calls.append((meeting_id, user_id))
        return {"meeting_id": meeting_id, "status": "ready"}

    monkeypatch.setattr(uploaded_recordings, "supabase_gateway", fake)
    monkeypatch.setattr(uploaded_recordings.settings, "uploaded_recordings_dir", str(tmp_path))
    monkeypatch.setattr(
        uploaded_recordings,
        "_transcribe_uploaded_file",
        fake_transcribe_uploaded_file,
    )
    monkeypatch.setattr(
        uploaded_recordings,
        "generate_meeting_intelligence",
        fake_generate_meeting_intelligence,
    )
    monkeypatch.setattr(
        uploaded_recordings,
        "index_meeting_transcript",
        fake_index_meeting_transcript,
    )

    result = run(
        uploaded_recordings.create_uploaded_recording(
            user_id="user-1",
            title="Uploaded client sync",
            meeting_date="2026-05-29T10:00:00Z",
            file=FakeUploadFile("client-sync.mp4", b"video-bytes", "video/mp4"),
            transcript_text=None,
        )
    )

    assert result["status"] == "ready"
    assert result["job"]["status"] == "ready"
    assert [row["text"] for row in fake.tables["transcript_segments"]] == [
        "Review the launch plan.",
        "Send the client summary.",
    ]
    assert transcribed_files[0][1] == "client-sync.mp4"
    assert transcribed_files[0][2] == "video/mp4"
    assert intelligence_calls == [("meetings-1", "user-1")]
    assert index_calls == [("meetings-1", "user-1")]


def test_transcription_response_to_text_uses_phrase_speakers():
    from app.services import uploaded_recordings

    text = uploaded_recordings._transcription_response_to_text(
        {
            "phrases": [
                {"speaker": 1, "text": "Review the launch plan."},
                {"speaker": 2, "text": "Send the client summary."},
            ]
        }
    )

    assert text == (
        "Speaker 1: Review the launch plan.\n"
        "Speaker 2: Send the client summary."
    )


def test_transcription_response_to_text_uses_combined_phrase_fallback():
    from app.services import uploaded_recordings

    text = uploaded_recordings._transcription_response_to_text(
        {"combinedPhrases": [{"text": "Review the launch plan."}]}
    )

    assert text == "Review the launch plan."
