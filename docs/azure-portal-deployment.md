# Azure Portal Deployment Guide

This guide is for deploying the code in:

```text
E:\Productivity_Tool_V1\productivity-platform
```

Do not use `meetiq-platform-repo` for this deployment.

The first deployment phase includes:

```text
frontend/   Next.js web app
backend/    FastAPI API
ChromaDB    vector database server
Supabase    database and auth
Azure Blob  uploaded media storage
Azure Speech transcription
Azure OpenAI summaries, chat, and embeddings
```

The .NET Teams bot is phase 2. Keep it on the VM until the platform is working in Azure.

## 1. How The Deployed System Will Look

```text
Azure Resource Group
|
+-- Azure Container Registry
|   +-- meetiq-backend image
|   +-- meetiq-frontend image
|
+-- Azure Container Apps Environment
|   +-- meetiq-frontend  public, port 3000
|   +-- meetiq-backend   public first, port 8000
|   +-- meetiq-chroma    internal only, port 8000
|
+-- Azure Storage Account
|   +-- Blob container: meeting-transcripts
|   +-- File share: chroma-data
|
+-- Azure Speech
+-- Azure OpenAI
+-- Supabase project
```

## 2. What Azure Portal Can And Cannot Do

Azure Portal can create and configure:

```text
Resource groups
Container registries
Container apps
Secrets
Environment variables
Ingress
Storage accounts
Azure Files mounts
Logs
Revisions
```

Azure Portal does not build your local source folder directly. Build images using GitHub Actions from this repository, then deploy those images from the Portal.

## 3. Prepare The GitHub Repository

Push the contents of `E:\Productivity_Tool_V1\productivity-platform` to a GitHub repository.

In the GitHub repository, add these repository variables:

```text
ACR_NAME
ACR_LOGIN_SERVER
NEXT_PUBLIC_API_BASE_URL
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
NEXT_PUBLIC_APP_NAME
```

Add this GitHub repository secret:

```text
AZURE_CREDENTIALS
```

`AZURE_CREDENTIALS` is a JSON credential for GitHub Actions to push images to Azure Container Registry. If you do not want to create this yet, you can manually build/push images from Docker Desktop later. The Azure Portal deployment steps are the same after images exist in the registry.

## 4. Create Supabase

In Supabase:

1. Create a new project.
2. Save these values:

```text
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_JWT_SECRET
DATABASE_URL
```

3. Open the Supabase SQL Editor.
4. Run the SQL files from `backend/supabase` in order.

At minimum, run:

```text
001_initial_schema.sql
008_auth_bootstrap_policies.sql
010_uploaded_recordings.sql
```

If the other numbered files have not already been applied, run all numbered files in order.

## 5. Create Azure Resources From Portal

In Azure Portal:

1. Create a Resource Group, for example `rg-meetiq-prod`.
2. Create an Azure Container Registry, for example `meetiqacr`.
3. Create a Storage Account.
4. In the Storage Account, create a Blob container:

```text
meeting-transcripts
```

5. In the Storage Account, create an Azure Files share:

```text
chroma-data
```

6. Create an Azure Speech resource.
7. Create an Azure OpenAI resource.
8. Create or choose Azure OpenAI deployments:

```text
chat deployment
embedding deployment
```

Use the same embedding dimension configured in the backend. The current default is:

```text
AZURE_OPENAI_EMBEDDING_DIMENSIONS=1536
```

## 6. Build Images

Use GitHub Actions:

1. Go to your GitHub repository.
2. Open `Actions`.
3. Select `Build Container Images`.
4. Run the workflow.
5. Confirm these images appear in Azure Container Registry:

```text
meetiq-backend:latest
meetiq-frontend:latest
```

## 7. Create Container Apps Environment

In Azure Portal:

1. Search for `Container Apps Environment`.
2. Create a new environment.
3. Put it in the same Resource Group and Region as your other resources.

All three container apps should live in this same environment.

## 8. Deploy ChromaDB Container App

Your current VM command is:

