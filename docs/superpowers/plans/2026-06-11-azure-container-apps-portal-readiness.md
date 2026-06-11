# Azure Container Apps Portal Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `E:\Productivity_Tool_V1\productivity-platform` ready for Azure Portal-based Container Apps deployment.

**Architecture:** The platform deploys as separate container apps: Next.js frontend, FastAPI backend, and ChromaDB. Supabase, Azure Blob Storage, Azure Speech, and Azure OpenAI remain managed services configured through environment variables and secrets.

**Tech Stack:** Next.js, FastAPI, ChromaDB, Azure Container Apps, Azure Container Registry, Azure Files, Azure Blob Storage, Supabase.

---

### Task 1: Backend Container

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`

- [ ] Add a Python 3.12 container image that installs the backend package and runs `uvicorn app.main:app` on `${PORT:-8000}`.
- [ ] Exclude virtualenvs, caches, local env files, and test output from the Docker build context.

### Task 2: Frontend Container

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/.dockerignore`

- [ ] Add a Node 22 container image that installs dependencies, builds Next.js, and starts with `npm run start`.
- [ ] Accept `NEXT_PUBLIC_*` build arguments because the frontend needs the production API and Supabase public values during build.
- [ ] Exclude `node_modules`, `.next`, local env files, and local logs from the Docker build context.

### Task 3: Azure Portal Deployment Guide

**Files:**
- Create: `docs/azure-portal-deployment.md`

- [ ] Document the exact components to create in Azure Portal.
- [ ] Explain ChromaDB mapping from the current VM command to Azure Container Apps.
- [ ] List backend secrets, backend environment variables, frontend public variables, and Chroma settings.
- [ ] Keep the .NET Teams bot out of phase 1 and explain what remains offline until phase 2.

### Task 4: Image Build Workflow Template

**Files:**
- Create: `.github/workflows/build-container-images.yml`

- [ ] Add a GitHub Actions workflow that builds and pushes frontend/backend images to Azure Container Registry.
- [ ] Keep Azure-specific names configurable through GitHub repository variables and secrets.

### Verification

- [ ] Confirm all files are under `E:\Productivity_Tool_V1\productivity-platform`.
- [ ] Confirm no real secrets are written to the repo.
- [ ] Confirm the deployment guide uses Portal-first steps and only uses GitHub Actions for image building.
