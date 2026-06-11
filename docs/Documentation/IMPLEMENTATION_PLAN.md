# MeetIQ Implementation Plan

## 1. Goal

Build the full MeetIQ productivity platform around the already completed ASP.NET Core Teams media bot.

The existing `.NET` bot remains responsible for Microsoft Teams, Microsoft Graph communications, meeting join, audio capture, transcription, approval cards, and transcript posting. The new platform will provide the user-facing product experience, multi-user configuration, analytics, AI summaries, tasks, and meeting knowledge search.

## 2. Repository Strategy

Use two repositories.

```text
Repo 1: teams-media-bot-dotnet
Repo 2: productivity-platform
```

### Repo 1: teams-media-bot-dotnet

Purpose:

```text
Teams bot endpoint
Microsoft Graph calendar scanning
Teams approval cards
Meeting join / leave
Audio receive
Azure Speech transcription
Transcript posting back to Teams
Bot-to-platform event publishing
```

The `.NET` bot already has a bundled/static frontend. Do not use that as the product frontend. It can remain only for bot debugging or internal testing.

### Repo 2: productivity-platform

Purpose:

```text
FastAPI backend
Next.js frontend
Supabase Auth
Supabase PostgreSQL
Analytics dashboard
Meeting/task/productivity UI
AI summaries and action items
AI chat over meeting knowledge
Bot integration APIs
```

Suggested structure:

```text
productivity-platform/
  backend/
    app/
      api/
      auth/
      core/
      db/
      models/
      schemas/
      services/
      integrations/
      workers/
      analytics/
      ai/
      bot_integration/
    tests/
    pyproject.toml
    .env.example

  frontend/
    app/
    components/
    lib/
    hooks/
    styles/
    public/
    package.json
    .env.example

  docs/
    contracts/
      bot-platform-api.md
    architecture.md

  docker-compose.yml
  README.md
```

## 3. Architecture

Use a modular monolith for the platform backend, plus the separate `.NET` bot service.

```text
Next.js frontend
  -> FastAPI backend
  -> Supabase PostgreSQL

.NET Teams bot
  -> FastAPI internal bot APIs
  -> Microsoft Graph / Teams / Azure Speech
```

The `.NET` bot should not write directly to Supabase. It should communicate with FastAPI through internal API endpoints. FastAPI owns product data, authorization, validation, analytics, and business rules.

## 4. Technology Choices

Frontend:

```text
Next.js
React
TypeScript
TailwindCSS
Motion / motion-react style animation package
Supabase client
Chart library for analytics
```

Backend:

```text
FastAPI
Pydantic
SQLAlchemy or Supabase Python client
Supabase JWT verification
Background workers
OpenAI / Azure OpenAI integration later
```

Database/Auth:

```text
Supabase PostgreSQL
Supabase Auth
Row Level Security
pgvector later for AI chat / RAG
```

Bot:

```text
ASP.NET Core 8
Microsoft Graph communications APIs
Bot Framework
Azure Speech
Azure Blob transcript storage
```

## 5. Figma Frontend Baseline

The user-facing frontend must follow the provided Figma wireframe:

```text
https://www.figma.com/proto/rxRBFb0sPUNxBvMHRR5eIE/Productivity_Tool_WireFrame?node-id=25-2
```

Detected product screens:

```text
Screen 01 - Main Dashboard
Screen 02 - Meeting Detail / Transcript / Summary
Screen 03 - Task Board
Screen 04 - AI Chat
Screen 05 - New User Onboarding / Connect Calendar
```

Visual baseline:

```text
Product name: MeetIQ
Primary color: #3d35b0
Background: #f5f4f0
Card background: #ffffff
Border: #e2e1dc
Text primary: #1a1a18
Text secondary: #6b6b66
Fonts: DM Sans, DM Mono
UI style: compact SaaS dashboard
```

The Figma screens are the visual source of truth, but the frontend must also include backend/bot features that are not shown in the wireframe.

## 6. Frontend Routes

Initial route map:

```text
/login
/onboarding
/dashboard
/meetings
/meetings/[id]
/approvals
/tasks
/ai-chat
/analytics
/integrations
/settings
/settings/meeting-assistant
/settings/transcription
/settings/bot-events
```

Optional admin routes:

```text
/admin/bot-health
/admin/bot-events
```

Sidebar navigation:

```text
Main
- Dashboard
- Meetings
- Approvals
- Tasks
- AI Chat

Workspace
- Channels
- Analytics
- Integrations

Account
- Settings
```

Settings sections:

```text
Profile
Meeting Assistant
Transcription
Notifications
Security
Bot Events
```