```powershell
cd C:\productivity-platform\backend
.\.venv\Scripts\Activate.ps1
chroma run --host 0.0.0.0 --port 8001 --path C:\chroma-data
```

In Azure Container Apps, map that concept like this:

```text
Local VM port 8001              -> Azure container target port 8000
Local C:\chroma-data            -> Azure Files mounted at /chroma/chroma
Manual chroma run process       -> chromadb/chroma container image
Backend talks to localhost:8001 -> Backend talks to internal Chroma host:8000
```

Create a Container App:

```text
Name: meetiq-chroma
Image: chromadb/chroma
Ingress: enabled, internal only
Target port: 8000
Min replicas: 1
Max replicas: 1
```

Add Azure Files storage:

```text
File share: chroma-data
Mount path: /chroma/chroma
```

After creation, open the Chroma Container App `Overview` page and copy the application URL/FQDN. For backend config, use the host name only, without `https://`.

## 9. Deploy Backend Container App

Create a Container App:

```text
Name: meetiq-backend
Image: <your-acr-login-server>/meetiq-backend:latest
Ingress: external for first deployment
Target port: 8000
Min replicas: 1
Max replicas: 3
```

Use external ingress for the first deployment because it is easier to test. Later, you can decide whether to put the backend behind a private network or keep it public with authentication.

### Backend Secrets

In the backend Container App, add these as secrets:

```text
backend-secret-key
bot-internal-api-key
supabase-service-role-key
supabase-jwt-secret
database-url
microsoft-client-secret
azure-speech-key
azure-storage-connection-string
azure-openai-api-key
task-smtp-password
```

Only add `task-smtp-password` if email is enabled.

### Backend Environment Variables

Set these environment variables:

```text
APP_ENV=production
APP_NAME=MeetIQ
API_BASE_URL=https://BACKEND_URL_FROM_PORTAL
FRONTEND_BASE_URL=https://FRONTEND_URL_FROM_PORTAL
AUTH_REQUIRED=true
ALLOW_DEV_USER_FALLBACK=false
CORS_ALLOWED_ORIGINS=https://FRONTEND_URL_FROM_PORTAL
ENABLE_MICROSOFT_ONBOARDING=true
ENABLE_AI_SUMMARIES=true
ENABLE_AI_CHAT=true
ENABLE_BOT_INTERNAL_APIS=true
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
MICROSOFT_TENANT_ID=YOUR_TENANT_ID
MICROSOFT_CLIENT_ID=YOUR_CLIENT_ID
MICROSOFT_REDIRECT_URI=https://BACKEND_URL_FROM_PORTAL/api/v1/auth/microsoft/callback
TEAMS_BOT_BASE_URL=https://YOUR_VM_OR_BOT_URL
VECTOR_STORE_PROVIDER=chroma
CHROMA_HOST=MEETIQ_CHROMA_INTERNAL_HOST
CHROMA_PORT=8000
CHROMA_SSL=false
CHROMA_COLLECTION=meeting-transcript-chunks
AZURE_SPEECH_REGION=YOUR_SPEECH_REGION
AZURE_SPEECH_API_VERSION=2025-10-15
AZURE_SPEECH_DEFAULT_LANGUAGE=en-IN
AZURE_STORAGE_CONNECTION_STRING=secretref:azure-storage-connection-string
AZURE_MEDIA_CONTAINER=meeting-transcripts
AZURE_MEDIA_PREFIX=uploaded-media
AZURE_OPENAI_ENDPOINT=https://YOUR_AZURE_OPENAI_RESOURCE.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT=YOUR_CHAT_DEPLOYMENT
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=YOUR_EMBEDDING_DEPLOYMENT
AZURE_OPENAI_EMBEDDING_DIMENSIONS=1536
BACKEND_SECRET_KEY=secretref:backend-secret-key
BOT_INTERNAL_API_KEY=secretref:bot-internal-api-key
SUPABASE_SERVICE_ROLE_KEY=secretref:supabase-service-role-key
SUPABASE_JWT_SECRET=secretref:supabase-jwt-secret
DATABASE_URL=secretref:database-url
MICROSOFT_CLIENT_SECRET=secretref:microsoft-client-secret
AZURE_SPEECH_KEY=secretref:azure-speech-key
AZURE_OPENAI_API_KEY=secretref:azure-openai-api-key
```

