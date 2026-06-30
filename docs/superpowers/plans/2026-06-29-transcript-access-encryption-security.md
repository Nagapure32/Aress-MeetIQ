# Transcript Access And Encryption Security Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make meeting transcripts visible only to allowed meeting participants or audited super admins, while preventing ordinary org users, database users, and VM/resource users from casually reading transcript plaintext.

**Architecture:** Enforce access in three layers: backend authorization, database row policies, and application-level encryption. The backend verifies the signed-in user, checks meeting participant or super-admin permission, decrypts transcript text only in memory, returns plaintext only for that authorized request, and writes an audit event for every transcript access.

**Tech Stack:** FastAPI, Pydantic, Supabase/Postgres, Supabase Auth or Microsoft Entra ID claims, Azure Key Vault or equivalent KMS, Next.js frontend, .NET 8 Teams media bot, Azure Blob Storage, pytest, TypeScript checks.

---

## Easy Explanation

Today, transcript data can become risky if someone gets backend access, database access, or if a route forgets to check the user properly. The target security model is:

1. A user logs in.
2. The backend identifies the user from a verified token.
3. The backend checks whether that user was in the meeting or is a special super admin.
4. If the user is not allowed, the backend returns `403 Forbidden`.
5. If the user is allowed, the backend reads encrypted transcript rows.
6. The backend asks Key Vault for permission to decrypt the meeting key.
7. The backend decrypts transcript text in memory only.
8. The frontend receives normal text and displays the Transcript tab.
9. The system records who accessed which transcript and when.

The frontend never receives encryption keys. The database stores encrypted transcript text. The VM should not store long-lived secrets in `.env`.

---

## .NET Bot Compatibility Review

The .NET bot at `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot` is compatible with this security model only if we close its plaintext side channels.

Current bot behavior:

- `Bot/PlatformBotReportingClient.cs` sends transcript segments as plaintext to backend endpoint `internal/bot/transcripts`.
- `Bot/TranscriptBlobStorage.cs` writes live and final transcript files as plaintext JSON/text blobs.
- `Bot/CallHandler.cs` posts finalized transcript text to Teams chat through `TeamsTranscriptPoster`.
- `Bot/AudioHandler.cs` has a local plaintext `transcript_yyyyMMdd_HHmmss.txt` write path.
- `Controllers/JoinController.cs` exposes `/api/join` without route-level authorization.
- `Controllers/TranscriptTestController.cs` exposes `/api/test-transcript` with `[AllowAnonymous]`.
- `Controllers/CallsController.cs` must remain callable by Microsoft Graph/Bot Framework callbacks, but callback validation should be explicit.
- `appsettings.example.json` includes `TranscriptStorage`, `PlatformApi`, and approval-link settings that affect transcript confidentiality.

Compatibility decision:

- The bot can continue sending plaintext transcript segments to the backend over HTTPS because the backend can encrypt immediately on ingest.
- The bot must not persist plaintext transcript blobs unless the blobs are encrypted before upload or the storage feature is disabled.
- The bot should not post transcript lines into Teams chat by default, because that bypasses the participant-only Transcript tab and app audit trail.
- Bot endpoints that can trigger joins or transcript posts must require an internal service token or equivalent authentication.
---

## Security Rules To Implement

- Meeting transcripts are **participant-only by default**.
- Meeting organizer can view transcript if they are in `meeting_participants`.
- Org admin can manage organization settings but **cannot automatically read transcripts**.
- Super admin can read any transcript only through a special audited path.
- Service bot can write transcript data but should not have general read access.
- Normal database users should not see plaintext transcript data.
- VM/resource admins should not get plaintext data just because they can log into the machine.
- All transcript reads, exports, AI chat reads, and recording downloads must be audited.

---

## Files And Responsibilities

### Backend Auth And Roles

- Modify: `backend/app/auth/current_user.py`
  - Add trusted role/tenant fields to `CurrentUser`.
  - Validate production JWT claims strictly.