## 7. Frontend Features

### Dashboard

Based on the Figma main dashboard.

Show:

```text
Meetings today
Meetings this week
Weekly meeting hours
Pending approvals
Open action items
Recent transcripts
Upcoming meetings
AI-detected action items
Active channels
```

Charts:

```text
Meetings by day
Meeting hours by week
Action items by status
Task completion trend
```

### Meetings

Show:

```text
Upcoming meetings
Completed meetings
Meetings waiting for approval
Bot status per meeting
Transcript availability
Summary availability
Action item count
```

### Meeting Detail

Tabs:

```text
Transcript
Summary
Tasks
Storage / Export
```

Features:

```text
Meeting metadata
Approval status
Bot join status
Speaker-labeled transcript
Detected language per segment
Summary
Decisions
Action items
Linked tasks
Download transcript
Download summary
```

### Task Board

Based on the Figma task board.

Features:

```text
Task columns by status
Task cards
Assignee
Priority
Due date
Source meeting
Link back to transcript segment
```

### AI Chat

Based on the Figma AI chat screen.

Features:

```text
Ask questions across meetings
Suggested prompts
Source citations
Meeting and timestamp references
Generate follow-up email
```

### Onboarding

Based on the Figma onboarding flow.

Steps:

```text
Create account
Connect calendar
Profile setup
Join or create team
```

Calendar connection screen:

```text
Microsoft Outlook / Microsoft 365 supported first
Google Calendar shown as post-MVP / coming soon
```

### Approvals

This is not fully represented in the Figma wireframe but must be added.

Show:

```text
Pending approvals
Approved meetings
Rejected meetings
Expired approvals
Approve / Reject buttons
Approval method: Teams, email, web
Approval expiry time
Meeting subject/start/end
```

### Meeting Assistant Settings

Expose bot behavior that is currently in `appsettings.json`.

Settings:

```text
Enable auto-join
Require approval before joining
Approval lead minutes
Join early seconds
Max late join minutes
Leave grace minutes
Use service-hosted media
```

### Transcription Settings

Expose multilingual transcription settings.

Settings:

```text
Auto language detection enabled
Language ID mode: AtStart / Continuous
Candidate languages
Default fallback language
```

Initial candidate languages:

```text
en-IN
en-US
hi-IN
mr-IN
```

### Integrations / Bot Health

Show:

```text
Microsoft Teams bot connection status
Microsoft Graph calendar access status
Azure Speech status
Transcript storage status
Last bot heartbeat
Last calendar scan
Last successful meeting join
Bot callback URL
Teams messaging endpoint status
```

### Teams Bot Setup Checklist

Important because the current working Teams approval path requires the user to message the bot first.

Show checklist:

```text
Install Teams app
Open bot chat
Send "Hi"
Conversation reference saved
Approval cards enabled
Transcript posting enabled
```

Statuses:

```text
Ready
Needs user message
Missing Teams app install
Reference lost after bot restart
```

### Bot Events

Troubleshooting screen.

Show:

```text
Calendar scan started
Meeting detected
Approval requested
Teams card sent
Email approval sent
Join attempted
Join succeeded
Audio started
Transcript segment received
Meeting ended
Error events
```

## 8. Supabase Data Model

Initial tables:

```text
profiles
organizations
organization_members
calendar_connections
meeting_settings
meetings
meeting_participants
meeting_approvals
transcript_segments
meeting_summaries
action_items
tasks
ai_chat_messages
bot_events
bot_heartbeats
```

### profiles

```text
id
email
display_name
avatar_url
role_title
timezone
created_at
updated_at
```

### organizations

```text
id
name
created_at
updated_at
```

### organization_members

```text
id
organization_id
user_id
role
created_at
```

### calendar_connections

```text
id
user_id
provider
tenant_id
aad_user_id
email
enabled
connection_status
last_sync_at
created_at
updated_at
```

### meeting_settings

```text
id
user_id
auto_join_enabled
require_approval
approval_lead_minutes
look_ahead_minutes
join_early_seconds
max_late_join_minutes
leave_grace_minutes
use_service_hosted_media
created_at
updated_at
```

### meetings

```text
id
user_id
organization_id
graph_event_id
subject
organizer_email
join_url
start_time
end_time
status
bot_status
approval_status
created_at
updated_at
```

### meeting_approvals

```text
id
meeting_id
user_id
status
requested_at
expires_at
decided_at
decided_by
decided_via
created_at
updated_at
```

### transcript_segments

```text
id
meeting_id
speaker
source_id
language
text
started_at
ended_at
created_at
```

### meeting_summaries

