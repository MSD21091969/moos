# 2026-02-05: MVP Debugging & Integration Fixes

**Author:** Copilot  
**Phase:** 3.5 - Integration Debugging  
**Status:** ✅ Completed

---

## Summary

This session resolved critical integration issues preventing the MVP from running end-to-end. The main issues were CORS configuration, service worker crashes due to heavy LangChain imports, and authentication flow debugging.

---

## Issues Resolved

### 1. CORS Configuration (Backend)

**Problem:** Portal at `http://localhost:3001` received `Failed to fetch` errors when calling the backend API at `http://localhost:8000`.

**Root Cause:** The `.env` file was overriding `config.py` CORS settings with an incomplete origin list.

**Solution:**
1. Updated `.env` to include `http://localhost:3001`:
   ```
   COLLIDER_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
   ```

2. Added dynamic chrome-extension support in `main.py`:
   ```python
   allow_origin_regex=r"^chrome-extension://.*$"
   ```

**Files Modified:**
- `ColliderDataServer/.env`
- `ColliderDataServer/src/main.py`

**Verification:**
```bash
curl -v http://localhost:8000/health -H "Origin: http://localhost:3001" 2>&1 | grep -i "access-control"
# Returns: access-control-allow-origin: http://localhost:3001
```

---

### 2. Service Worker Crash (Chrome Extension)

**Problem:** Extension sidepanel Login button showed "Signing in..." indefinitely. Service worker marked as "(Inactive)" in chrome://extensions.

**Root Cause:** Heavy LangChain imports at module load time crashed the service worker before it could process any messages.

**Problematic Code:**
```typescript
// router.ts - BEFORE (crashes SW)
import { runAgent, getApiKey } from "./runner"
```

**Solution:** Changed to dynamic imports so LangChain modules only load when needed:

```typescript
// router.ts - AFTER (works)
let runnerModule: typeof import("./runner") | null = null

async function getRunner() {
  if (!runnerModule) {
    try {
      runnerModule = await import("./runner")
    } catch (e) {
      console.error("[Router] Failed to load runner module:", e)
      return null
    }
  }
  return runnerModule
}

// In processMessage():
const runner = await getRunner()
if (runner) {
  return runner.runAgent(...)
}
```

**Files Modified:**
- `ColliderMultiAgentsChromeExtension/src/background/agents/router.ts`

---

### 3. Authentication Flow Debugging

**Problem:** Needed visibility into message flow between sidepanel and service worker.

**Solution:** Added comprehensive console logging:

**Files Modified:**
- `ColliderMultiAgentsChromeExtension/src/background/index.ts`
  - Added: `[Collider] SW startup`, `[Collider] Message received: ${type}`
  - Added: `[Collider LOGIN]` prefixed logs for auth flow

- `ColliderMultiAgentsChromeExtension/src/sidepanel/index.tsx`
  - Added: `[Sidepanel] handleLogin called`
  - Added: `[Sidepanel] Sending LOGIN message to service worker...`

---

## Technical Insights

### Service Worker Constraints

Chrome extension service workers have strict constraints compared to web workers:

1. **Module Loading:** Heavy synchronous imports can crash the SW before event listeners are registered
2. **Memory Limits:** LangChain's graph libraries consume significant memory
3. **Startup Time:** SW must start quickly to handle browser events

**Best Practice:** Use dynamic `import()` for heavy AI/ML libraries and only load them when executing AI operations (e.g., CHAT messages), not on every SW start (e.g., LOGIN messages).

### CORS Debugging

When debugging CORS issues:

1. Check both `config.py` defaults AND `.env` overrides
2. Use `curl -v` with `Origin` header to test directly
3. Look for `access-control-allow-origin` in response headers
4. For Chrome extensions, use `allow_origin_regex` since extension IDs change

---

## Final Working Configuration

### Backend (.env)
```env
COLLIDER_ENV=development
COLLIDER_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/collider
COLLIDER_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
FIREBASE_AUTH_ENABLED=false
```

### Backend (main.py CORS)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^chrome-extension://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Running the MVP

### Prerequisites
- PostgreSQL running on :5432 with database `collider`
- Node.js 18+ with pnpm
- Python 3.11+ with virtual environment

### Startup Commands

**Terminal 1 - Backend:**
```powershell
cd ColliderDataServer
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Portal:**
```powershell
cd collider-frontend
pnpm exec nx dev portal
# Runs on http://localhost:3001
```

**Terminal 3 - Extension Dev:**
```powershell
cd ColliderMultiAgentsChromeExtension
npx plasmo dev
# Build at chrome-mv3-dev/
```

### Loading the Extension
1. Go to `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `ColliderMultiAgentsChromeExtension/build/chrome-mv3-dev/`
5. Click the extension icon → Open sidepanel
6. Click "Login" (uses superuser@test.com in dev mode)

---

## Verification Checklist

| Component       | Test                                                 | Expected                                |
| --------------- | ---------------------------------------------------- | --------------------------------------- |
| Backend Health  | `curl http://localhost:8000/health`                  | `{"status":"healthy"}`                  |
| Backend Auth    | `POST /api/v1/auth/verify` with email                | Returns user object                     |
| Portal Load     | Visit `http://localhost:3001`                        | Shows "My Test App"                     |
| Portal Auth     | Click Sign In                                        | Signs in, shows email                   |
| Extension SW    | chrome://extensions → Inspect views → service worker | Console shows `[Collider] SW startup`   |
| Extension Login | Click Login in sidepanel                             | Shows "Logged in as superuser@test.com" |

---

## Files Changed Summary

**Backend:**
- `.env` - Added localhost:3001 to CORS origins
- `src/main.py` - Added `allow_origin_regex` for chrome-extension://

**Extension:**
- `src/background/index.ts` - Debug logging
- `src/background/agents/router.ts` - Dynamic imports for LangChain
- `src/sidepanel/index.tsx` - Debug logging

---

## Lessons Learned

1. **Environment variables override code** - Always check `.env` when config.py settings don't work
2. **Service workers are fragile** - Heavy imports must be lazy-loaded
3. **CORS regex for dynamic origins** - Use `allow_origin_regex` for chrome-extension:// since IDs vary
4. **Console logging is essential** - Add `[Component]` prefixed logs for debugging message flows

---

## Next Steps

With MVP working, focus areas are:

1. **UI Polish** - Loading states, error messages
2. **Chrome Extension Features** - PiP window testing, NodeBrowser navigation
3. **Production Deployment** - Firebase auth enabled, proper secrets management
