from __future__ import annotations

from typing import Any

from app.services.sensitive_fields import (
    SENSITIVE_LOOKUP_HASH_ALGORITHM,
    decrypt_json_field,
    decrypt_text_field,
    lookup_hash_for_text,
    protect_json_field,
    protect_text_field,
    sensitive_field_encryption_enabled,
    strip_encrypted_fields,
)

ENCRYPTED_SUMMARY_PLACEHOLDER = "[encrypted meeting summary]"
ENCRYPTED_TASK_TITLE_PLACEHOLDER = "[encrypted task title]"
ENCRYPTED_TASK_DESCRIPTION_PLACEHOLDER = "[encrypted task description]"

SUMMARY_FIELDS = ["summary", "key_points", "decisions"]
TASK_CONTENT_FIELDS = ["title", "description"]


def protect_meeting_summary_content(
    summary: str,
    key_points: list[str],
    decisions: list[str],
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    payload.update(
        protect_text_field(
            "summary",
            summary,
            placeholder=ENCRYPTED_SUMMARY_PLACEHOLDER,
        )
    )
    payload.update(
        protect_json_field(
            "key_points",
            key_points,
            plaintext_placeholder=[],
        )
    )
    payload.update(
        protect_json_field(
            "decisions",
            decisions,
            plaintext_placeholder=[],
        )
    )
    return payload


def decrypt_meeting_summary_content(
    row: dict[str, Any],
    *,
    strip: bool = True,
) -> dict[str, Any]:
    decrypted = decrypt_text_field(row, "summary")
    decrypted = decrypt_json_field(decrypted, "key_points", default=[])
    decrypted = decrypt_json_field(decrypted, "decisions", default=[])
    return strip_encrypted_fields(decrypted, SUMMARY_FIELDS) if strip else decrypted


def protect_task_content(title: str, description: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    payload.update(
        protect_text_field(
            "title",
            title,
            placeholder=ENCRYPTED_TASK_TITLE_PLACEHOLDER,
        )
    )
    payload.update(
        protect_text_field(
            "description",
            description,
            placeholder=ENCRYPTED_TASK_DESCRIPTION_PLACEHOLDER,
        )
    )
    if sensitive_field_encryption_enabled():
        payload["title_lookup_hash"] = lookup_hash_for_text(title)
        payload["title_lookup_hash_alg"] = SENSITIVE_LOOKUP_HASH_ALGORITHM
    return payload


def protect_task_update_content(payload: dict[str, Any]) -> dict[str, Any]:
    protected = payload.copy()
    if "title" in payload:
        title = None if payload["title"] is None else str(payload["title"]).strip()
        protected.pop("title", None)
        protected.update(
            protect_text_field(
                "title",
                title,
                placeholder=ENCRYPTED_TASK_TITLE_PLACEHOLDER,
            )
        )
        if title is not None and sensitive_field_encryption_enabled():
            protected["title_lookup_hash"] = lookup_hash_for_text(title)
            protected["title_lookup_hash_alg"] = SENSITIVE_LOOKUP_HASH_ALGORITHM
        elif not sensitive_field_encryption_enabled():
            protected["title_lookup_hash"] = None
            protected["title_lookup_hash_alg"] = None
    if "description" in payload:
        description = payload.get("description")
        protected.pop("description", None)
        protected.update(
            protect_text_field(
                "description",
                description,
                placeholder=ENCRYPTED_TASK_DESCRIPTION_PLACEHOLDER,
            )
        )
    return protected


def decrypt_task_content(row: dict[str, Any], *, strip: bool = True) -> dict[str, Any]:
    decrypted = decrypt_text_field(row, "title")
    decrypted = decrypt_text_field(decrypted, "description")
    if strip:
        decrypted = strip_encrypted_fields(decrypted, TASK_CONTENT_FIELDS)
        decrypted.pop("title_lookup_hash", None)
        decrypted.pop("title_lookup_hash_alg", None)
    return decrypted


def decrypt_task_contents(rows: list[dict[str, Any]], *, strip: bool = True) -> list[dict[str, Any]]:
    return [decrypt_task_content(row, strip=strip) for row in rows]


def title_lookup_keys(title: Any) -> list[str]:
    keys = []
    title_hash = lookup_hash_for_text(title)
    if title_hash:
        keys.append(f"hash:{title_hash}")

    normalized = " ".join(str(title or "").lower().split())
    if normalized:
        keys.append(f"text:{normalized}")
    return keys