```text
id
meeting_id
summary
key_points
decisions
model
created_at
updated_at
```

### action_items

```text
id
meeting_id
assignee_user_id
title
description
status
priority
due_date
source_transcript_segment_id
created_at
updated_at
```

### tasks

```text
id
organization_id
owner_user_id
assignee_user_id
meeting_id
action_item_id
title
description
status
priority
due_date
created_at
updated_at
```

### bot_events

```text
id
bot_instance_id
user_id
meeting_id
event_type
severity
message
payload
created_at
```

### bot_heartbeats

```text
id
bot_instance_id
version
status
last_seen_at
payload
```

## 9. FastAPI Backend Modules

Modules:

```text
auth
profiles
organizations
calendar_connections
meeting_settings
meetings
transcripts
summaries
tasks
analytics
ai_chat
bot_integration
health
```

Public frontend APIs:

```text
GET  /api/v1/me
GET  /api/v1/dashboard

GET  /api/v1/settings/meeting-assistant
PUT  /api/v1/settings/meeting-assistant
GET  /api/v1/settings/transcription
PUT  /api/v1/settings/transcription

GET  /api/v1/meetings
GET  /api/v1/meetings/{id}
GET  /api/v1/meetings/{id}/transcript
GET  /api/v1/meetings/{id}/summary
GET  /api/v1/meetings/{id}/tasks

GET  /api/v1/approvals
POST /api/v1/approvals/{id}/approve
POST /api/v1/approvals/{id}/reject

GET  /api/v1/tasks
POST /api/v1/tasks
PUT  /api/v1/tasks/{id}
DELETE /api/v1/tasks/{id}

GET  /api/v1/analytics/overview
GET  /api/v1/analytics/calendar
GET  /api/v1/analytics/tasks

POST /api/v1/ai/chat
GET  /api/v1/integrations/bot-health
GET  /api/v1/integrations/bot-events
```

Internal bot APIs:

```text
GET  /internal/bot/calendar-users
POST /internal/bot/meetings/upsert
POST /internal/bot/meetings/{meeting_id}/status
POST /internal/bot/transcripts
POST /internal/bot/events
POST /internal/bot/heartbeats
POST /internal/bot/approvals/{approval_id}/decision
```

Use service authentication:

```text
Authorization: Bearer BOT_INTERNAL_API_KEY
```

## 10. Bot Integration Contract

The `.NET` bot should call FastAPI to fetch users and report events.

### Calendar Users

Endpoint:

```text
GET /internal/bot/calendar-users
```

Response:

```json
[
  {
    "user_id": "uuid",
    "tenant_id": "tenant-id",
    "aad_user_id": "graph-user-id",
    "email": "person@company.com",
    "auto_join_enabled": true,
    "require_approval": true,
    "look_ahead_minutes": 15,
    "approval_lead_minutes": 2,
    "join_early_seconds": 0,
    "max_late_join_minutes": 10,
    "leave_grace_minutes": 2
  }
]
```

### Meeting Upsert

Endpoint:

```text
POST /internal/bot/meetings/upsert
```

Payload:

```json
{
  "user_id": "uuid",
  "graph_event_id": "AAMk...",
  "subject": "Sprint Planning",
  "organizer_email": "organizer@company.com",
  "join_url": "https://teams.microsoft.com/l/meetup-join/...",
  "start_time": "2026-05-15T10:00:00Z",
  "end_time": "2026-05-15T10:30:00Z",
  "status": "detected",
  "approval_status": "pending"
}
```

### Transcript Segment

Endpoint:

```text
POST /internal/bot/transcripts
```

Payload:

```json
{
  "bot_instance_id": "teams-bot-prod-1",
  "user_id": "uuid",
  "meeting_id": "uuid",
  "graph_event_id": "AAMk...",
  "speaker": "Priya Sharma",
  "source_id": "12345",
  "language": "hi-IN",
  "text": "आज का discussion project timeline पर है",
  "occurred_at": "2026-05-15T10:30:00Z"
}
```

### Bot Event

Endpoint:

```text
POST /internal/bot/events
```

Payload:

```json
{
  "bot_instance_id": "teams-bot-prod-1",
  "user_id": "uuid",
  "meeting_id": "uuid",
  "event_type": "meeting_join_succeeded",
  "severity": "info",
  "message": "Bot joined the meeting successfully.",
  "payload": {}
}
```

## 11. Remove Hardcoded Calendar User

Current `.NET` bot behavior:

```json
"CalendarUserId": "shweta.nagpure@aress.com"
```

Target behavior:

```text
.NET bot fetches enabled calendar users from FastAPI
```

New flow:

```text
User signs up in Next.js
-> user connects Microsoft calendar
-> user enables meeting assistant
-> FastAPI stores meeting settings in Supabase
-> .NET bot calls /internal/bot/calendar-users
-> bot scans every enabled user's calendar
-> bot sends meeting/transcript/status events back to FastAPI
-> dashboard shows meetings and analytics per user
```

This is required to make the platform usable by more than one person.

## 12. Analytics Dashboard

Dashboard stats:

```text
Meetings today
Meetings this week
Meeting hours this week
Upcoming meetings
Pending approvals
Completed meetings
Transcript minutes
Action items created
Open tasks
Completed tasks
Average meeting duration
Top recurring organizers
```

Charts:

```text
Meetings by day
Meeting hours by week
Action items by status
Task completion trend
Transcript volume over time
```

Backend endpoints:

```text
GET /api/v1/analytics/overview
GET /api/v1/analytics/calendar
GET /api/v1/analytics/tasks
```

## 13. AI Features

Implement after the meeting/transcript/task foundation is working.

### Meeting Summary

Flow:

```text
Meeting completed
-> collect transcript segments
-> generate summary
-> extract key points
-> extract decisions
-> store in meeting_summaries
```

### Action Items

Flow:

```text
Transcript
-> extract action items
-> infer assignee if possible
-> infer due date if possible
-> create action_items
-> allow user to convert to tasks
```

### AI Chat / RAG

Flow:

```text
Transcript segments
-> chunking
-> embeddings
-> Supabase pgvector
-> semantic search
-> AI response with meeting/timestamp citations
```

Endpoint:

```text
POST /api/v1/ai/chat
```

## 14. Phased Rollout

### Phase 1: Platform Scaffold

Deliver:

```text
productivity-platform repo
FastAPI backend scaffold
Next.js frontend scaffold
Supabase connection
Supabase Auth integration
base layout from Figma
```

### Phase 2: Core Data Model

Deliver:

```text
Supabase tables
RLS policies
profiles
organizations
meeting settings
calendar connections
meetings
transcript segments
tasks
bot events
```

### Phase 3: Onboarding and Settings

Deliver:

```text
login
onboarding flow
connect Microsoft calendar screen
meeting assistant settings
transcription settings
Teams bot setup checklist
```

### Phase 4: Bot Integration APIs

Deliver:

```text
/internal/bot/calendar-users
/internal/bot/meetings/upsert
/internal/bot/transcripts
/internal/bot/events
/internal/bot/heartbeats
service API key auth
contract documentation
```

### Phase 5: Multi-User .NET Bot Change

Deliver:

```text
remove dependency on hardcoded CalendarUserId
fetch enabled users from FastAPI
scan calendars per user
send meeting status events to FastAPI
send transcript segments to FastAPI
send heartbeat/events to FastAPI
```

### Phase 6: Dashboard and Meetings

Deliver:

```text
Figma-style dashboard
meetings list
meeting detail page
transcript tab
summary placeholder
tasks/action items placeholder
analytics cards
```

### Phase 7: Approvals and Bot Health

Deliver:

```text
approvals page
approve/reject from web app
integration health page
bot event log
conversation reference status
```

### Phase 8: Task Board

Deliver:

```text
Figma-style task board
create/update/delete tasks
meeting-linked tasks
action-item-to-task flow
```

### Phase 9: AI Summary and Action Items

Deliver:

```text
summary worker
key point extraction
decision extraction
action item extraction
task suggestions
```

### Phase 10: AI Chat / RAG

Deliver:

```text
transcript chunking
pgvector embeddings
meeting knowledge search
AI chat UI
source citations
```

### Phase 11: Production Hardening

Deliver:

```text
audit logs
rate limits
retry handling
error monitoring
secret management
deployment scripts
CI/CD
Supabase backup strategy
```

## 15. First Milestone

The first working milestone should be:

```text
User logs in
-> completes onboarding
-> connects Microsoft calendar / enables meeting assistant
-> dashboard shows user meeting settings and placeholder analytics
-> FastAPI exposes /internal/bot/calendar-users
-> .NET bot reads users from FastAPI instead of a hardcoded CalendarUserId
```

This milestone proves the most important architectural change: the system becomes a multi-user platform instead of a single-user bot.

## 16. Implementation Start Checklist

Before starting implementation:

```text
Confirm final repo names
Confirm Supabase project URL and anon/service keys
Confirm Microsoft app registration strategy for multi-user use
Confirm whether FastAPI should use SQLAlchemy or Supabase client first
Confirm deployment target for Next.js and FastAPI
Confirm whether existing .NET bot repo should be copied into a new clean repo name
```

