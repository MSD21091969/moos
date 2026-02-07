# Phase 3: Production (Prompt)

**Context:** Cloud Deployment, Real Auth, Live Traffic.
**Environment:** `VITE_MODE=production` (Cloud Run).

---

## 1. Environment Setup (Solid Start)
1.  **Clean Slate:**
    *   Ensure local environment is clean.
2.  **Launch:**
    *   Run `Tasks: 🚀 Launch: Phase 3 (Cloud)`.
    *   Frontend points to `https://api.mailmind.ai` (or equivalent).
3.  **Verification:**
    *   Login flow works with real Google Auth.

## 2. Bug/Feature List (Fresh Start)
*   **Action:** Archive Phase 2 list. Create `BUG_LIST.md` for Phase 3.
*   **Focus:** Auth Redirects, CORS, Cold Starts, Quotas.

## 3. Workflow Cycle

### A. Observation (User)
*   **Role:** User tests in "Incognito" or real devices.
*   **Action:** Report connectivity or auth issues.

### B. Analysis & Research (Copilot Agent)
*   **Tools:**
    *   **GCP Logs:** `Tasks: ☁️ GCP: Query Cloud Run Errors`.
    *   **Logfire:** Production traces.
*   **Output:** Update `BUG_LIST.md` with deployment-specifics.

### C. Test Design (Copilot Agent)
*   **Goal:** Smoke Testing & Availability for the *current* cycle.
*   **Principle:** "New Cycle = New Tests".
*   **Tool:** Playwright (`frontend/tests/e2e/production-smoke.spec.ts`).
*   **Strategy (Professional):**
    *   **Freshness:** Design specific tests for the active Bug List items.
    *   **Sanity Checks:** Verify critical paths only (Login -> Load -> Logout).
    *   **Non-Destructive:** Do NOT delete real user data unless using a test account.
    *   **Timeouts:** Increase timeouts for network latency.

### D. Planning (Plan Mode)
*   **Handoff:** Agent -> Plan Mode.
*   **Action:** Propose infrastructure changes (Terraform/Dockerfile).
*   **Approval:** User reviews.

### E. Implementation (Agent Mode)
*   **Action:** Apply config changes, redeploy.
*   **Log:** Update `IMPLEMENTATION_LOG.md`.

## 4. Exit Criteria
*   Successful Login/Logout in Production.
*   No 5xx Errors in GCP Logs.
