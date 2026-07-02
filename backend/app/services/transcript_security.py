from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.sensitive_fields import (
    SENSITIVE_FIELD_ENCRYPTION_ALGORITHM,
    decrypt_text_value,
    encrypt_text_value,
    sensitive_field_encryption_enabled,
)

ENCRYPTED_TEXT_PLACEHOLDER = "[encrypted transcript]"
TRANSCRIPT_ENCRYPTION_ALGORITHM = SENSITIVE_FIELD_ENCRYPTION_ALGORITHM


def protect_transcript_text(text: str) -> dict[str, str]:
    if not sensitive_field_encryption_enabled():
        return {"text": text}

    return {
        "text": ENCRYPTED_TEXT_PLACEHOLDER,
        "encrypted_text": encrypt_text_value(text),
        "encryption_alg": TRANSCRIPT_ENCRYPTION_ALGORITHM,
        "encryption_key_id": settings.transcript_encryption_key_id,
    }


def decrypt_transcript_segment(segment: dict[str, Any]) -> dict[str, Any]:
    encrypted_text = segment.get("encrypted_text")
    if not encrypted_text:
        return segment

    return {**segment, "text": decrypt_text_value(str(encrypted_text))}


def decrypt_transcript_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [decrypt_transcript_segment(segment) for segment in segments]