- Create: `backend/app/auth/roles.py`
  - Define role constants: `super_admin`, `org_admin`, `meeting_participant`, `service_bot`.

- Create: `backend/app/auth/authorization.py`
  - Centralize permission checks like `can_read_meeting_transcript`.

### Meeting Participant Access

- Modify or create migration under: `backend/supabase/`
  - Add or enforce `meeting_participants`.
  - Add indexes for `meeting_id`, `user_id`, `aad_user_id`, and `email`.

- Modify: `backend/app/services/meetings.py`
  - Make transcript, summary, and meeting reads use participant checks.

- Modify: `backend/app/api/v1/routes/meetings.py`
  - Ensure every transcript/summary/chat endpoint passes `current_user` into authorization checks.

### Transcript Encryption

- Create: `backend/app/security/key_management.py`
  - Wrap Key Vault/KMS operations.
  - Provide functions for wrapping/unwrapping per-meeting data keys.

- Create: `backend/app/security/transcript_crypto.py`
  - Encrypt/decrypt transcript text.
  - Keep plaintext only in memory.

- Modify: transcript storage code in `backend/app/services/uploaded_recordings.py` and bot ingestion services.
  - Encrypt transcript text before insert.

- Modify: transcript read code in `backend/app/services/meetings.py`.
  - Decrypt only after permission check.

### Audit Logging

- Create migration under: `backend/supabase/`
  - Add `transcript_access_audit` table.

- Create: `backend/app/services/audit.py`
  - Record successful and failed transcript access.

- Modify transcript, summary, recording, and meeting chat routes/services.
  - Write audit logs.

### Frontend

- Modify: transcript tab/page components under `frontend/app/meetings/`
  - Display `403` as â€œYou do not have access to this transcript.â€
  - Do not show raw backend error details.

- Modify: `frontend/lib/api.ts`
  - Map sensitive backend errors to safe UI messages.

### CI And Verification

- Add backend route tests for participant access, non-participant denial, and super-admin audited access.
- Add encryption tests proving the database/storage layer receives ciphertext, not plaintext.
- Add frontend tests for forbidden transcript UX.
- Add CI security checks for tests, dependency audit, and secret scanning.


### .NET Bot

- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Bot\PlatformBotReportingClient.cs`
  - Include participant identity fields needed for backend participant access.
  - Continue sending transcript text only to the trusted platform API over HTTPS.

- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Bot\TranscriptBlobStorage.cs`
  - Disable plaintext blob transcript storage, or encrypt blob content before upload.

- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Bot\CallHandler.cs`
  - Stop posting transcript text to Teams chat by default.
  - Keep only metadata logging, not transcript text.

- Modify or remove: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Bot\AudioHandler.cs`
  - Remove local plaintext transcript file writes if this path is active.

- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Controllers\JoinController.cs`
  - Require internal authentication for manual join and leave endpoints.

- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Controllers\TranscriptTestController.cs`
  - Disable in production or protect with internal authentication.

- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\appsettings.example.json`
  - Add safe defaults: transcript blob storage disabled unless encrypted, transcript chat posting disabled, approval-link logging disabled.
---

## Task 0: Make .NET Bot Compatible With Transcript Security

**Files:**
- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Bot\PlatformBotReportingClient.cs`
- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Bot\TranscriptBlobStorage.cs`
- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Bot\CallHandler.cs`
- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Bot\TeamsTranscriptPoster.cs`
- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Bot\AudioHandler.cs`
- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Controllers\JoinController.cs`
- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\Controllers\TranscriptTestController.cs`
- Modify: `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot\appsettings.example.json`

- [ ] **Step 1: Add bot config switches**

Add safe config options:

```json
{
  "TranscriptSecurity": {
    "PostTranscriptToTeamsChat": false,
    "PersistPlaintextBlobTranscripts": false,
    "PersistLocalPlaintextTranscript": false,
    "EnableTranscriptTestEndpoint": false,
    "RequireInternalAuthForJoin": true
  }
}
```

