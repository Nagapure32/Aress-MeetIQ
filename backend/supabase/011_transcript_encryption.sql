-- Adds optional encrypted transcript storage columns.
-- Existing plaintext rows continue to work. New encrypted writes keep the legacy
-- text column populated with a placeholder because the original schema requires it.

alter table public.transcript_segments
    add column if not exists encrypted_text text,
    add column if not exists encryption_alg text,
    add column if not exists encryption_key_id text;

create index if not exists idx_transcript_segments_encryption_key
    on public.transcript_segments(encryption_key_id)
    where encryption_key_id is not null;