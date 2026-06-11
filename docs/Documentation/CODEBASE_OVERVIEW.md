# TeamsMediaBot Codebase Overview

This project is an ASP.NET Core 8 Teams media bot. It scans a configured user's calendar for upcoming Teams meetings, requests approval before joining, joins approved meetings through Microsoft Graph communications APIs, receives meeting audio, transcribes audio with Azure Speech, stores finalized transcript data, and posts transcript lines back into Teams.

## High-Level Flow

```text
Application starts
-> Program.cs registers bot, Graph, calendar, approval, meeting, audio, and transcript services
-> CalendarAutoJoinService runs in the background
-> CalendarMeetingService scans CalendarAutoJoin:CalendarUserId
-> If a Teams meeting is found:
     -> create or reuse a MeetingApprovalRequest
     -> try to send a Teams approval card
     -> optionally send email approval
     -> log web approval links
     -> wait for Approved status
-> MeetingJoinService joins the approved Teams meeting
-> CallHandler receives meeting audio
-> Azure Speech recognizes transcript text
-> TranscriptBlobStorage stores finalized transcript data
-> TeamsTranscriptPoster posts transcript lines back to Teams
```

## Main Configuration

The main settings are in `appsettings.json`. The current project file contains real-looking secrets. For production or shared VM use, move these values to environment variables, user-secrets, Azure Key Vault, or another secure store.

Important sections:

```json
"AzureAd": {
  "TenantId": "...",
  "ClientId": "...",
  "ClientSecret": "..."
}
```

Used by `GraphAccessTokenProvider` and Bot Framework auth fallback settings in `Program.cs`.

```json
"Bot": {
  "CallbackUri": "https://shweta-teams-bot.eastus.cloudapp.azure.com/api/calls",
  "Fqdn": "shweta-teams-bot.eastus.cloudapp.azure.com",
  "MediaPublicIp": "...",
  "MediaPublicPort": "8445",
  "CertificateThumbprint": "..."
}
```

Used by Graph call callbacks, media setup, and approval base URL fallback.

```json
"CalendarAutoJoin": {
  "Enabled": true,
  "RequireApproval": true,
  "CalendarUserId": "shweta.nagpure@aress.com",
  "PollIntervalSeconds": 60,
  "LookAheadMinutes": 15,
  "ApprovalLeadMinutes": 2,
  "JoinEarlySeconds": 0,
  "MaxLateJoinMinutes": 10,
  "LeaveGraceMinutes": 2,
  "UseServiceHostedMedia": false
}
```

Controls background calendar scanning and automatic meeting join behavior.

## Approval System

Approval is controlled by:

```json
"CalendarAutoJoin": {
  "RequireApproval": true,
  "Approval": {
    "SendTeams": true,
    "LogApprovalLinks": true,
    "AllowLatestConversationReference": true,
    "BaseUrl": "",
    "Email": {
      "Enabled": true,
      "Provider": "Smtp",
      "Recipient": "shweta.nagpure@aress.com"
    },
    "TeamsInstallation": {
      "Enabled": true,
      "TeamsAppCatalogId": "",
      "TeamsAppExternalId": "817db4df-9775-4266-b386-de505d80d1ba"
    }
  }
}
```

`MeetingApprovalService` creates or reuses a pending approval request for a calendar event. Approval statuses are:

```text
Pending
Approved
Rejected
Expired
```

The first valid decision wins. A Teams, email, or web decision all update the same `MeetingApprovalStore` record.

## Teams Approval Card - Option 1

The currently working Teams approval path is option 1: the user first messages the bot, usually with `Hi`, and the bot saves the Teams conversation reference. Later, the calendar approval flow uses that reference to proactively send an Adaptive Card.

Implemented in:

```text
Bot/TeamsTranscriptBot.cs
Bot/ConversationReferenceStore.cs
Bot/MeetingApprovalService.cs
```

Flow:

```text
User sends "Hi" to bot in Teams
-> Teams posts activity to POST /api/messages
-> TeamsTranscriptBot saves the conversation reference
-> TeamsTranscriptBot calls TeamsInfo.GetMemberAsync
-> ConversationReferenceStore stores the same reference by Teams id, AAD id, UPN, email, and display name
-> CalendarAutoJoinService finds an eligible Teams meeting
-> MeetingApprovalService finds the stored reference
-> MeetingApprovalService sends an Adaptive Card with Approve and Reject buttons
-> TeamsTranscriptBot receives Action.Submit
-> MeetingApprovalService.RecordDecision records Approved or Rejected
```

`AllowLatestConversationReference` is enabled so the approval card can fall back to the most recent saved Teams conversation reference when exact identity matching is not available.

Current limitation: conversation references are stored in memory. After a bot restart, the user must send `Hi` again before option 1 can send approval cards.

## Teams Conversation Reference Store