- [ ] **Step 2: Stop Teams chat transcript posting by default**

In `Bot/CallHandler.cs`, keep transcript posting only when explicitly enabled:

```csharp
if (_config.GetValue("TranscriptSecurity:PostTranscriptToTeamsChat", false))
{
    _ = _teamsTranscriptPoster.PostAsync(transcript);
}
```

Expected behavior: production does not post transcript text into Teams chat unless explicitly enabled.

- [ ] **Step 3: Stop plaintext blob persistence by default**

In `Bot/TranscriptBlobStorage.cs`, before creating blob clients, check:

```csharp
if (!_config.GetValue("TranscriptSecurity:PersistPlaintextBlobTranscripts", false))
{
    _logger.LogInformation("Plaintext transcript blob persistence is disabled.");
    _isConfigured = false;
    return;
}
```

Expected behavior: transcript plaintext is not written to Azure Blob Storage unless an encrypted storage implementation replaces this path.

- [ ] **Step 4: Remove or disable local plaintext transcript files**

In `Bot/AudioHandler.cs`, remove `File.AppendAllText(_transcriptPath, ...)` or guard it behind a development-only setting:

```csharp
if (config.GetValue("TranscriptSecurity:PersistLocalPlaintextTranscript", false))
{
    File.AppendAllText(_transcriptPath, line + Environment.NewLine);
}
```

Expected behavior: VM disk does not receive plaintext transcript files in production.

- [ ] **Step 5: Protect manual join endpoint**

Add internal authentication to `Controllers/JoinController.cs` for:

```text
POST /api/join
POST /api/calls/join
DELETE /api/join
```

The backend should call these endpoints with a service credential. `GET /api/join` can remain a health-style response only if it exposes no secrets.

- [ ] **Step 6: Protect or disable transcript test endpoint**

`Controllers/TranscriptTestController.cs` should return `404` in production unless `TranscriptSecurity:EnableTranscriptTestEndpoint=true` and internal authentication succeeds.

Expected behavior: anonymous users cannot post arbitrary transcript text into Teams chat.

- [ ] **Step 7: Preserve participant identity payload**

Keep sending these fields from `PlatformBotReportingClient.RecordTranscriptSegmentAsync`:

```text
speakerParticipantId
speakerAadUserId
speakerEmail
speakerUserPrincipalName
sourceId
language
```

The backend will use these fields to populate `meeting_participants` and support participant-only transcript access.

- [ ] **Step 8: Build bot**

Run from `C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot`:

```powershell
dotnet build
```

Expected: build succeeds.

---
## Task 1: Add Roles And Current User Shape

**Files:**
- Create: `backend/app/auth/roles.py`
- Modify: `backend/app/auth/current_user.py`
- Test: `backend/tests/test_current_user.py`

- [ ] **Step 1: Add role constants**

Create `backend/app/auth/roles.py`:

```python
SUPER_ADMIN = "super_admin"
ORG_ADMIN = "org_admin"
MEETING_PARTICIPANT = "meeting_participant"
SERVICE_BOT = "service_bot"

TRANSCRIPT_READ_ALL_ROLES = {SUPER_ADMIN}
```

- [ ] **Step 2: Extend `CurrentUser`**

Update `CurrentUser` in `backend/app/auth/current_user.py` conceptually to include:

```python
class CurrentUser(BaseModel):
    user_id: str
    email: str | None = None
    tenant_id: str | None = None
    aad_user_id: str | None = None
    roles: list[str] = []
    auth_source: Literal["supabase", "dev"]
```

- [ ] **Step 3: Add tests for roles and claims**

Add tests that verify:

```text
valid token creates CurrentUser with user_id/email/roles
missing exp is rejected
wrong audience is rejected
wrong issuer is rejected
dev fallback cannot be used in production
```

- [ ] **Step 4: Run tests**

Run:

```powershell
pytest backend/tests/test_current_user.py -v
```

Expected: all current-user tests pass.

---

## Task 2: Add Meeting Participant Authorization

