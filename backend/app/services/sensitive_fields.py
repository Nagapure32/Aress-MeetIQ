from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings

ENCRYPTED_VALUE_PLACEHOLDER = "[encrypted value]"
SENSITIVE_FIELD_ENCRYPTION_ALGORITHM = "fernet-v1"
SENSITIVE_LOOKUP_HASH_ALGORITHM = "hmac-sha256-v1"


def sensitive_field_encryption_enabled() -> bool:
    return settings.enable_transcript_encryption


def encrypt_text_value(value: str) -> str:
    return _fernet_for_current_key().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_text_value(token: str) -> str:
    decrypted = _fernet_for_current_key().decrypt(token.encode("utf-8"))
    return decrypted.decode("utf-8")


def protect_text_field(
    field_name: str,
    value: str | None,
    *,
    encrypted_field_name: str | None = None,
    placeholder: str = ENCRYPTED_VALUE_PLACEHOLDER,
) -> dict[str, Any]:
    encrypted_field_name = encrypted_field_name or f"encrypted_{field_name}"
    if value is None:
        return {field_name: None, encrypted_field_name: None}

    if not sensitive_field_encryption_enabled():
        return {field_name: value, encrypted_field_name: None}

    return {
        field_name: placeholder,
        encrypted_field_name: encrypt_text_value(value),
        "encryption_alg": SENSITIVE_FIELD_ENCRYPTION_ALGORITHM,
        "encryption_key_id": settings.transcript_encryption_key_id,
    }


def protect_json_field(
    field_name: str,
    value: Any,
    *,
    encrypted_field_name: str | None = None,
    plaintext_placeholder: Any,
) -> dict[str, Any]:
    encrypted_field_name = encrypted_field_name or f"encrypted_{field_name}"
    if not sensitive_field_encryption_enabled():
        return {field_name: value, encrypted_field_name: None}

    serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return {
        field_name: plaintext_placeholder,
        encrypted_field_name: encrypt_text_value(serialized),
        "encryption_alg": SENSITIVE_FIELD_ENCRYPTION_ALGORITHM,
        "encryption_key_id": settings.transcript_encryption_key_id,
    }


def decrypt_text_field(
    row: dict[str, Any],
    field_name: str,
    *,
    encrypted_field_name: str | None = None,
) -> dict[str, Any]:
    encrypted_field_name = encrypted_field_name or f"encrypted_{field_name}"
    encrypted_value = row.get(encrypted_field_name)
    if not encrypted_value:
        return row
    plaintext_value = row.get(field_name)
    if (
        isinstance(plaintext_value, str)
        and plaintext_value
        and not plaintext_value.startswith("[encrypted")
    ):
        return row

    return {**row, field_name: decrypt_text_value(str(encrypted_value))}


def decrypt_json_field(
    row: dict[str, Any],
    field_name: str,
    *,
    encrypted_field_name: str | None = None,
    default: Any,
) -> dict[str, Any]:
    encrypted_field_name = encrypted_field_name or f"encrypted_{field_name}"
    encrypted_value = row.get(encrypted_field_name)
    if not encrypted_value:
        return row
    plaintext_value = row.get(field_name)
    if plaintext_value not in (None, [], {}):
        return row

    decrypted = decrypt_text_value(str(encrypted_value))
    try:
        parsed = json.loads(decrypted)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encrypted field '{field_name}' did not contain valid JSON.",
        ) from exc
    return {**row, field_name: parsed if parsed is not None else default}


def strip_encrypted_fields(row: dict[str, Any], field_names: list[str]) -> dict[str, Any]:
    stripped = row.copy()
    for field_name in field_names:
        stripped.pop(f"encrypted_{field_name}", None)
    stripped.pop("encryption_alg", None)
    stripped.pop("encryption_key_id", None)
    return stripped


def normalize_lookup_text(value: Any) -> str:
    return " ".join(str(value or "").lower().split())


def lookup_hash_for_text(value: Any) -> str | None:
    normalized = normalize_lookup_text(value)
    if not normalized:
        return None

    secret = (
        settings.transcript_encryption_key
        or settings.backend_secret_key
        or settings.supabase_jwt_secret
    )
    if not secret:
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return digest

    return hmac.new(
        secret.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _fernet_for_current_key():
    if not settings.transcript_encryption_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TRANSCRIPT_ENCRYPTION_KEY is required when encryption is enabled.",
        )

    try:
        from cryptography.fernet import Fernet, InvalidToken
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="cryptography package is required for encryption.",
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