Implemented in:

```text
Bot/ConversationReferenceStore.cs
```

The store keeps:

```text
latest conversation reference
conversation references by user key
```

User keys include:

```text
activity.From.Id
activity.From.AadObjectId
activity.From.Name
activity.MembersAdded ids/names
activity.MembersRemoved ids/names
TeamsChannelAccount.Id
TeamsChannelAccount.AadObjectId
TeamsChannelAccount.UserPrincipalName
TeamsChannelAccount.Email
TeamsChannelAccount.Name
```

This broader key set was added because Teams activities often use internal Teams ids, while approval lookup starts from `CalendarAutoJoin:CalendarUserId`.

## Teams App Installation Fallback

Implemented in:

```text
Bot/TeamsAppInstallationService.cs
Bot/MeetingApprovalService.cs
```

If no conversation reference is available and `TeamsInstallation:Enabled` is true, the app tries to install the Teams app for the calendar user through Microsoft Graph.

Endpoints used:

```text
GET  /appCatalogs/teamsApps
GET  /users/{user}/teamwork/installedApps
POST /users/{user}/teamwork/installedApps
```

After installation, `MeetingApprovalService` waits and retries for a conversation reference:

```text
CalendarAutoJoin:Approval:TeamsReferenceRetryCount default 6
CalendarAutoJoin:Approval:TeamsReferenceRetryDelaySeconds default 5
```

This is a fallback. The currently verified working path is still option 1: send `Hi` first, then use that saved reference.

## Email and Web Approval

Email approval is implemented in:

```text
Bot/EmailApprovalSender.cs
```

The current config uses SMTP:

```json
"Email": {
  "Enabled": true,
  "Provider": "Smtp",
  "Recipient": "shweta.nagpure@aress.com",
  "Smtp": {
    "Host": "smtp.gmail.com",
    "Port": 587,
    "EnableSsl": true
  }
}
```

Web approval endpoints are implemented in:

```text
Controllers/ApprovalsController.cs
```

Endpoints:

```text
GET  /api/approvals
GET  /api/approvals/{approvalId}?token=...
GET  /api/approvals/{approvalId}/approve?token=...
GET  /api/approvals/{approvalId}/reject?token=...
POST /api/approvals/{approvalId}/decision?token=...
```

The same token-protected approval record is used by Teams, email, and web approval.

## Calendar Auto-Join

Implemented in:

```text
Bot/CalendarAutoJoinService.cs
Bot/CalendarMeetingService.cs
Bot/CalendarAutoJoinState.cs
```

`CalendarAutoJoinService` scans the configured calendar every `PollIntervalSeconds`. `CalendarMeetingService` calls Microsoft Graph calendarView:

```text
GET /users/{CalendarUserId}/calendarView
```

It detects Teams meetings from:

```text
onlineMeeting.joinUrl
bodyPreview
body.content
```

When approval is required, `CalendarAutoJoinService` starts approval at `ApprovalLeadMinutes` before the meeting. It joins only after the approval status becomes `Approved`. Rejected or expired meetings are marked handled and skipped.

## Meeting Join

Implemented in:

```text
Bot/MeetingJoinService.cs
Bot/MeetingJoinModels.cs
Controllers/JoinController.cs
```

Manual join endpoints:

```text
POST /api/join
POST /api/calls/join
```

Leave endpoint:

```text
DELETE /api/join
```

The service builds the Graph call payload and calls:

```text
POST https://graph.microsoft.com/v1.0/communications/calls
```

`MeetingSessionManager` prevents concurrent meeting sessions and cleans up media/call state on leave or call termination.

## Callbacks and Meeting State

Implemented in:

```text
Controllers/CallsController.cs
Bot/MeetingSessionManager.cs
Bot/ParticipantAudioSourceMapper.cs
```

Graph sends call lifecycle callbacks to:

```text
POST /api/calls
```

The callback handler processes call state, termination, and participant updates. `ParticipantAudioSourceMapper` maps media source ids to participant display names when possible.

## Audio and Multilingual Transcription

Implemented in:

```text
Bot/CallHandler.cs
Bot/AudioHandler.cs
Bot/ParticipantAudioSourceMapper.cs
```

The main meeting transcription path is `CallHandler`. `AudioHandler` is an older/secondary transcription path and was updated for consistency.

Previous issue: both recognizer paths hard-coded:

```csharp
speechConfig.SpeechRecognitionLanguage = "en-US";
```

That made English work well but caused Hindi, Marathi, and other non-English speech to be recognized poorly.

Current behavior:

```text
CallHandler uses Azure Speech auto language detection
AudioHandler also supports auto language detection
LanguageIdMode defaults to Continuous
Detected language is logged with each finalized transcript line
```

Current speech config:

```json
"SpeechService": {
  "Region": "eastus",
  "RecognitionLanguage": "en-IN",
  "AutoDetectEnabled": true,
  "LanguageIdMode": "Continuous",
  "AutoDetectLanguages": [
    "en-IN",
    "en-US",
    "hi-IN",
    "mr-IN"
  ]
}
```

If the meeting needs another language, add its Azure Speech locale to `AutoDetectLanguages`. Keep the list focused; a smaller list generally gives better detection than a very large list.

Audio flow:

```text
AudioMediaReceived
-> copy PCM 16 kHz 16-bit mono audio bytes
-> CallHandler.PushAudio
-> one recognizer per speaker source id
-> Azure Speech recognizes text and detects language
-> finalized transcript is recorded
-> transcript line is posted to Teams
```

## Transcript Posting and Storage

Transcript posting is implemented in:

```text
Bot/TeamsTranscriptPoster.cs
```

It posts finalized transcript lines through Bot Framework using the latest saved conversation reference. If no reference exists, it logs a warning and skips the Teams post.

Transcript storage is implemented in:

```text
Bot/IMeetingTranscriptStore.cs
Bot/TranscriptBlobStorage.cs
```

Current storage config:

```json
"TranscriptStorage": {
  "ConnectionString": "...",
  "ContainerName": "meeting-transcripts",
  "Prefix": "transcripts"
}
```

## Teams Bot Message Endpoint

Implemented in:

```text
Controllers/BotMessagesController.cs
Bot/TeamsTranscriptBot.cs
```

Teams sends bot activities to:

```text
POST /api/messages
```

For normal messages, the bot stores the conversation reference and replies:

```text
Transcript posting is connected. I will send finalized transcript lines here.
```

For approval card button submits, the bot records the decision and replies with the result message.

## Azure and Teams Requirements

The app registration needs valid:

```text
Tenant ID
Client ID
Client secret value
```

Required Microsoft Graph permissions depend on enabled features:

```text
Calendars.Read or equivalent calendar permission
Calls.JoinGroupCall.All
Calls.AccessMedia.All
OnlineMeetings.Read.All if required by tenant policy
TeamsAppInstallation.ReadWriteSelfForUser.All
TeamsAppInstallation.ReadForUser.All
AppCatalog.Read.All
Mail.Send if Graph mail is used
```

Admin consent is required for application permissions.

The Azure Bot resource messaging endpoint must be:

```text
https://shweta-teams-bot.eastus.cloudapp.azure.com/api/messages
```

The Teams app manifest bot id must match the app registration client id:

```json
"bots": [
  {
    "botId": "817db4df-9775-4266-b386-de505d80d1ba",
    "scopes": [ "personal", "team", "groupchat" ]
  }
]
```

For option 1 approval cards, `personal` scope and a prior user message to the bot are important.

## Running on the VM

Example:

```powershell
Get-ChildItem Env:ASPNETCORE_Kestrel__Certificates__Default__* | Remove-Item

$env:ASPNETCORE_Kestrel__Certificates__Default__Subject="shweta-teams-bot.eastus.cloudapp.azure.com"
$env:ASPNETCORE_Kestrel__Certificates__Default__Store="My"
$env:ASPNETCORE_Kestrel__Certificates__Default__Location="LocalMachine"
$env:ASPNETCORE_Kestrel__Certificates__Default__AllowInvalid="false"

dotnet run --urls "https://0.0.0.0:443;http://0.0.0.0:5121"
```

The VM path used during testing was:

```text
C:\TeamsMediaBot
```

The local workspace path is:

```text
C:\Users\shweta.nagapure\TeamsMediaBot\TeamsMediaBot
```

When changing code locally, copy the changed files to the VM run directory before testing.

## Current Limitations

Approval requests are stored in memory. If the app restarts, pending approval records are lost.

Conversation references are stored in memory. If the app restarts, send `Hi` to the bot again before expecting option 1 approval cards or transcript posts.

The Teams app installation fallback is configured, but option 1 is the verified working flow. Sending cards without a prior user message depends on Teams app installation, Graph permissions, and Teams delivering a usable conversation update.

Speech auto-detect is configured for English India, English US, Hindi India, and Marathi India. Other languages must be added explicitly.

Mixed-language speech inside the same sentence can still be imperfect. Azure Speech performs best when candidate languages are known and the list is not too broad.

Secrets are currently present in `appsettings.json`; rotate and move them to secure configuration.

## Recently Updated Files

Approval card and option 1 conversation reference work:

```text
Bot/ConversationReferenceStore.cs
Bot/TeamsTranscriptBot.cs
Bot/MeetingApprovalService.cs
appsettings.json
```

Multilingual transcription:

```text
Bot/CallHandler.cs
Bot/AudioHandler.cs
appsettings.json
```

The attempted JSON persistence change for conversation references was reverted. The current store is intentionally in memory.