**Files:**
- Create: `backend/app/auth/authorization.py`
- Modify: `backend/app/services/meetings.py`
- Test: `backend/tests/test_meeting_authorization.py`

- [ ] **Step 1: Create authorization helper**

Create `backend/app/auth/authorization.py`:

```python
from fastapi import HTTPException, status

from app.auth.current_user import CurrentUser
from app.auth.roles import SUPER_ADMIN
from app.db.supabase import supabase_gateway


async def require_transcript_access(current_user: CurrentUser, meeting_id: str) -> None:
    if SUPER_ADMIN in current_user.roles:
        return

    rows = await supabase_gateway.get(
        "meeting_participants",
        {
            "select": "meeting_id",
            "meeting_id": f"eq.{meeting_id}",
            "user_id": f"eq.{current_user.user_id}",
            "limit": "1",
        },
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this transcript.",
        )
```

- [ ] **Step 2: Use helper before transcript reads**

Every transcript read must do:

```python
await require_transcript_access(current_user, meeting_id)
```

before reading transcript rows.

- [ ] **Step 3: Test access rules**

Create tests for:

```text
participant can read transcript
non-participant gets 403
super_admin can read transcript
org_admin who is not participant gets 403
```

- [ ] **Step 4: Run tests**

Run:

```powershell
pytest backend/tests/test_meeting_authorization.py -v
```

Expected: participant and super admin pass; non-participant and org admin are denied.

---

## Task 3: Add Database Participant Model And RLS

**Files:**
- Create migration: `backend/supabase/0XX_transcript_access_security.sql`
- Test manually in Supabase SQL editor or local Postgres test harness.

- [ ] **Step 1: Add participant indexes**

Migration should ensure:

```sql
create index if not exists idx_meeting_participants_meeting_user
on public.meeting_participants (meeting_id, user_id);

create index if not exists idx_meeting_participants_aad_user
on public.meeting_participants (aad_user_id);

create index if not exists idx_transcript_segments_meeting
on public.transcript_segments (meeting_id);
```

- [ ] **Step 2: Enable RLS for transcript data**

Conceptual policy:

```sql
alter table public.transcript_segments enable row level security;

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
```

- [ ] **Step 3: Add super-admin database policy only if roles are available in JWT**

Only add this if super-admin role is safely present in verified JWT claims:

```sql
create policy "Super admins can read all transcripts"
on public.transcript_segments
for select
using (
  auth.jwt() -> 'app_metadata' -> 'roles' ? 'super_admin'
);
```

- [ ] **Step 4: Verify database behavior**

Verify:

```text
participant JWT can select transcript rows
non-participant JWT cannot select transcript rows
service role is not used for normal user reads
```

---

## Task 4: Add Transcript Encryption

**Files:**
- Create: `backend/app/security/key_management.py`
- Create: `backend/app/security/transcript_crypto.py`
- Modify: transcript write services
- Modify: transcript read services
- Test: `backend/tests/test_transcript_crypto.py`

- [ ] **Step 1: Create crypto interface**

Create `backend/app/security/transcript_crypto.py` with functions shaped like:

```python
def encrypt_transcript_text(plaintext: str, key: bytes) -> dict[str, str]:
    """Return nonce, ciphertext, and algorithm metadata."""
    ...


def decrypt_transcript_text(ciphertext: str, nonce: str, key: bytes) -> str:
    """Return plaintext for authorized request only."""
    ...
```

Implementation should use an authenticated encryption mode such as AES-GCM.

- [ ] **Step 2: Create key management interface**

Create `backend/app/security/key_management.py` with functions shaped like:

```python
async def get_or_create_meeting_data_key(meeting_id: str) -> bytes:
    ...


async def unwrap_meeting_data_key(meeting_id: str) -> bytes:
    ...
```

In production this should use Azure Key Vault or KMS. For tests, use a fake provider.

- [ ] **Step 3: Encrypt before storing**

Transcript storage should save:

```text
encrypted_text
encryption_nonce
encryption_algorithm
key_version
```

and should not store plaintext `text` for new transcript rows.

- [ ] **Step 4: Decrypt after authorization**

Transcript read flow should be:

```python
await require_transcript_access(current_user, meeting_id)
encrypted_rows = await load_transcript_rows(meeting_id)
key = await unwrap_meeting_data_key(meeting_id)
return decrypt_rows(encrypted_rows, key)
```

- [ ] **Step 5: Test encryption**

Tests must prove:

```text
plaintext is not present in stored payload
authorized read returns original plaintext
wrong key fails
non-participant cannot trigger decrypt
```

Run:

```powershell
pytest backend/tests/test_transcript_crypto.py -v
```

---

## Task 5: Add Transcript Access Audit Logs

**Files:**
- Create migration: `backend/supabase/0XX_transcript_access_audit.sql`
- Create: `backend/app/services/audit.py`
- Modify transcript/summary/chat/recording services
- Test: `backend/tests/test_transcript_audit.py`

- [ ] **Step 1: Add audit table**

Migration:

```sql
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
```

- [ ] **Step 2: Add audit service**

Create `backend/app/services/audit.py`:

```python
async def record_transcript_access(
    *,
    meeting_id: str,
    user_id: str | None,
    role: str | None,
    action: str,
    access_result: str,
    reason: str | None = None,
) -> None:
    ...
```

- [ ] **Step 3: Audit success and failure**

Audit:

```text
transcript_view_success
transcript_view_denied
summary_view_success
chat_with_transcript_success
recording_download_success
super_admin_access_success
```

- [ ] **Step 4: Test audit events**

Tests verify:

```text
participant transcript view writes success audit
non-participant denial writes denied audit
super admin access writes super_admin audit with reason
```

Run:

```powershell
pytest backend/tests/test_transcript_audit.py -v
```

---

## Task 6: Secure Frontend Transcript UX

**Files:**
- Modify: `frontend/lib/api.ts`
- Modify: transcript UI components under `frontend/app/meetings/`
- Test: frontend source tests if available.

- [ ] **Step 1: Map forbidden errors**

In frontend API helper, map `403` from transcript endpoints to safe copy:

```text
You do not have access to this transcript.
```

- [ ] **Step 2: Do not show raw backend details**

For transcript/security endpoints, avoid rendering raw `detail` strings from backend.

- [ ] **Step 3: Add UI state**

Transcript tab should show:

```text
No access: You do not have access to this transcript.
```

not an empty transcript and not a technical error.

- [ ] **Step 4: Verify frontend**

Run:

```powershell
npm run build
```

from `frontend`.

Expected: build succeeds and no transcript access error text leaks backend details.

---

## Task 7: Protect Operations And Deployment

**Files:**
- Modify: backend config validation
- Modify: frontend config validation
- Modify: GitHub workflows
- Modify deployment docs

- [ ] **Step 1: Backend production fail-closed**

Production must refuse to start if:

```text
AUTH_REQUIRED is not true
ALLOW_DEV_USER_FALLBACK is not false
SUPABASE_JWT_SECRET is missing
SUPABASE_SERVICE_ROLE_KEY is missing for background jobs
BOT_INTERNAL_API_KEY is weak/missing when internal APIs enabled
CORS includes wildcard or localhost
```

- [ ] **Step 2: Frontend production fail-closed**

Production frontend must refuse to build/start if:

```text
NEXT_PUBLIC_SUPABASE_URL missing
NEXT_PUBLIC_SUPABASE_ANON_KEY missing
NEXT_PUBLIC_API_BASE_URL missing
NEXT_PUBLIC_SITE_URL missing
```

- [ ] **Step 3: Move secrets out of VM `.env`**

Use:

```text
Azure Key Vault
Managed Identity
restricted access policies
no transcript keys stored in database or VM files
```

- [ ] **Step 4: Add CI gates**

CI should run:

```powershell
pytest
npm run build
npm audit --omit=dev --audit-level=moderate
secret scanning
```

