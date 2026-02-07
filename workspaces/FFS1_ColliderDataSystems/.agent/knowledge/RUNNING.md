# Collider MVP - Running Guide

> Quick reference for running the complete Collider MVP stack.

## Prerequisites

| Component  | Version | Purpose             |
| ---------- | ------- | ------------------- |
| Node.js    | 18+     | Frontend, Extension |
| pnpm       | 8+      | Package manager     |
| Python     | 3.11+   | Backend servers     |
| PostgreSQL | 14+     | Database            |
| Chrome     | Latest  | Extension testing   |

---

## Database Setup

```powershell
# Start PostgreSQL (if not running)
# Ensure database exists
psql -U postgres -c "CREATE DATABASE collider;"
```

---

## Quick Start

Open 3 terminals and run:

### Terminal 1: Backend API Server
```powershell
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
**Verify:** `curl http://localhost:8000/health` → `{"status":"healthy"}`

### Terminal 2: Portal Frontend
```powershell
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\collider-frontend
pnpm exec nx dev portal
```
**Verify:** Open `http://localhost:3001` in browser

### Terminal 3: Chrome Extension
```powershell
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderMultiAgentsChromeExtension
npx plasmo dev
```
**Build Location:** `build/chrome-mv3-dev/`

---

## Loading the Extension

1. Navigate to `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select: `ColliderMultiAgentsChromeExtension/build/chrome-mv3-dev/`
5. Pin the extension to toolbar

### Opening Sidepanel
1. Click the Collider extension icon
2. Click "Open sidepanel" or right-click → "Open in sidepanel"

### Dev Mode Login
- Click **Login** button in sidepanel
- Automatically signs in as `superuser@test.com`
- No Firebase required in development

---

## Port Reference

| Service     | Port | URL                   |
| ----------- | ---- | --------------------- |
| Backend API | 8000 | http://localhost:8000 |
| Portal      | 3001 | http://localhost:3001 |
| Plasmo Dev  | 1012 | Internal HMR          |
| PostgreSQL  | 5432 | localhost:5432        |

---

## Development Debugging

### Backend Logs
Watch the uvicorn terminal for:
- Request logs
- SQL queries (if debug enabled)
- SSE connection events

### Extension DevTools
1. `chrome://extensions` → Find Collider
2. Click "service worker" link under "Inspect views"
3. Check Console for `[Collider]` logs

### Sidepanel DevTools
1. Open sidepanel
2. Right-click inside → "Inspect"
3. Check Console for `[Sidepanel]` logs

---

## Common Issues

### "Failed to fetch" in Portal
**Cause:** CORS misconfiguration
**Fix:** Ensure `.env` has:
```
COLLIDER_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
```

### Extension Service Worker "(Inactive)"
**Cause:** Heavy imports crashing SW
**Fix:** Already fixed with dynamic imports in `router.ts`

### Login Stuck on "Signing in..."
**Debug Steps:**
1. Open SW DevTools (chrome://extensions → service worker)
2. Check for errors on startup
3. Look for `[Collider] Message received: LOGIN`

### Database Connection Failed
**Cause:** PostgreSQL not running or wrong connection string
**Fix:** Check `.env`:
```
COLLIDER_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/collider
```

---

## Environment Files

### Backend `.env`
```env
COLLIDER_ENV=development
COLLIDER_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/collider
COLLIDER_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
FIREBASE_AUTH_ENABLED=false
```

### Portal `.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_API_KEY=your-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project
```

---

## Build Commands

### Production Build - Backend
```powershell
cd ColliderDataServer
pip install -e .
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Production Build - Portal
```powershell
cd collider-frontend
pnpm exec nx build portal
# Output in apps/portal/.next/
```

### Production Build - Extension
```powershell
cd ColliderMultiAgentsChromeExtension
npx plasmo build
# Output in build/chrome-mv3-prod/
```

---

## Verification Script

Quick health check:

```powershell
# Backend
curl -s http://localhost:8000/health | ConvertFrom-Json

# Auth endpoint (dev mode)
curl -s -X POST http://localhost:8000/api/v1/auth/verify `
  -H "Content-Type: application/json" `
  -d '{"token":"superuser@test.com"}' | ConvertFrom-Json

# Portal
curl -s http://localhost:3001 | Select-String "Collider"
```

---

## Architecture Reference

```
┌─────────────────────────────────────────────────────────────┐
│                          COLLIDER MVP                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Chrome Extension          Portal (Next.js)                │
│   ┌──────────────┐         ┌──────────────┐                 │
│   │  Sidepanel   │         │  localhost   │                 │
│   │  NodeBrowser │         │    :3001     │                 │
│   │  Login UI    │         │  Auth UI     │                 │
│   └──────┬───────┘         └──────┬───────┘                 │
│          │                        │                         │
│   ┌──────┴───────┐               │                         │
│   │Service Worker│───────────────┤                         │
│   │ LangGraph.js │               │                         │
│   └──────┬───────┘               │                         │
│          │                        │                         │
│          └────────────┬───────────┘                         │
│                       │                                     │
│                       ▼                                     │
│               ┌──────────────┐                              │
│               │   Backend    │                              │
│               │ localhost    │                              │
│               │   :8000      │                              │
│               │  FastAPI     │                              │
│               │  REST + SSE  │                              │
│               └──────┬───────┘                              │
│                      │                                      │
│                      ▼                                      │
│               ┌──────────────┐                              │
│               │  PostgreSQL  │                              │
│               │    :5432     │                              │
│               └──────────────┘                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```
