from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings

ENCRYPTED_TEXT_PLACEHOLDER = "[encrypted transcript]"
TRANSCRIPT_ENCRYPTION_ALGORITHM = "fernet-v1"


def protect_transcript_text(text: str) -> dict[str, str]:
    if not settings.enable_transcript_encryption:
        return {"text": text}

    fernet = _fernet_for_current_key()
    token = fernet.encrypt(text.encode("utf-8")).decode("utf-8")
    return {
        "text": ENCRYPTED_TEXT_PLACEHOLDER,
        "encrypted_text": token,
        "encryption_alg": TRANSCRIPT_ENCRYPTION_ALGORITHM,
        "encryption_key_id": settings.transcript_encryption_key_id,
    }


def decrypt_transcript_segment(segment: dict[str, Any]) -> dict[str, Any]:
    encrypted_text = segment.get("encrypted_text")
    if not encrypted_text:
        return segment

    decrypted = _fernet_for_current_key().decrypt(encrypted_text.encode("utf-8"))
    return {**segment, "text": decrypted.decode("utf-8")}


def decrypt_transcript_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [decrypt_transcript_segment(segment) for segment in segments]


def _fernet_for_current_key():
    if not settings.transcript_encryption_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TRANSCRIPT_ENCRYPTION_KEY is required when transcript encryption is enabled.",
        )

    try:
        from cryptography.fernet import Fernet, InvalidToken
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="cryptography package is required for transcript encryption.",
        ) from exc

    try:
        fernet = Fernet(settings.transcript_encryption_key.encode("utf-8"))
        fernet.decrypt
        return fernet
    except (ValueError, InvalidToken) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TRANSCRIPT_ENCRYPTION_KEY must be a valid Fernet key.",
        ) from exc