If you enable email later, also add:

```text
TASK_EMAIL_ENABLED=true
TASK_SMTP_HOST=smtp.gmail.com
TASK_SMTP_PORT=587
TASK_SMTP_USERNAME=YOUR_SMTP_USERNAME
TASK_SMTP_PASSWORD=secretref:task-smtp-password
TASK_SMTP_FROM_ADDRESS=no-reply@example.com
TASK_SMTP_FROM_NAME=MeetIQ
TASK_SMTP_ENABLE_TLS=true
```

## 10. Test Backend

After backend deployment, open:

```text
https://BACKEND_URL_FROM_PORTAL/health
```

Expected response:

```json
{"status":"ok","service":"MeetIQ"}
```

## 11. Deploy Frontend Container App

Before building the frontend image, set the GitHub repository variable:

```text
NEXT_PUBLIC_API_BASE_URL=https://BACKEND_URL_FROM_PORTAL
```

Run the GitHub Actions workflow again so the frontend image is rebuilt with the real backend URL.

Create a Container App:

```text
Name: meetiq-frontend
Image: <your-acr-login-server>/meetiq-frontend:latest
Ingress: external
Target port: 3000
Min replicas: 1
Max replicas: 3
```

Frontend public variables are build-time values:

```text
NEXT_PUBLIC_API_BASE_URL=https://BACKEND_URL_FROM_PORTAL
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
NEXT_PUBLIC_APP_NAME=MeetIQ
```

## 12. Update Backend After Frontend URL Exists

After frontend deployment, copy the frontend URL from Azure Portal.

Update backend environment variables:

```text
FRONTEND_BASE_URL=https://FRONTEND_URL_FROM_PORTAL
CORS_ALLOWED_ORIGINS=https://FRONTEND_URL_FROM_PORTAL
```

Create a new backend revision or restart the latest revision.

## 13. Update Supabase Auth Settings

In Supabase:

1. Go to Authentication settings.
2. Set the site URL:

```text
https://FRONTEND_URL_FROM_PORTAL
```

3. Add redirect URLs:

```text
https://FRONTEND_URL_FROM_PORTAL
https://FRONTEND_URL_FROM_PORTAL/login
```

## 14. Update Microsoft App Registration

In Azure Portal, open Microsoft Entra ID app registration.

Add redirect URI:

```text
https://BACKEND_URL_FROM_PORTAL/api/v1/auth/microsoft/callback
```

Confirm these values match backend environment variables:

```text
MICROSOFT_TENANT_ID
MICROSOFT_CLIENT_ID
MICROSOFT_CLIENT_SECRET
MICROSOFT_REDIRECT_URI
```

## 15. Phase 1 Test Checklist

Test in this order:

```text
Backend /health returns ok
Frontend opens
Login page opens
Supabase login works
Dashboard loads
Upload recording works
Uploaded media appears in Azure Blob Storage
Azure Speech creates transcript text
Meeting summary generation works
Meeting chat indexing works
Meeting chat answers from transcript
```

Expected bot-related limitation in phase 1:

```text
Bot health may show offline
Manual join may fail
Auto-join meetings will not work until the .NET bot is deployed
```

## 16. Phase 2 Bot Connection Later

When you are ready to deploy or connect the .NET Teams bot:

```text
Use the same BOT_INTERNAL_API_KEY in backend and bot
Set bot platform API URL to https://BACKEND_URL_FROM_PORTAL
Set backend TEAMS_BOT_BASE_URL to the bot's public HTTPS URL
Verify bot heartbeat reaches backend
Verify backend bot health page sees the bot
```

Keep the bot on the VM until phase 1 is stable.
