# Productivity Improvement Platform — PRD v2.0

**Version**: 2.0  
**Date**: 2026-04-21  
**Status**: Draft  
**Based on**: MVP Feature Analysis PDF + AI Agent Meeting Integration Document

---

## 1. Executive Summary

### 1.1 Project Overview
The Productivity Improvement Platform is an AI-powered meeting intelligence and task management solution. Inspired by tools like Otter.ai, the platform's core value is transforming every meeting into structured, searchable, and actionable knowledge — automatically joining meetings, transcribing conversations in real time, extracting action items, and feeding them into a collaborative task management system.

### 1.2 Business Objectives
- Eliminate manual note-taking through AI-powered meeting intelligence
- Reduce time spent on post-meeting follow-ups by 60% via automated action item creation
- Improve team productivity by 35% through AI-driven task prioritization
- Create a searchable organizational knowledge base from every conversation

### 1.3 Target Audience
- **Primary**: Medium to large enterprises (50–5000 employees) using Microsoft Teams
- **Secondary**: Sales, recruiting, education, and media teams needing specialized meeting intelligence
- **Tertiary**: Remote and hybrid teams seeking asynchronous collaboration tools

---

## 2. System Architecture Overview

### 2.1 Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, TailwindCSS, Chart.js |
| Backend | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| AI/ML | Agno, OpenAI GPT-4, Azure Speech Services |
| Message Bus | Apache Kafka |
| Database | PostgreSQL 15 (primary), Redis (cache) |
| Storage | Azure Blob Storage (audio/video/files) |
| Cloud | Azure App Service, Azure GraphAPI,Azure Bot framework, Azure OpenAI Services, Azure MCP |
| API Gateway |Nginx with JWT auth |
| Service Discovery | Consul |
| DevOps | Azure DevOps, Docker, GitHub Actions |
| Monitoring | Azure Application Insights |

### 2.2 High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                            │
├──────────────────────────────────────────────────────────────────┤
│   React Dashboard  │  Admin Panel  │  AI Chat  │  Analytics UI   │
└──────────────────────────────────────────────────────────────────┘
                                │  HTTPS / WSS
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                          API GATEWAY                             │
├──────────────────────────────────────────────────────────────────┤
│              Nginx  │  JWT Auth  │  Rate Limiting                │
└──────────────────────────────────────────────────────────────────┘
                                │
                                │  HTTP / WebSocket
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                          │
├──────────────────────────────────────────────────────────────────┤
│  Auth Service  │  Meeting Integration  │  Audio Processing        │
│  Transcription │  AI Processing        │  Task Management         │
│  Channels      │  Notifications        │  MCP Gateway             │
└──────────────────────────────────────────────────────────────────┘
                                │
                                │  Apache Kafka Event Streams
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                         AI / ML LAYER                            │
├──────────────────────────────────────────────────────────────────┤
│  Agno Multi-Agent Teams │  GPT-4  │  Azure Speech / WhisperX     │
│  pgvector RAG Search    │  Specialized Agents (Sales/Recruit)    │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                              │
├──────────────────────────────────────────────────────────────────┤
│  PostgreSQL 15 + pgvector  │  Redis Cache  │  Azure Blob Storage  │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                        │
├──────────────────────────────────────────────────────────────────┤
│  Azure App Service  │  Azure Functions  │  Azure Bot Framework    │
│  Azure Key Vault    │  Azure DevOps     │  Azure CDN               │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 Microservices Breakdown

```
API Gateway (Nginx)
        │
        ├── Auth Service
        ├── Meeting Integration Service  ← Teams bot, join/leave
        ├── Audio Processing Service     ← Real-time audio chunking
        ├── Transcription Service        ← Azure Speech, speaker ID
        ├── AI Processing Service        ← Agno multi-agent teams
        ├── Task Management Service      ← Task lifecycle + AI creation
        ├── Notification Service         ← WebSocket, email, Slack
        ├── Storage Service              ← Blob references, media
        ├── Channel Service              ← Meeting grouping
        ├── User Management Service      ← Profiles, voice recognition
        └── MCP Gateway Service          ← External AI tool access
```

**Inter-service communication:** All microservices communicate via Apache Kafka event streams. Key topics: `meeting-events`, `audio-events`, `transcription-events`, `ai-processing-events`, `notification-events`. Each service runs in its own Docker container with independent resources, circuit breakers (failure threshold: 5), and dead-letter queues for fault isolation.

