# MeetIQ Product User Guide

MeetIQ is a meeting intelligence platform for Microsoft Teams users. It helps teams approve bot attendance, capture meeting transcripts, review meeting details, ask AI questions about meeting content, track tasks, and understand productivity trends.

## Access MeetIQ

Use the deployment link provided by your administrator.

```text
MeetIQ web app: https://teamsmeetiq-frontend.nicesmoke-3151dcc8.eastus.azurecontainerapps.io/
```

Sign in with your Microsoft work account. If this is your first time, MeetIQ may ask you to connect your Microsoft calendar.

## What MeetIQ Does

MeetIQ works with your Microsoft calendar and Teams meetings. When enabled, it can detect upcoming Teams meetings, ask for approval, join approved meetings, capture transcript information, and make the meeting content available inside the web app.

The Teams approval card setup currently requires the MeetIQ Teams custom app. See:

```text
docs/user-guides/meetiq-teams-setup-user-manual.md
```

## Main Areas of the App

### Dashboard

The dashboard is the starting point after sign-in. Use it to get a quick view of your meeting activity, pending work, and recent workspace status.

### Meetings

The Meetings page shows meetings detected or processed by MeetIQ. Use it to:

- Review upcoming and past meetings.
- Open a meeting detail page.
- Check meeting status, bot status, and approval status.
- Access transcript, summary, tasks, and AI actions connected to a meeting.

### Meeting Details

The meeting detail page gives you a focused view of one meeting. Depending on the available meeting data, you can review:

- Meeting subject and time.
- Bot and processing status.
- Transcript lines.
- Meeting summary.
- Action items or tasks created from the meeting.
- AI-powered meeting actions.

### Approvals

The Approvals page lists meeting requests that need a decision. Use it to:

- See pending approval requests.
- Approve MeetIQ joining a meeting.
- Reject MeetIQ joining a meeting.
- Review closed approvals that were approved, rejected, or expired.

Approval requests may also appear as cards in Microsoft Teams after the Teams setup is complete.

### Transcripts

The Transcripts area is where meeting transcript content becomes available after MeetIQ receives it from the bot. Use transcripts to review what was said, search for context, and support summaries or AI chat answers.

### AI Chat

AI Chat lets you ask questions about your meeting knowledge. Use it to find decisions, action items, discussion points, or context from past meeting content.

Example questions:

```text
What did we decide about the launch plan?
Who owns the follow-up tasks from the client meeting?
Summarize the last discussion about pricing.
```

### Tasks

The Tasks page helps track work that comes from meetings. Use it to:

- Review tasks.
- Create new tasks.
- Update task status.
- Track ownership and follow-up work.

### Insights

The Insights page shows analytics for meetings, tasks, approvals, and bot activity. Use it to understand workload, meeting patterns, and productivity signals.

### Settings

Settings includes Meeting Assistant controls. Use it to configure:

- Whether MeetIQ can auto-join eligible meetings.
- Whether MeetIQ must ask for approval before joining.
- How early MeetIQ asks for approval.
- How far ahead MeetIQ scans the calendar.
- Join timing and leave timing behavior.

## First-Time Setup Checklist

Complete these steps before expecting MeetIQ to join meetings or send Teams approval cards.

1. Open the MeetIQ web app:

   ```text
   [ADD_FRONTEND_DEPLOYMENT_URL_HERE]
   ```

2. Sign in with your Microsoft work account.
3. Connect your Microsoft calendar when prompted.
4. Download the MeetIQ Teams custom app ZIP:

   ```text
   [ADD_TEAMS_APP_ZIP_LINK_HERE]
   ```

5. Upload the ZIP as a custom app in Microsoft Teams.
6. Open the MeetIQ bot chat in Teams.
7. Send:

   ```text
   Hi
   ```

8. In MeetIQ, open **Settings > Meeting Assistant**.
9. Turn on **Enable auto-join**.
10. Turn on **Require approval** if you want approval before the bot joins.
11. Save settings.

## Daily Workflow

### Before a Meeting

MeetIQ scans connected calendars for eligible Teams meetings. If approval is required, MeetIQ sends an approval request before the meeting based on your Meeting Assistant settings.

You can approve or reject from:

- The Microsoft Teams approval card.
- The MeetIQ web app Approvals page.

### During a Meeting

When approved, the MeetIQ bot may join the meeting and capture meeting information. Participants should be aware that an AI meeting assistant is present.

### After a Meeting

After the meeting, return to MeetIQ to review:

- Meeting status.
- Transcript.
- Summary.
- Tasks and action items.
- AI chat answers based on meeting content.
- Analytics and insights.

## Best Practices

- Use the same Microsoft account in Teams and MeetIQ.
- Send `Hi` to the MeetIQ bot after installing the Teams app.
- Keep approval enabled if users should control whether the bot joins.
- Review approvals before meetings start.
- Check the Meetings page after important meetings to confirm transcript and summary availability.
- Keep task ownership clear when creating or updating meeting tasks.

## Current Limitations

- Each user must install or receive the MeetIQ Teams app before Teams approval cards can be delivered.
- Each user must send `Hi` to the MeetIQ bot so Teams creates the conversation reference.
- If custom app upload is disabled, a Teams administrator must help deploy or approve the app.
- Approval cards depend on the Teams bot being online and able to message the user.
- Google Calendar and non-Teams meeting platforms may be limited or unavailable depending on the current deployment.

## Getting Help

Contact your MeetIQ administrator if:

- You cannot upload the Teams custom app.
- You do not receive approval cards.
- Your calendar does not connect.
- Meetings are missing from MeetIQ.
- The bot does not join after approval.
- Transcripts or summaries do not appear after a meeting.
