# Bug List

**Last Updated:** 2025-12-08  
**Current Cycle:** V4.1 Unified Container Model + UX Polish

---

## 1. Status Summary

| Phase | Status | Gate Date |
|-------|--------|-----------|
| Phase 1 (UX/Demo) | ✅ PASSED | 2025-12-07 |
| Phase 2 (Integration) | 🔄 READY TO START | — |
| Phase 3 (Production) | ⏳ PENDING | — |

---

## 2. Phase 1: UX/Demo (Completed)

**Status:** ✅ GATE PASSED (2025-12-07)

> **Manual Testing Complete (2025-12-07):** Copilot-assisted browser testing via MCP Playwright confirmed:
> - ✅ Source terminal behavior (no "Open" in menu, double-click doesn't navigate)
> - ✅ Context menu differentiation (Container vs Terminal menus)
> - ✅ Breadcrumb friendly names (shows titles, not raw IDs)
> - ✅ Voice button stability (no TypeError on click)
> - ✅ User/ACL stub context menu (FIXED - shows disabled "User System-Defined" item)
> - ✅ Double-click navigation for Agent/Tool nodes (FIXED - navigates correctly)

### Fixed Bugs (Phase 1)

#### ✅ FIXED: Gemini 3 Pro Thought Signature Missing Error
- **Error:** `ApiError: {"error":{"code":400,"message":"Function call is missing a thought_signature..."}}`
- **Fix:** Preserved `thoughtSignature` in `chatHistory`.
- **Fixed:** 2025-12-08

#### ✅ FIXED: Voice Connection Fails - SystemPromptBuilder TypeError
- **Error:** `TypeError: Cannot read properties of undefined (reading 'map')`
- **Fix:** Added defensive null checks in `system-prompt-builder.ts`.
- **Fixed:** 2025-12-06

#### ✅ FIXED: Source Nodes Allow "Open" Navigation
- **Error:** Source nodes showed "Open" in context menu.
- **Fix:** Removed `source` from `isContainerNode` check in `ContextMenu.tsx`.
- **Fixed:** 2025-12-06

#### ✅ FIXED: Context Menu Identical for All Node Types
- **Fix:** Implemented type-specific menu rendering (Session/Agent/Tool vs Source vs User).
- **Fixed:** 2025-12-06

#### ✅ FIXED: Backend Terminal Node Validation
- **Fix:** Added `TerminalNodeError` and service-level guards for USER/SOURCE containers.
- **Fixed:** 2025-12-06

---

## 3. Phase 2: Backend Integration (Current)

**Status:** ✅ V5 API INTEGRATION VERIFIED (2025-12-08)  
**Environment:** `VITE_MODE=development`, Backend with MockFirestore

### 3.1 Data Flow
```
LoginForm → POST /auth/login → JWT stored in localStorage
    ↓
Page reload → App initializes
    ↓
loadContainer(null) → GET /usersessions/{user_id}
    ↓
UserSessionService.get_or_create() → UserSession created in Firestore
    ↓
Zustand state populated from backend (localStorage = cache only)
```

### 3.2 Phase 2 Fixed Issues (2025-12-08)

#### ✅ FIXED: P2-API-405 - Missing Workspace Resource Endpoints
- **Error:** `405 Method Not Allowed` at `/usersessions/{user_id}/resources`
- **Fix:** Endpoint was already implemented, issue was user lookup in `get_user_context` querying wrong field.
- **Root Cause:** `get_user_context` queried by `email` but JWT `sub` contains `user_id`.
- **Fixed:** Changed query from `email == user_id` to `user_id == user_id` in `dependencies.py`.

#### ✅ FIXED: Tier Lookup Returns FREE Instead of ENTERPRISE
- **Error:** "Session limit reached. Tier 'Tier.FREE' allows max 5 active sessions"
- **Root Cause:** Mock data had `"tier": "ENTERPRISE"` (uppercase) but `Tier` enum uses lowercase values.
- **Fix:** Updated `.firestore_mock_data.json` to use `"tier": "enterprise"` (lowercase).

#### ✅ FIXED: Missing updateSession/deleteSession in API Client
- **Error:** Frontend had no functions to update or delete sessions.
- **Fix:** Added `updateSession()`, `deleteSession()`, `listSessions()` to `api-v4.ts`.
- **Also:** Fixed `deleteSession` in store to also delete the session entity (not just the ResourceLink).

#### ✅ FIXED: Direct URL Navigation Fails (link_id → resource_id mapping)
- **Error:** Navigating to `/workspace/session_xxx_yyy` returned 404 because backend expects `sess_xxx`.
- **Root Cause:** `workspaceResources` was empty during direct URL navigation, so mapping failed.
- **Fix:** `loadContainer` now pre-loads `workspaceResources` if empty before attempting navigation.

#### ✅ FIXED: 8+ Second Page Load Latency
- **Error:** Every page load/navigation took 8+ seconds.
- **Root Cause:** `sync_session_links()` was called on every `GET /resources` request, performing 3+ Firestore ACL queries.
- **Architecture Insight:** L0 sharing is visibility-only (no data dependency), so sync on login is sufficient.
- **Fix:** Moved `sync_session_links()` from `list_workspace_resources` to `get_usersession` (login endpoint).
- **Result:** Page load reduced from 8+ seconds to <500ms.

### 3.3 Phase 2 Open Issues

- [ ] **P2-AUTH-001:** Auth → UserSession flow not tested E2E

#### ✅ FIXED: P2-IMPORT-001 - Backend Fails to Start (ImportError)
- **Observed:** 2025-12-08 during CI/CD Phase 2 manual testing
- **Error:** `ImportError: cannot import name 'get_firestore' from 'src.api.dependencies'`
- **Root Cause:** v5_containers.py imported `get_firestore_client` from wrong module (`persistence.firestore_client` instead of `api.dependencies`)
- **Fix:** Changed import to `from src.api.dependencies import get_current_user, get_firestore_client`
- **Status:** ✅ FIXED - Backend starts successfully

#### ✅ FIXED: P2-REDIS-001 - Container Registry Redis AttributeError
- **Observed:** 2025-12-08
- **Error:** `AttributeError: 'RedisClient' object has no attribute 'zadd'`
- **Root Cause:** `_emit_event()` and `get_events_since()` called Redis sorted set methods directly without checking availability
- **Fix:** Added graceful degradation - in-memory SSE works without Redis, event catch-up disabled when Redis unavailable
- **Status:** ✅ FIXED - v5 API endpoints respond correctly
- **Console Evidence:**
  ```
  File "v5_containers.py", line 24, in <module>
      from src.api.dependencies import get_firestore, get_current_user
  ImportError: cannot import name 'get_firestore' from 'src.api.dependencies'
  ```

### 3.4 Phase 2 Remaining Work
1. **E2E Auth Test:** Verify Login → Backend Data Load loop.
2. **Agent Evaluation:** Implement batch runner for ChatAgent quality checks.
3. **Session Edit Modal:** Wire up to `updateSession` API.
4. **Delete Confirmation:** Add confirmation dialog before session deletion.

### 3.5 Phase 2 Manual Testing Notes (2025-12-08)

**Test Session Setup:**
- Task: "🎮 Start: Debug Session (All-in-One)"
- Environment: VITE_MODE=development, USE_FIRESTORE_MOCKS=true
- MCP Playwright connected on CDP 9222

**Observed Behavior:**
1. Frontend loads successfully at http://localhost:5173/workspace
2. Console shows proper initialization sequence:
   - `[BRIDGE] Initialized v1.0.0`
   - `🔄 loadContainer: Loading Root (UserSession)...`
   - `🔄 loadContainer: Fetching workspace for user_enterprise...`
3. Backend fails to start due to P2-IMPORT-001 (ImportError)
4. All API calls fail with `ERR_CONNECTION_REFUSED`:
   - `GET /api/v5/workspace` ← v5 workspace endpoint
   - `GET /definitions/agent` ← v4 definitions (still used)
   - `GET /definitions/tool`
   - `GET /definitions/source`

**API Surface Observed (Frontend Expects):**
| Endpoint | API Version | Purpose |
|----------|-------------|---------|
| `/api/v5/workspace` | v5 | Get UserSession + resources |
| `/api/v5/containers/{type}` | v5 | CRUD containers |
| `/api/v5/containers/{type}/{id}/resources` | v5 | Resource links |
| `/api/v5/events/containers` | v5 | SSE real-time |
| `/definitions/agent` | v4 | Agent definitions (still v4) |
| `/definitions/tool` | v4 | Tool definitions (still v4) |
| `/definitions/source` | v4 | Source definitions (still v4) |

**Test Blocked By:** P2-IMPORT-001

**Next Steps After Fix:**
1. Fix P2-IMPORT-001 (change `get_firestore` → `get_firestore_client` in v5_containers.py)
2. Restart backend
3. Run: `npx playwright test v5-api-integration --project=msedge`
4. Observe console and network for v5 API flow
5. Document any new issues found

**Test File Created:** `frontend/tests/e2e/v5-api-integration.spec.ts`
- Backend health checks
- Workspace load flow
- Session CRUD
- Navigation/containers
- SSE subscription
- Network request verification

---

## 4. Cycle 2: ChatAgent Tri-Agent (Planned)

**Prerequisite:** Complete Phase 2

### 4.1 Orchestration Triangle
- **VoiceAgent:** Primary UI, navigation, handoff coordinator.
- **CodingAgent:** Complex reasoning, code gen.
- **LocalAgent:** File ops, peer-user repos.

### 4.2 Planned Work
- **C2-001:** Wire AgentOrchestrator to ChatAgent.
- **C2-002:** Implement handoff protocol.
- **C2-003:** Switch to native Gemini Live audio.
- **C2-004:** Whisper WebGPU spike.
- **C2-005:** Automerge CRDT spike.

---

## 5. Deferred / Future

- **Menu Service:** Centralized UOM-aware menu builder (P2 Arch).
- **E2E Infra:** Fix navigation timeouts and selector mismatches.
- **Source ACL View:** Show UserStubs inside Source containers.
- **Portal Jump:** Click UserStub to navigate to shared session.
