from types import SimpleNamespace


def test_protect_transcript_text_preserves_plaintext_when_disabled(monkeypatch):
    from app.services import transcript_security

    monkeypatch.setattr(
        transcript_security,
        "settings",
        SimpleNamespace(enable_transcript_encryption=False),
    )

    assert transcript_security.protect_transcript_text("hello") == {"text": "hello"}


def test_protect_and_decrypt_transcript_text_when_enabled(monkeypatch):
    from app.services import transcript_security

    class FakeFernet:
        def encrypt(self, value: bytes) -> bytes:
            return b"cipher:" + value

        def decrypt(self, value: bytes) -> bytes:
            assert value == b"cipher:secret"
            return b"secret"

    monkeypatch.setattr(
        transcript_security,
        "settings",
        SimpleNamespace(
            enable_transcript_encryption=True,
            transcript_encryption_key_id="test-key",
        ),
    )
    monkeypatch.setattr(transcript_security, "_fernet_for_current_key", lambda: FakeFernet())

    protected = transcript_security.protect_transcript_text("secret")

    assert protected == {
        "text": "[encrypted transcript]",
        "encrypted_text": "cipher:secret",
        "encryption_alg": "fernet-v1",
        "encryption_key_id": "test-key",
    }
    assert transcript_security.decrypt_transcript_segment(protected)["text"] == "secret"