---

## Task 8: Data Migration For Existing Plaintext Transcripts

**Files:**
- Create migration/backfill script under `backend/scripts/`
- Add dry-run documentation under `docs/`

- [ ] **Step 1: Identify existing plaintext columns**

List all transcript-like plaintext fields:

```text
transcript_segments.text
meeting_summaries.summary
meeting_summaries.key_points
meeting_summaries.decisions
meeting_chat_messages.content
vector/search chunks containing transcript text
```

- [ ] **Step 2: Write dry-run migration**

Dry run should report:

```text
number of meetings
number of transcript rows
number of summary rows
number of chat rows
rows already encrypted
rows needing encryption
```

- [ ] **Step 3: Encrypt existing rows**

Backfill should:

```text
create meeting data key
encrypt plaintext
write encrypted fields
verify decrypt works
remove or null plaintext field after verification
```

- [ ] **Step 4: Rebuild search/vector indexes with permission metadata**

Every indexed chunk must include:

```text
organization_id
meeting_id
allowed participant ids or meeting access policy
```

Search must filter before AI context is built.

---

## Task 9: Final Security Verification

**Files:**
- Test files across backend and frontend
- Deployment runbook

- [ ] **Step 1: Verify participant access**

Expected:

```text
participant can view transcript
participant can ask AI about transcript
participant can view summary
```

- [ ] **Step 2: Verify non-participant denial**

Expected:

```text
same-org non-participant gets 403
external user gets 403
anonymous user gets 401
```

- [ ] **Step 3: Verify org admin denial**

Expected:

```text
org_admin who is not participant gets 403 for transcript text
org_admin can still manage org settings
```

- [ ] **Step 4: Verify super admin audited access**

Expected:

```text
super_admin can view transcript
access requires reason
audit log is written
security alert is sent if configured
```

- [ ] **Step 5: Verify database confidentiality**

Expected:

```text
database transcript rows do not contain plaintext
database-only user cannot decrypt transcript text
backup exports do not contain plaintext transcripts
```

- [ ] **Step 6: Verify VM/resource confidentiality**

Expected:

```text
VM does not store transcript keys in .env
VM user without Key Vault permission cannot decrypt transcript rows
app logs do not contain transcript plaintext
temporary files do not contain transcript plaintext
```

---

## Rollout Order

1. Make .NET bot safe: disable plaintext blob/local/chat transcript outputs and protect join/test endpoints.
2. Add authorization tests and participant-only checks in the backend.
3. Lock down unauthenticated transcript/summary/chat/recording routes.
4. Add audit logs.
5. Add encryption for new transcript data.
6. Add Key Vault integration.
7. Backfill old plaintext transcript data.
8. Remove or null old plaintext columns after verification.
9. Add CI and deployment fail-closed checks.
10. Run production smoke tests across frontend, backend, and .NET bot.

---

## Questions To Confirm Before Implementation

1. Should **meeting organizer** be allowed to share transcript access with non-participants?
2. Should **external guests** get transcript access if they attended?
3. Should **org admin** be blocked from transcript text unless they were in the meeting?
4. Should **super admin** access require approval from another admin?
5. Should transcript downloads be allowed, or only viewing inside the app?
6. How long should audit logs be retained?
7. Which key provider should be used: Azure Key Vault, Supabase Vault, or another KMS?
8. Should transcript text ever be posted into Teams chat, or should it only be visible inside the secured Transcript tab?
9. Should the bot keep any transcript blob backup, or should the platform database be the only transcript store?

---

## Self-Review

- Spec coverage: participant-only access, super-admin access, database confidentiality, VM/resource confidentiality, encryption, frontend display, audit, migration, and CI are covered.
- Placeholder scan: no task uses unbounded â€œdo laterâ€ language; implementation details are defined at the right level for planning.
- Type consistency: `CurrentUser`, `roles`, `meeting_participants`, `transcript_access_audit`, and encryption helper names are consistent across tasks.



