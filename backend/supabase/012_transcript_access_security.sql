-- Enforce participant-scoped transcript access at the database layer.
-- The backend still performs its own authorization before decrypting transcript text.

alter table public.meeting_participants
    add column if not exists user_id uuid references auth.users(id) on delete set null;

create index if not exists idx_meeting_participants_meeting_user
    on public.meeting_participants(meeting_id, user_id);

create index if not exists idx_meeting_participants_aad_user
    on public.meeting_participants(aad_user_id);

create index if not exists idx_meeting_participants_email
    on public.meeting_participants(lower(email));

create index if not exists idx_meeting_participants_upn
    on public.meeting_participants(lower(user_principal_name));

create index if not exists idx_transcript_segments_meeting
    on public.transcript_segments(meeting_id);

alter table public.transcript_segments enable row level security;
alter table public.meeting_participants enable row level security;

create policy "Participants can read own meeting transcript"
on public.transcript_segments
for select
using (
    exists (
        select 1
        from public.meeting_participants mp
        where mp.meeting_id = transcript_segments.meeting_id
        and mp.user_id = auth.uid()
    )
);

create policy "Super admins can read all transcripts"
on public.transcript_segments
for select
using (
    coalesce(auth.jwt() -> 'app_metadata' -> 'roles', '[]'::jsonb) ? 'super_admin'
);

create policy "Users can read own participant records"
on public.meeting_participants
for select
using (
    user_id = auth.uid()
    or coalesce(auth.jwt() -> 'app_metadata' -> 'roles', '[]'::jsonb) ? 'super_admin'
);