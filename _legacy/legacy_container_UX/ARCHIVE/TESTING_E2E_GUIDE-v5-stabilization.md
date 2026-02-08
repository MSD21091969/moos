# E2E Testing Guide & Strategy

**Last Updated:** 2025-12-09
**Scope:** End-to-End Testing, Integration Strategy, and Load Testing for Universal Object Model (UOM) v5.

---

## 1. Overview

This guide consolidates the testing strategy for the Data Collider. It covers the validation of the Universal Object Model (UOM) v5, ensuring alignment between the ReactFlow frontend and the FastAPI/Firestore backend.

**Key Objectives:**
1.  **UX-Backend Alignment:** Verify menu options match actual capabilities (Tier, Container Type, Depth).
2.  **Data Persistence:** Ensure the chain of Instance -> ResourceLink -> Definition is preserved in Firestore.
3.  **Container Models:** Validate "Create-New" (Sessions) vs "Add-Existing" (Agents/Tools) paradigms.
4.  **Depth & Rules:** Enforce nesting rules (L1-L4) and terminal node behavior (Source).

---

## 2. Test Strategy

### Phase 1: UX Baseline (Canvas Level)
*Focus: Menu correctness, visual feedback, and basic navigation.*
- **Root Menu:** Only "Create Session" allowed.
- **L1 Session Menu:** "Open", "Edit", "Duplicate", "Delete".
- **Context Menus:** Must reflect current depth and container type.

### Phase 2: Integration (Real Firestore)
*Focus: Data persistence, API interaction, and state management.*
- **Real Backend:** Tests run against local FastAPI + Real Firestore (no mocks).
- **Auth Injection:** Requires valid Enterprise token injected via `scripts/auth/inject-auth.js`.
- **CRUD:** Create, Read, Update, Delete operations for all container types.

### Phase 3: Load Testing
*Focus: Performance and stability under load.*
- **Target:** 50+ concurrent sessions.
- **Validation:** Batch creation API, Firestore indexing, and frontend rendering performance.

---

## 3. Current Status (Dec 2025)

| Feature | Status | Notes |
| :--- | :--- | :--- |
| **Menu System** | ✅ Excellent | Correctly reflects Tier/Depth/Type rules. |
| **Session Creation** | ✅ Working | L1 & L2 sessions persist correctly. |
| **Data Persistence** | 🟡 Partial | Creation works, but Edits (P2-EDIT-001) are lossy. |
| **Agent/Tool Creation** | 🔴 Blocked | Requires `definition_id`. UI for creating definitions is missing. |
| **Cache Invalidation** | 🔴 Broken | New children not visible until reload (P2-CACHE-001). |

---

## 4. Detailed Test Scenarios

### Scenario 1: Workspace Root & L1 Session
1.  **Root Context Menu:** Right-click workspace -> Verify only "Create Session" exists.
2.  **Create Session:** Create "Test Session 1". Verify node appears.
3.  **L1 Context Menu:** Right-click session -> Verify "Open", "Edit", "Duplicate", "Delete".
4.  **Navigate:** Double-click session -> Verify breadcrumb updates.

### Scenario 2: L2 Container (Agent) - *Blocked by Definitions*
1.  **Navigate to L1:** Enter "Test Session 1".
2.  **Add Agent:** Right-click canvas -> "Add Agent".
3.  **Create New:** Select "Create New...".
4.  **Verify:** AgentInstance created in Firestore with `depth=2`.

### Scenario 3: Terminal Node (Source)
1.  **Navigate to Tool:** Enter a Tool container.
2.  **Add Source:** Right-click canvas -> "Add Source".
3.  **Verify Terminal:** Source cannot be double-clicked (no navigation).

---

## 5. Load Testing Plan (50 Sessions)

**Goal:** Create 50 L1 sessions via Batch API and validate frontend rendering.

### Execution Steps
1.  **Batch API:** POST `/api/v5/containers/batch` with 50 session payloads.
2.  **Firestore Check:** Validate 50 documents in `sessions` collection.
3.  **Frontend Check:** Load workspace, verify 50 nodes render without lag.
4.  **ResourceLinks:** Verify `usersession` has 50 entries in `resources_sessions`.

---

## 6. Known Issues & Blockers

*   **P2-EDIT-001 (High):** Session edits (title/desc) do not persist to Firestore.
*   **P2-CACHE-001 (High):** Newly created children not visible until page reload (Cache TTL issue).
*   **P2-DEFINITION-001 (Blocker):** No UI to create Agent/Tool definitions, blocking L2+ testing.

---

## 7. Reference: Execution History

*   **2025-12-09:** Validated Menu System (Pass) and Session Creation (Pass). Identified P2-EDIT-001 and P2-CACHE-001.
*   **2025-12-09:** Confirmed L2 Session visibility fix (removed legacy demo filter).

### Manual Test Session (2025-12-09)
- **Method:** Manual Launch (Explicit Terminal)
- **Test:** L2 Session Visibility
- **Result:** ✅ Passed (User confirmed visibility via screenshot)
- **Notes:** Fixed by removing isDemo filter in GameCanvas.tsx.