> [!NOTE]
> **MCP Server clarification:** The `MCP Gateway Service` is a custom FastAPI service that implements the [Model Context Protocol](https://modelcontextprotocol.io) specification. "Azure MCP" in the tech stack refers to hosting this service on Azure App Service — there is no native Azure-managed MCP offering. The service exposes tool definitions and handles invocation routing to the meeting knowledge base.

### 2.4 Detailed Backend Service Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                      API Gateway (Nginx)                           │
│--------------------------------------------------------------------│
│  Auth  │  Rate Limiting  │  Routing  │  Logging                   │
└──────────────────────────────────────────────────────────────────┬─┘
                                                                   │
 ┌────────────────┬───────────────┬───────────────┬────────────────┴──────────┐
 │                │               │               │                           │
 ▼                ▼               ▼               ▼                           ▼
┌──────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Ingestion   │ │Transcription│ │AI Processing│ │Task Service  │ │Chat Service(RAG) │
│  Service     │ │  Service    │ │  Service    │ │              │ │                  │
└──────┬───────┘ └──────┬──────┘ └──────┬──────┘ └──────┬───────┘ └────────┬─────────┘
       │                │               │               │                  │
       ▼                ▼               ▼               ▼                  ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│Meeting Agent │ │Speech Engine│ │LLM           │ │Task Extractor│ │Retrieval Engine  │
│(Teams Bot)   │ │(Azure Speech│ │Orchestrator  │ │(from meeting)│ │(pgvector Search) │
│              │ │/ WhisperX)  │ │(Agno Team)   │ │              │ │                  │
└──────┬───────┘ └──────┬──────┘ └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘
       │                │               │               │                  │
       └────────────────┴───────────────┴───────────────┴──────────────────┘
                                        │
                                        ▼
              ┌────────────────────────────────────────────────────┐
              │              Message Queue                         │
              │  meeting-events │audio-events │transcription-events│
              └──────────────────────────┬─────────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              ▼                          ▼                           ▼
 ┌────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
 │   PostgreSQL DB    │    │  Vector Store        │    │   Object Storage     │
 │--------------------│    │  (pgvector)          │    │  (Azure Blob)        │
 │ - Users / Teams    │    │  - Transcript        │    │  - Audio / Video     │
 │ - Meetings         │    │    Embeddings        │    │  - Raw transcripts   │
 │ - Transcriptions   │    │  - Semantic chunks   │    │  - Meeting exports   │
 │ - Tasks / Channels │    └─────────────────────┘    └─────────────────────┘
 │ - Summaries / Notes│
 └────────────────────┘
                        │
                        ▼
          ┌─────────────────────────────────┐
          │         External Services        │
          │---------------------------------│
          │ - Microsoft Graph API (Teams)    │
          │ - Azure OpenAI (GPT-4)           │
          │ - Azure Speech Services          │
          │ - Salesforce / HubSpot (CRM)     │
          │ - Slack / MS Planner             │
          └─────────────────────────────────┘
```

### 2.5 Data Flow

```
Meeting Join → Audio Capture → Transcription → AI Analysis → Action Items
                                                     ↓
                              Real-time WebSocket Updates → Dashboard
                                                     ↓
                              Task Auto-Creation → Team Notification
```

---

## 3. Core Feature Set — Part 1: Meeting Intelligence

### 3.1 AI Notetaker / Meeting Agent ⭐ FLAGSHIP

The AI Notetaker is a virtual assistant that **automatically joins scheduled Microsoft Teams meetings**, records the conversation, and takes structured notes without human intervention.

**Capabilities:**
- Auto-join meetings from calendar invites (Microsoft Graph API)
- Record audio and optionally video streams
- Announce itself to participants ("Productivity AI has joined")
- Graceful exit when meeting ends or host removes it
- Configurable: users can enable/disable per meeting or by default

**Technical Flow:**
1. Calendar service detects upcoming meeting
2. Bot joins via Microsoft Graph `/communications/calls` API
3. Audio stream captured and chunked every 2 seconds
4. Chunks sent to Transcription Service via Kafka `audio-events` topic
5. Final notes compiled and pushed to user dashboard

### 3.2 Live Transcription

Real-time speech-to-text as meeting words are spoken.

**Capabilities:**
- Speaker recognition — labels each transcript segment by speaker name
- Multi-language support (English, Spanish, French, German, Hindi; configurable)
- Confidence scoring per transcription segment
- Real-time display on dashboard via WebSocket push
- Timestamped segments for precise replay navigation

**Technical Notes:**
- **Primary engine**: Azure Cognitive Services Speech SDK with `PushAudioInputStream`
- **Fallback engine**: WhisperX (self-hosted OpenAI Whisper large-v3) — activated automatically when Azure Speech confidence score < 0.70 or during Azure Speech service outages
- Segments published to `transcription-events` Kafka topic
- Stored in `transcriptions` PostgreSQL table with `speaker_id`, `confidence`, `language`

### 3.3 Automated Meeting Summaries

After every meeting ends, AI generates a structured summary automatically.

**Includes:**
- Key points discussed
- Decisions made
- Topics covered (extracted by LLM)
- Participation scores per speaker
- Sentiment analysis (positive / neutral / negative)
- Meeting productivity score

**Delivery:**
- Available in dashboard immediately after meeting
- Email summary sent to all participants
- Exportable as PDF, Word, or plain text
- Stored in `meeting_summaries` table with JSONB columns for structured data

### 3.4 Automated Action Items & Task Creation

AI automatically captures, tracks, and creates tasks from meeting conversations.

**Capabilities:**
- Detects commitment language ("I will...", "Can you handle...", "By Friday...")
- Extracts: task description, assignee, due date, priority
- Auto-creates tasks in the task management system
- Assigns to registered platform users by name match
- Sends follow-up reminders to assignees
- Tracks task completion and links back to source meeting

**Agno Agent:** `TaskExtractor` — part of the `MeetingAnalysisTeam` workflow

### 3.5 Audio / Video Import & Transcription

Users can upload pre-recorded audio and video files for transcription.

**Supported formats:** MP3, MP4, WAV, M4A, WEBM, MOV  
**Max file size:** 2 GB  
**Processing:** Async via Azure Functions — user notified on completion

**Flow:**
1. Upload via `POST /api/v1/media/upload` (multipart)
2. Stored in Azure Blob Storage
3. Video → audio extraction (ffmpeg)
4. Audio → Transcription Service pipeline (same as live meeting)
5. Full transcript + summary generated
6. Notification sent via WebSocket and email

---

## 4. Core Feature Set — Part 2: AI Assistant & Chat

### 4.1 AI Chat — Meeting Knowledge Search

An interactive AI assistant that searches across all past meeting transcriptions.

**Capabilities:**
- Natural language queries: "What did we decide about the Q3 budget?"
- Searches full transcript history with semantic vector search
- Drafts follow-up emails based on meeting outcomes
- Generates custom reports (weekly summaries, topic trends)
- Accessible via dashboard chat panel and API

**Technical:**
- Vector embeddings stored in PostgreSQL with `pgvector` extension
- OpenAI `text-embedding-3-small` for embedding generation
- GPT-4 for response synthesis with retrieved context
- Endpoint: `POST /api/v1/ai/chat`

### 4.2 External AI Integrations — MCP Server

Expose organizational meeting knowledge to third-party AI tools (ChatGPT, Claude, custom agents) via the **Model Context Protocol (MCP)**.

**MCP Tools Exposed:**
- `search_meetings` — semantic search across transcripts
- `get_meeting_summary` — retrieve summary for a specific meeting
- `list_action_items` — list open tasks created from meetings
- `get_team_insights` — aggregated team productivity data

**Security:**
- API key authentication per external tool
- Organization-scoped data isolation (no cross-org data leakage)
- Rate limiting: 100 requests/minute per API key
- Audit log of all MCP queries

**Endpoint:** `GET /api/v1/mcp/manifest` returns tool definitions

---

## 5. Core Feature Set — Part 3: Specialized Agents

All specialized agents are built on the same Agno base but with domain-specific prompts, tools, and knowledge bases.

### 5.1 Sales Notetaker Agent

For sales teams using CRM platforms.

**Capabilities:**
- Captures prospect name, company, deal stage, and objections from calls
- Automatically syncs meeting notes and deal details to Salesforce CRM
- Drafts follow-up emails with next steps
- Tracks deal mentions across multiple meetings

**Integrations:** Salesforce API, HubSpot API  
**Activation:** Enabled per team; requires CRM credentials configured in Settings

### 5.2 Education Notetaker Agent

For academic institutions and training teams.

**Capabilities:**
- Connects to educational calendar (Google Calendar, Outlook)
- Auto-joins and transcribes lectures and training sessions
- Organizes notes by course, week, and topic
- Generates study summaries and key concept extraction

**Activation:** Requires calendar integration; available as a team-level setting

### 5.3 Media Notetaker Agent

For content creators, journalists, and media teams.

**Capabilities:**
- Captures initial thoughts and brainstorming sessions
- Organizes into structured content outlines
- Extracts specific quotes with speaker attribution and timestamps
- Drafts content briefs from recorded ideation sessions

### 5.4 SDR (Sales Development Representative) Agent

For outbound sales and product demo teams.

**Capabilities:**
- Can be embedded on a company website via JavaScript snippet
- Handles live product demo conversations
- Answers prospect questions using product knowledge base
- Books follow-up meetings via calendar integration (Calendly / MS Bookings)

**Technical:** Deployed as a separate stateless microservice with widget embed support

### 5.5 Recruiting Agent

For HR and talent acquisition teams.

**Capabilities:**
- Joins interview calls and transcribes candidate responses
- Extracts candidate insights: skills mentioned, experience highlights, red flags
- Provides real-time question suggestions to the interviewer
- Syncs notes to recruiting platforms (Greenhouse, Lever, Workday)
- Generates structured candidate evaluation reports

---

## 6. Core Feature Set — Part 4: Organization & Collaboration

### 6.1 Channels

Groups meetings by team, project, or topic into shared workspaces for easy discovery.

**Capabilities:**
- Create channels (e.g., "Q3 Product Planning", "Sales Calls", "Engineering Standups")
- Auto-assign meetings to channels by calendar invite keywords or team membership
- Shared access — all channel members see all meetings and transcripts
- Channel-level search across all meeting content
- Channel analytics: meeting frequency, average duration, participation trends

**Data Model:** `channels` table with `team_id`, `name`, `description`, `auto_assign_rules (JSONB)`

### 6.2 Collaborative Note Editing

Real-time co-editing of meeting notes and summaries, similar to Google Docs.

**Capabilities:**
- AI-generated notes are the starting point; humans can edit inline
- Multiple users can edit simultaneously with presence indicators
- Edit history with version tracking
- Comments and mentions (@user) on specific note sections
- Changes auto-saved every 5 seconds

**Technical:**
- WebSocket-based operational transforms (OT) for conflict resolution
- `note_versions` table for history
- Presence broadcast via Redis pub/sub

### 6.3 Team Management & RBAC

**Roles:**
| Role | Permissions |
|---|---|
| Admin | Full org access, billing, user management, all data |
| Manager | Manage team channels, view team analytics, configure agents |
| Member | Access own meetings + team channels they belong to |
| Guest | View-only access to specific shared meetings |

**Multi-team support:** A user can belong to multiple teams via `user_team_memberships` junction table.

---

## 7. Core Feature Set — Part 5: Task Management

### 7.1 Task Lifecycle

Full task management system integrated with meeting intelligence.

**Capabilities:**
- Create tasks manually or auto-create from meeting action items
- Fields: title, description, assignee(s), due date, priority, status, linked meeting
- Task dependencies (blocked-by, blocks)
- Time tracking (manual entry + auto-detection from meeting discussions)
- Task comments linked back to transcript timestamps

### 7.2 AI Task Prioritization

Agno `TaskPrioritizationAgent` analyzes all open tasks and suggests daily priority order.

**Signals used:**
- Due date proximity
- Task urgency language from meeting transcript
- Assignee current workload
- Team goals and sprint targets
- Historical on-time completion patterns

### 7.3 Productivity Analytics

**Personal Dashboard:**
- Focus hours per day (from calendar + task tracking)
- Tasks completed vs. created ratio
- Meeting time vs. deep work time ratio
- Productivity score trend over time

**Team Dashboard:**
- Team task velocity
- Meeting load analysis (too many meetings flag)
- Action item completion rate per team member
- Workflow bottleneck identification

---

## 8. Integrations

### 8.1 Meeting Platforms
| Platform | Status | Integration Method |
|---|---|---|
| Microsoft Teams | ✅ MVP | Microsoft Graph API bot |

### 8.2 Project Management
| Tool | Sync Capability |
|---|---|
| Microsoft Planner | Tasks, notes export |
| Jira | Action items → Jira tickets |
| GitHub Issues | Dev tasks auto-creation |
| Microsoft Word / OneDrive | Meeting summaries export |

### 8.3 Communication & CRM
| Tool | Sync Capability |
|---|---|
| Slack | Meeting summary push, action item alerts |
| Microsoft Teams Chat | Summary cards via Teams bot |
| Salesforce | Deal data sync (Sales Agent) |
| HubSpot | Contact + note sync (Sales Agent) |
| Greenhouse / Lever | Candidate notes sync (Recruiting Agent) |

### 8.4 Calendar
- Microsoft Outlook / Exchange — meeting detection, auto-join scheduling
- Google Calendar — meeting detection (post-MVP)
- Calendly / MS Bookings — meeting scheduling (SDR Agent)

---

## 9. Database Schema

### 9.1 Database Schema Diagram

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  organizations  │  │     teams        │  │     users        │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ id (PK)         │◄──│ organization_id │  │ id (PK)         │
│ name            │  │ id (PK)         │◄─│ organization_id │
│ settings (JSONB)│  │ name            │  │ email (UNIQUE)  │
│ created_at      │  │ lead_id         │  │ name            │
│ updated_at      │  │ created_at      │  │ role (ENUM)     │
└─────────────────┘  └───────┬─────────┘  └───────┬─────────┘
                                │                         │
                    ┌────────┴─────────────────────────┘
                    ▼
         ┌─────────────────────┐  ┌─────────────────────┐
         │ user_team_memberships │  │      channels        │
         ├─────────────────────┤  ├─────────────────────┤
         │ user_id (FK)          │  │ id (PK)             │
         │ team_id (FK)          │  │ team_id (FK)        │
         │ role                  │  │ name                │
         │ joined_at             │  │ auto_assign_rules   │
         └─────────────────────┘  └─────────┬────────────┘
                                                  │
                                                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    meetings      │  │  transcriptions  │  │ meeting_summaries │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ id (PK)         │◄──│ meeting_id (FK)  │  │ meeting_id (FK)   │
│ team_id (FK)    │  │ speaker_name     │  │ key_points (JSON) │
│ channel_id (FK) │  │ text             │  │ action_items      │
│ platform (ENUM) │  │ confidence       │  │ decisions_made    │
│ status (ENUM)   │◄─│ language         │  │ sentiment_score   │
│ start_time      │  │ start/end_secs   │  │ productivity_score│
│ recording_url   │  └─────────────────┘  └─────────────────┘
└─────┬───────────┘
         │
 ┌────────┴─────────┐
 ▼                ▼
┌─────────────────┐  ┌─────────────────┐
│  meeting_notes  │  │  note_versions   │
├─────────────────┤  ├─────────────────┤
│ meeting_id (FK) │  │ meeting_id (FK) │
│ content (JSONB) │  │ version         │
│ version         │  │ content (JSONB) │
│ last_edited_by  │  │ edited_by (FK)  │
└─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│      tasks      │  │task_dependencies│  │  task_comments   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ id (PK)         │◄──│ task_id (FK)    │  │ task_id (FK)    │
│ team_id (FK)    │  │ depends_on (FK) │  │ author_id (FK)  │
│ source_meeting  │  └─────────────────┘  │ content         │
│   _id (FK)      │                      │ linked_transcript│
│ title           │◄────────────────────│   _id (FK)      │
│ status (ENUM)   │                      └─────────────────┘
│ priority (ENUM) │
│ due_date        │
└─────────────────┘
```

### 9.2 Core SQL Tables

```sql
-- ============================================================
-- ENUM DEFINITIONS
-- ============================================================
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'member', 'guest');
CREATE TYPE task_status AS ENUM ('todo', 'in_progress', 'blocked', 'in_review', 'done', 'cancelled');
CREATE TYPE task_priority AS ENUM ('critical', 'high', 'medium', 'low');
CREATE TYPE meeting_status AS ENUM ('scheduled', 'joining', 'active', 'ended', 'cancelled', 'processing');
CREATE TYPE insight_type AS ENUM ('summary', 'action_item', 'decision', 'sentiment', 'topic', 'productivity');
CREATE TYPE platform_type AS ENUM ('teams', 'zoom', 'meet', 'upload');

-- ============================================================
-- CORE TABLES
-- ============================================================

-- Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Teams
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    lead_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    profile_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- User-Team junction (many-to-many)
CREATE TABLE user_team_memberships (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, team_id)
);

-- Channels
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    auto_assign_rules JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Meetings
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id),
    channel_id UUID REFERENCES channels(id),
    platform VARCHAR(50) NOT NULL DEFAULT 'teams',
    platform_meeting_id VARCHAR(255),
    title VARCHAR(500),
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'scheduled',
    recording_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transcriptions
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    speaker_id VARCHAR(255),
    speaker_name VARCHAR(255),
    text TEXT NOT NULL,
    confidence DECIMAL(4,3),
    language VARCHAR(10) DEFAULT 'en-US',
    start_time_seconds DECIMAL(10,3),
    end_time_seconds DECIMAL(10,3),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Meeting Summaries
CREATE TABLE meeting_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    key_points JSONB,
    action_items JSONB,
    decisions_made JSONB,
    topics_discussed JSONB,
    sentiment_score DECIMAL(4,3),
    productivity_score DECIMAL(4,3),
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id),
    creator_id UUID NOT NULL REFERENCES users(id),
    assignee_id UUID REFERENCES users(id),
    source_meeting_id UUID REFERENCES meetings(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'todo',
    priority VARCHAR(50) NOT NULL DEFAULT 'medium',
    due_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Task Dependencies
CREATE TABLE task_dependencies (
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, depends_on_id)
);

-- Task Comments (with optional link back to transcript timestamp)
CREATE TABLE task_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    linked_transcription_id UUID REFERENCES transcriptions(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_task_comments_task_id ON task_comments(task_id);

-- Meeting Notes (collaborative — current live state)
CREATE TABLE meeting_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL UNIQUE REFERENCES meetings(id) ON DELETE CASCADE,
    content JSONB NOT NULL DEFAULT '{}',
    version INTEGER NOT NULL DEFAULT 1,
    last_edited_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Note Versions (edit history for collaborative notes)
CREATE TABLE note_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content JSONB NOT NULL,
    edited_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (meeting_id, version)
);
CREATE INDEX idx_note_versions_meeting_id ON note_versions(meeting_id);

-- Productivity Metrics
CREATE TABLE productivity_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    team_id UUID NOT NULL REFERENCES teams(id),
    date DATE NOT NULL,
    tasks_completed INTEGER DEFAULT 0,
    focus_hours DECIMAL(5,2) DEFAULT 0.0,
    meeting_hours DECIMAL(5,2) DEFAULT 0.0,
    productivity_score DECIMAL(4,3),
    UNIQUE (user_id, date)
);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 10. Agno AI Architecture

### 10.1 Meeting Analysis Team

The core AI workflow uses an Agno `Team` with specialized agents:

```
                    ┌─────────────────┐
                    │  Agno Team      │
                    │  (Orchestrator) │
                    └───────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Topic Agent  │ │ Task Agent   │ │ Insight Agent│
    └──────────────┘ └──────────────┘ └──────────────┘
```

**Workflow:** `MeetingAnalysisTeam` — coordinates Topic extraction, Action Item identification, Sentiment analysis, and Insight generation.

**Trigger:** Automatically runs when `meeting.ended` event published to Kafka.

### 10.2 AI Agents

| Agent | Trigger | Output |
|---|---|---|
| Meeting Analysis Agent | Meeting ends | Summary, action items, sentiment |
| Task Prioritization Agent | Daily 7 AM / on-demand | Ordered task list per user |
| Workflow Optimization Agent | Weekly | Process improvement suggestions |
| Team Performance Agent | Weekly | Team productivity insights |
| Sales Notetaker Agent | Sales meeting ends | CRM-ready deal notes |
| Recruiting Agent | Interview ends | Structured candidate evaluation |

### 10.3 AI Chat (RAG Pipeline)

```
User Query
  → Embedding (text-embedding-3-small)
  → pgvector similarity search on transcriptions
  → Top-K chunks retrieved
  → GPT-4 generates answer with context
  → Response + source citations returned
```

---

## 11. API Specifications

### 11.1 Authentication
```
POST /api/v1/auth/login
POST /api/v1/auth/register
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

### 11.2 Meeting Management
```
POST   /api/v1/meetings/join           — AI bot joins a live meeting
POST   /api/v1/meetings/{id}/leave     — Bot leaves meeting
GET    /api/v1/meetings                — List meetings (paginated)
GET    /api/v1/meetings/{id}           — Meeting details
GET    /api/v1/meetings/{id}/transcript — Full transcript
GET    /api/v1/meetings/{id}/summary   — Meeting summary
GET    /api/v1/meetings/{id}/insights  — AI insights
POST   /api/v1/meetings/{id}/notes     — Update collaborative notes
```

### 11.3 Media Import
```
POST   /api/v1/media/upload            — Upload audio/video file
GET    /api/v1/media/{id}/status       — Processing status
GET    /api/v1/media/{id}/transcript   — Resulting transcript
```

### 11.4 AI & Chat
```
POST   /api/v1/ai/chat                 — Query meeting knowledge base
POST   /api/v1/ai/task-prioritization  — Get prioritized task list
POST   /api/v1/ai/workflow-optimization — Team workflow suggestions
GET    /api/v1/mcp/manifest            — MCP tool definitions
POST   /api/v1/mcp/invoke              — Invoke MCP tool
```

### 11.5 Tasks
```
GET    /api/v1/tasks                   — List tasks
POST   /api/v1/tasks                   — Create task
PUT    /api/v1/tasks/{id}              — Update task
DELETE /api/v1/tasks/{id}             — Delete task
GET    /api/v1/tasks/{id}/dependencies — Task dependency graph
```

### 11.6 Channels & Teams
```
GET    /api/v1/channels                — List channels
POST   /api/v1/channels                — Create channel
GET    /api/v1/channels/{id}/meetings  — Meetings in channel
GET    /api/v1/teams
POST   /api/v1/teams
PUT    /api/v1/teams/{id}
```

### 11.7 Analytics
```
GET    /api/v1/analytics/productivity  — Personal metrics
GET    /api/v1/analytics/team/{id}     — Team metrics
GET    /api/v1/analytics/meetings      — Meeting load analysis
```

### 11.8 WebSocket
```
WS    /api/v1/meetings/{id}/live-updates    — Live transcript stream
WS    /api/v1/notes/{meeting_id}/edit       — Collaborative editing
WS    /api/v1/notifications                 — User notification stream
```

**WebSocket Auth:** JWT token passed as query param `?token=` during handshake. Connection rejected before `accept()` if token invalid.

### 11.9 Standard Error Response Schema

All API endpoints return errors in this consistent format:

```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with id 'abc-123' does not exist or you do not have access.",
    "status": 404,
    "request_id": "req_7f3a9c12",
    "timestamp": "2026-04-21T06:30:00Z"
  }
}
```

**Standard HTTP error codes used:**

| Code | Meaning | Example |
|---|---|---|
| 400 | Bad Request — validation failed | Missing required field |
| 401 | Unauthorized — token missing or expired | No Authorization header |
| 403 | Forbidden — valid token, insufficient permissions | Member accessing admin endpoint |
| 404 | Not Found — resource doesn't exist | Meeting ID not found |
| 409 | Conflict — duplicate resource | Email already registered |
| 422 | Unprocessable Entity — semantic validation failed | Due date in the past |
| 429 | Too Many Requests — rate limit exceeded | > 100 req/min |
| 500 | Internal Server Error — unexpected failure | Unhandled exception |
| 503 | Service Unavailable — dependency down | Azure Speech offline |

---

## 12. Security Requirements

| Requirement | Implementation |
|---|---|
| REST Auth | OAuth 2.0 + JWT (access 15min, refresh 7d) |
| WebSocket Auth | JWT token in handshake query param, validated before connection accept |
| Authorization | RBAC with org-scoped and team-scoped data isolation |
| Data at rest | AES-256 encryption (Azure managed keys) |
| Data in transit | TLS 1.3 |
| MCP access | Per-key API authentication with org-scoped isolation |
| Compliance | GDPR, SOC 2 Type II |
| Audit | All data access logged to `audit_logs` table |
| Rate limiting | 100 req/min (standard), 10 req/min (AI endpoints) |

---

## 13. Performance Requirements

| Metric | Target | Scope |
|---|---|---|
| API response time | < 200ms (p95) | Non-AI endpoints |
| AI endpoint response | < 5s (p95) | Agno Team + GPT-4 calls |
| Live transcription latency | < 3s end-to-end | Audio chunk → display |
| WebSocket message delivery | < 100ms | Real-time updates |
| System availability | 99.9% uptime | All services |
| Concurrent users | 10,000 | Platform-wide |
| Audio file processing | < 2x recording duration | Import feature |

> **Note:** AI endpoints are excluded from the 200ms SLA due to LLM inference times.

---

## 14. Implementation Roadmap

### Phase 1 — Foundation (Weeks 1–2)
- PostgreSQL schema deployment with all tables
- Authentication service (JWT + OAuth 2.0)
- Azure infrastructure provisioning (App Service, Blob, Redis, Kafka)
- CI/CD pipeline setup

### Phase 2 — Meeting Core (Weeks 3–5)
- Microsoft Teams bot (auto-join via Graph API)
- Audio Processing Service (Kafka pipeline)
- Transcription Service (Azure Speech SDK)
- Live transcript WebSocket push
- Meeting summary generation (Agno)
- Audio/Video import endpoint

### Phase 3 — AI Intelligence (Weeks 6–7)
- Action item extraction + auto task creation
- AI Chat with RAG (pgvector + GPT-4)
- Task Prioritization Agent
- MCP Server (search_meetings, get_summary, list_action_items)

### Phase 4 — Collaboration (Week 8)
- Channels feature
- Collaborative note editing (WebSocket OT)
- Slack integration (summary push)
- Salesforce / CRM integration (Sales Agent)

### Phase 5 — Specialized Agents & Polish (Weeks 9–10)
- Recruiting Agent
- Education Notetaker Agent
- SDR Agent (website widget)
- Analytics dashboards (personal + team)
- Security hardening + SOC 2 prep
- Production deployment + monitoring

---

## 15. Success Metrics & KPIs

### Business
- 80% of invited users active within 30 days
- 60% reduction in post-meeting follow-up time
- NPS score ≥ 70 within 90 days of launch

### Product
- ≥ 85% transcription accuracy (measured on English)
- Action item auto-creation acceptance rate ≥ 75%
- AI Chat query satisfaction rate ≥ 80%

### Technical
- 99.9% uptime
- Live transcription latency < 3 seconds
- Zero cross-org data leakage incidents

---

## 16. Out of Scope (v2.0 MVP)

- Zoom / Google Meet integration (post-MVP)
- Mobile native app (iOS / Android) — PWA only at launch
- On-premise / self-hosted deployment
- Real-time translation (transcription language detection only)
- Video recording playback with synchronized transcript (audio only at MVP)
- Zoom / Google Meet meeting bot (post-MVP)
- Mobile native app (iOS / Android) — PWA-first at launch

---

## 17. Frontend Component Architecture

```
┌──────────────────────────────────────────────────────┐
│                    App Layout                        │
│------------------------------------------------------│
│ Sidebar | Topbar | Main Content Area                 │
└───────────────┬──────────────────────────────────────┘
                │
 ┌──────────────┼────────────────────────────────────────┐
 │              │                │               │       │
 ▼              ▼                ▼               ▼       ▼
Dashboard   Meetings        AI Chat         Tasks    Settings
            (Channels)      (RAG Search)    (Board)

            │
            ▼
    ┌──────────────────────────────┐
    │      Meeting Workspace       │
    │------------------------------│
    │ Transcript | Summary | Tasks │
    └────────────┬─────────────────┘
                 │
 ┌───────────────┼────────────────────────┐
 │               │                        │
 ▼               ▼                        ▼
Transcript    Summary Panel          Action Items
Panel         (AI Generated)         Panel
(Live+Upload)
 │               │                        │
 ▼               ▼                        ▼
Speaker Labels  Key Points UI         Task Cards
Timestamps      Decisions UI          Assign User
Search Bar      Highlights            Status / Due Date
                Export (PDF/Word)     Link to Transcript
```

**Key UI components:**
- **Live Transcript Panel**: Streams segments via WebSocket. Speaker label chips, confidence indicator, click-to-seek.
- **Summary Panel**: Auto-populated post-meeting. Editable inline with collaborative presence dots.
- **Action Items Panel**: Card per task with assignee avatar, due date picker, status toggle, and link back to source transcript segment.
- **AI Chat Drawer**: Slide-in panel accessible from any page. Shows query history and source citations.
- **Channel View**: Kanban-style meeting list grouped by week, searchable across all transcripts.

---
## 18. User Journey Workflows

### 18.1 New User Onboarding Flow

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Sign Up /   │──▶│  Connect     │──▶│  Profile     │──▶│  Join or     │
│  SSO Login   │   │  Calendar    │   │  Setup       │   │  Create Team │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
  Create Account     Outlook/Exchange    Add Name,          Enable AI Bot
                     OAuth grant         Role, Timezone     for all meetings
                                                                │
                                                                ▼
                                                       ┌──────────────┐
                                                       │  Dashboard   │
                                                       │  Tutorial    │
                                                       └──────────────┘
```
### 18.2 Meeting Intelligence Flow (Core Daily Loop)
```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Calendar    │──▶│  AI Bot      │──▶│  Live        │──▶│  Post-       │
│  Invite      │   │  Auto-Joins  │   │  Transcript  │   │  Meeting AI  │
│  Detected    │   │  Meeting     │   │  Streams     │   │  Processing  │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                                                                │
                          ┌─────────────────────────────────────┤
                          │                                     │
                          ▼                                     ▼
                   ┌──────────────┐                   ┌──────────────┐
                   │  Summary +   │                   │  Action      │
                   │  Email sent  │                   │  Items →     │
                   │  to all      │                   │  Tasks Auto  │
                   │  attendees   │                   │  Created     │
                   └──────────────┘                   └──────────────┘
```

### 18.3 AI Chat Search Flow

```
 User Query → Embedding → pgvector Search → Top-K Chunks
                                                  │
                                                  ▼
                                      GPT-4 Response with
                                      Source Citations
                                      (Meeting + Timestamp)
```

---

## 19. Risk Mitigation

### 19.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Azure Speech accuracy < target (85%) | Medium | High | WhisperX fallback; human correction UI in transcript panel |
| Microsoft Graph API bot policy changes | Low | Critical | Monitor MS Bot Framework changelog; abstract bot layer for easy swap |
| GPT-4 latency spikes (> 5s p95) | Medium | Medium | Streaming responses for AI Chat; async processing for summaries |
| Kafka consumer lag under high meeting load | Medium | High | Per-partition consumer groups; auto-scaling consumer pods; DLQ monitoring |
| pgvector search degradation at scale | Low | Medium | Partition embeddings by org; HNSW index; evaluate Pinecone migration at 10M+ vectors |
| Teams bot ejected by host mid-meeting | High | Medium | Graceful exit handler; partial transcript saved; user notified |
| Cross-org data leakage via MCP | Low | Critical | Org-scoped DB queries enforced at service layer; MCP keys tied to org ID; audit every call |

### 19.2 Business Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| User adoption — participants uncomfortable with AI bot | High | High | Clear bot announcement message; easy opt-out per meeting; GDPR consent flow |
| Compliance in regulated industries (HIPAA, FINRA) | Medium | High | Data residency controls; encryption key management; legal review pre-launch |
| CRM API rate limits (Salesforce) | Medium | Low | Exponential backoff; batch sync instead of real-time for large orgs |
| Competitive pressure from Otter.ai, Fireflies | High | Medium | Differentiate on MCP openness, specialized agents, deep task integration |

### 19.3 Operational Risks

| Risk | Mitigation |
|---|---|
| Azure regional outage | Multi-region deployment for critical services; fallback to WhisperX |
| Blob storage costs at scale | Tiered storage (hot → cool → archive) based on meeting age; compressed audio |
| Database connection exhaustion | PgBouncer connection pooler; per-service connection limits |
