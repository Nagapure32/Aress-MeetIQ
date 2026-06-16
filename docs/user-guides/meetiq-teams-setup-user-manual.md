# MeetIQ Teams Setup User Manual

This guide explains what an end user must do before MeetIQ can send approval cards and join Microsoft Teams meetings.

## Links You Will Need

Use the links provided by your MeetIQ administrator.

```text
MeetIQ web app: https://teamsmeetiq-frontend.nicesmoke-3151dcc8.eastus.azurecontainerapps.io/
MeetIQ Teams custom app ZIP: https://drive.google.com/file/d/1GtGB4Y4i_1LylTifg-ITqvFKhPVHW4dp/view?usp=sharing
```

## Why This Setup Is Required

At the moment, some Microsoft Teams permissions require users to install the MeetIQ Teams app as a custom app and send an initial message to the bot.

That first message lets Teams create and save a conversation reference for the user. MeetIQ needs that conversation reference so the bot can send approval cards in Teams before joining meetings.

Until this setup is complete, the user may not receive Teams approval cards.

## Before You Start

Make sure you have:

- Access to the MeetIQ web app.
- The MeetIQ Teams custom app ZIP file.
- Microsoft Teams desktop or web access.
- Permission to upload custom apps in Teams.
- A Microsoft calendar connected to the account you want MeetIQ to monitor.

If custom app upload is blocked, contact your Teams or Microsoft 365 administrator.

## Step 1: Open MeetIQ

1. Open the MeetIQ web app:

   ```text
   [ADD_FRONTEND_DEPLOYMENT_URL_HERE]
   ```

2. Sign in with your Microsoft work account.
3. If you are asked to connect your calendar, choose **Connect with Microsoft**.
4. Complete the Microsoft sign-in and consent flow.
5. After the connection is complete, MeetIQ will prepare your workspace and calendar assistant.

## Step 2: Upload the MeetIQ App in Teams

1. Download the MeetIQ Teams custom app ZIP:

   ```text
   [ADD_TEAMS_APP_ZIP_LINK_HERE]
   ```

2. Open Microsoft Teams.
3. Go to **Apps**.
4. Choose **Manage your apps** or **Upload a custom app**.
5. Select **Upload for me or my teams**.
6. Upload the MeetIQ ZIP file.
7. Confirm that the MeetIQ app appears in Teams.

If you do not see the upload option, your organization may have disabled custom app upload. Ask your Teams administrator to allow the MeetIQ app or upload it for your tenant.

## Step 3: Open the MeetIQ Bot Chat

1. In Teams, search for **MeetIQ**.
2. Open the MeetIQ bot chat.
3. Send this message:

   ```text
   Hi
   ```

4. Wait for the bot to respond or for the message to be delivered.

This step is important. It creates the Teams conversation reference that lets MeetIQ send approval cards to you later.

## Step 4: Enable Meeting Assistant Settings

1. Return to the MeetIQ web app.
2. Open **Settings**.
3. Go to **Meeting Assistant**.
4. Turn on **Enable auto-join**.
5. Keep **Require approval** turned on if you want MeetIQ to ask before joining a meeting.
6. Review timing settings:
   - **Approval lead**: how many minutes before the meeting MeetIQ should ask for approval.
   - **Look ahead**: how far ahead MeetIQ scans your calendar.
   - **Join early**: how many seconds before the start time MeetIQ may join.
   - **Max late join**: how long after the meeting starts MeetIQ may still join.
   - **Leave grace**: how long MeetIQ waits before leaving after the meeting ends.
7. Select **Save settings**.

## Step 5: Confirm Approval Cards Work

When MeetIQ detects an eligible Teams meeting, it should send an approval card in your Teams bot chat.

The approval card lets you choose:

- **Approve**: MeetIQ can join the meeting.
- **Reject**: MeetIQ will not join the meeting.

You can also review approval requests in the MeetIQ web app under **Approvals**.

## Normal User Flow

1. Install the MeetIQ Teams custom app.
2. Send `Hi` to the MeetIQ bot in Teams.
3. Connect Microsoft calendar in MeetIQ.
4. Enable the meeting assistant.
5. Receive approval cards before meetings.
6. Approve the meetings where MeetIQ should join.
7. Review transcripts, summaries, tasks, and insights after the meeting.

## Troubleshooting

### I cannot upload the custom Teams app

Your organization may not allow custom app uploads. Contact your Teams or Microsoft 365 administrator and share the MeetIQ Teams custom app ZIP link.

### I uploaded the app but do not receive approval cards

Open the MeetIQ bot chat in Teams and send:

```text
Hi
```

This is required so Teams creates the conversation reference for your account.

### I sent Hi but still do not receive cards

Check these items:

- You are signed in to Teams with the same Microsoft account used in MeetIQ.
- Your Microsoft calendar is connected in MeetIQ.
- **Enable auto-join** is turned on in Meeting Assistant settings.
- **Require approval** is turned on if you expect approval cards.
- The meeting is a Microsoft Teams meeting with a valid Teams join link.

### The approval card arrived too late

Ask your administrator or update your settings to increase **Approval lead** or **Look ahead**.

### The bot says nothing after I send Hi

The message may still create the required Teams conversation reference even if the response is delayed. If approval cards still do not appear for future meetings, contact your MeetIQ administrator.

### The approval request appears in the web app but not in Teams

This usually means the MeetIQ platform can see the approval request, but the Teams bot cannot message you. Reopen the MeetIQ bot chat in Teams and send `Hi` again.

## Current Limitation

Because of the current Teams permission setup, each user must upload or receive the MeetIQ Teams app and send `Hi` to the bot before Teams approval cards can be delivered reliably.

This is a one-time setup per user unless the Teams app is removed, permissions change, or the bot loses the saved conversation reference.
