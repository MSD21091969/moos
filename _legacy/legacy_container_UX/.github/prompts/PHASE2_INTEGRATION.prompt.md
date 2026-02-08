# Phase 2: Integration (Prompt)

**Context:** Real Backend, Local Firestore, API Integration.
**Environment:** `VITE_MODE=development` (Localhost:8000).

---

## 1. Environment Setup (Solid Start)
1.  **Clean Slate:**
    *   Run `Tasks: 🧹 Clean: Environment`.
2.  **Launch:**
    *   Run `Tasks: 🚀 Start: Dev Environment (Golden Path)`.
    *   Wait for Backend (8000) and Frontend (5173).
3.  **Verification:**
    *   Check `http://localhost:8000/health`.
    *   Check `http://localhost:8000/docs` (Swagger).

## 2. Bug/Feature List (Fresh Start)
*   **Action:** Archive Phase 1 list. Create `BUG_LIST.md` for Phase 2.
*   **Focus:** Persistence, Sync, Error Handling, Latency.

## 3. Workflow Cycle

### A. Observation (User)
*   **Role:** User performs complex flows (Create -> Refresh -> Verify).
*   **Action:** Report data inconsistencies or errors.

### B. Analysis & Research (Copilot Agent)
*   **Tools:**
    *   **Logfire:** `Tasks: 🔥 Logfire: Query Errors`.
    *   **Trace Explorer:** Analyze request spans.
    *   **Context7:** Research FastAPI/Pydantic patterns.
*   **Output:** Update `BUG_LIST.md` with backend-specific details (Trace IDs, Error Codes).

### C. Test Design (Copilot Agent)
*   **Goal:** Data Integrity & Concurrency for the *current* cycle.
*   **Principle:** "New Cycle = New Tests".
*   **Tools:**
    *   **Playwright:** E2E flows (`frontend/tests/e2e/v5-*.spec.ts`).
    *   **Pytest:** API integration (`backend/tests/integration/`).
*   **Strategy (Professional):**
    *   **Freshness:** Design specific tests for the active Bug List items.
    *   **State Management:** Explicitly create/delete `UserSession` per test (No shared state).
    *   **Fixtures:** Use `conftest.py` for DB clients.
    *   **Mocking:** Mock external LLM APIs, but use **Real Firestore**.

### D. Planning (Plan Mode)
*   **Handoff:** Agent -> Plan Mode.
*   **Action:** Propose schema changes or API updates.
*   **Approval:** User reviews.

### E. Implementation (Agent Mode)
*   **Action:** Apply fixes (Backend & Frontend).
*   **Log:** Update `IMPLEMENTATION_LOG.md`.

## 4. Exit Criteria
*   Zero "Zombie Nodes" (Referential Integrity).
*   Data persists across restarts.
*   Pytest & Playwright suites pass.
