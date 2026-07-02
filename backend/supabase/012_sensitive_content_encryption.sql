-- Field-level encryption support for generated summaries and tasks.
-- Encryption/decryption is performed by the backend so keys do not live in the database.

alter table public.transcript_segments
    add column if not exists encrypted_text text,
    add column if not exists encryption_alg text,
    add column if not exists encryption_key_id text;

alter table public.meeting_summaries
    add column if not exists encrypted_summary text,
    add column if not exists encrypted_key_points text,
    add column if not exists encrypted_decisions text,
    add column if not exists encryption_alg text,
    add column if not exists encryption_key_id text;

alter table public.action_items
    add column if not exists encrypted_title text,
    add column if not exists encrypted_description text,
    add column if not exists title_lookup_hash text,
    add column if not exists title_lookup_hash_alg text,
    add column if not exists encryption_alg text,
    add column if not exists encryption_key_id text;

alter table public.tasks
    add column if not exists encrypted_title text,
    add column if not exists encrypted_description text,
    add column if not exists title_lookup_hash text,
    add column if not exists title_lookup_hash_alg text,
    add column if not exists encryption_alg text,
    add column if not exists encryption_key_id text;

create index if not exists idx_action_items_meeting_title_lookup
    on public.action_items(meeting_id, title_lookup_hash)
    where title_lookup_hash is not null;

create index if not exists idx_tasks_meeting_title_lookup
    on public.tasks(meeting_id, title_lookup_hash)
    where title_lookup_hash is not null;
