create table if not exists public.transcript_access_audit (
    id uuid primary key default gen_random_uuid(),
    meeting_id uuid not null,
    user_id uuid,
    role text,
    action text not null,
    access_result text not null,
    reason text,
    ip_address text,
    user_agent text,
    created_at timestamptz not null default now()
);

create index if not exists idx_transcript_access_audit_meeting_created
    on public.transcript_access_audit(meeting_id, created_at desc);

create index if not exists idx_transcript_access_audit_user_created
    on public.transcript_access_audit(user_id, created_at desc);

alter table public.transcript_access_audit enable row level security;