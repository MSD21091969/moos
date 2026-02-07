# CI/CD Workflow: The Bug List Cycle

**Version:** 2025-12-08  
**Philosophy:** "Watch, Reproduce, Test, Fix."

This workflow moves from observational debugging to rigorous automated regression through a **3-Phase Cycle**.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [The Copilot Cycle](#2-the-copilot-cycle)
3. [Data Collection & Tooling](#3-data-collection--tooling)
4. [Phase 1: UX & Demo](#4-phase-1-ux--demo)
5. [Phase 2: Integration](#5-phase-2-integration)
6. [Phase 3: Production](#6-phase-3-production)
7. [Appendix: Tools Reference](#7-appendix-tools-reference)

---

## 1. Environment Setup

### 1.1 Prerequisites

| Tool | Required | Verify |
|------|----------|--------|
| Node.js 20+ | ✅ | `node --version` |
| Python 3.11+ | ✅ | `python --version` |
| gcloud CLI | ✅ | `gcloud --version` |

### 1.2 VS Code Extensions

```powershell
code --install-extension 42crunch.vscode-openapi --install-extension anweber.vscode-httpyac --install-extension cameron.vscode-pytest --install-extension littlefoxteam.vscode-python-test-adapter
```

### 1.3 Backend Environment

**Files Required:** `backend/.env`, `backend/service-account-dev.json`

**Required values:**
```dotenv
LOGFIRE_TOKEN=pylf_v1_eu_xxxxx
GOOGLE_APPLICATION_CREDENTIALS=./service-account-dev.json
GCP_PROJECT=mailmind-ai-djbuw
FIRESTORE_DATABASE=my-tiny-data-collider
```

---

## 2. The Copilot Cycle

We do not just "write tests." We observe behavior, reproduce it programmatically, and then fix it.

### The Flow
1.  **Watch (Observe):** User drives the app. Copilot watches via MCP tools (Observer, Network, Console).
2.  **Note (Log):** Copilot records behavior, expected vs actual, and potential causes in `BUG_LIST.md`.
3.  **Reproduce (Design Tests):** Copilot designs Playwright tests to mimic the user's actions exactly.
    *   *Requirement:* Consult **Context7** (Playwright docs) and **AI Toolkit** (Agent patterns) for best practices.
4.  **Design Fixes:** Analyze test results to propose architectural or logic fixes.
5.  **Fix & Verify:** Implement the fix and verify it passes the reproduction tests.

---

## 3. Data Collection & Tooling

To "Watch" effectively, we use a specific toolbelt.

### 3.1 The Observer Toolbelt
These tools provide the "Input" (User Actions) and "Response" (System State) data for evaluation.

| Tool | Script/Command | Purpose |
|------|----------------|---------|
| **Observer** | `npm run inject-observer` | Injects listener for `[CLICK]`, `[NAV]`, `[MODAL]` events. |
| **State Poller** | `npm run poll-state` | Snapshots URL, Breadcrumb, and deep Zustand store. |
| **Console** | `browser_console_messages` | Streams Observer logs and app errors to Copilot. |
| **Network** | `browser_network_requests` | Captures API 400/500 errors (Phase 2+). |
| **Visual** | `browser_snapshot` | Verifies UI layout and accessibility tree. |

### 3.2 Reference Tools (MANDATORY)
Before designing tests or fixes, you **MUST** consult:
*   **Context7 (`mcp_io`)**: For up-to-date syntax (Playwright, ReactFlow, FastAPI).
*   **AI Toolkit**: For "Agent Runner" patterns and evaluation strategies.

---

## 4. Phase 1: UX & Demo (Frontend Only)

**Goal:** Verify UI logic, state management (Zustand), and visual interactions (ReactFlow) without backend noise.
**Environment:** `VITE_MODE=demo` (Mock data in memory/localStorage).

### Workflow
1.  **Start:** `🎮 Start: Demo + Edge Debug`.
2.  **Inject:** Run `🔍 MCP: Inject Observer`.
3.  **Watch:** User interacts. Copilot monitors `browser_console_messages` for `[CLICK]` and `[STATE]` logs.
4.  **Note:** Log findings in `BUG_LIST.md` (Phase 1).
5.  **Reproduce:** Create `tests/e2e/repro-issue-XXX.spec.ts` using Playwright.
6.  **Fix:** Apply frontend fixes.
7.  **Gate:** All Phase 1 bugs `[x]` before Phase 2.

---

## 5. Phase 2: Integration (Mock Backend)

**Goal:** Verify that **everything working in Phase 1** also works with Backend Persistence.
**Environment:** `VITE_MODE=development`, Backend with MockFirestore.

### 5.1 The "Parity" Rule
*   "If it worked in Phase 1, it must work in Phase 2."
*   Phase 2 is essentially a **Regression Test** of Phase 1 using the real API.

### 5.2 Workflow
1.  **Start:** `🎮 Start: Debug Session (All-in-One)`.
2.  **Seed:** `python backend/scripts/development/seed_demo_data.py` (Ensure data exists).
3.  **Watch (Network):** Monitor `browser_network_requests` for API failures.
4.  **Reproduce:** Run the **Phase 1 E2E Suite** against the backend.
    *   *Command:* `npx playwright test --project=msedge`
5.  **Design Fixes:**
    *   If API fails (405/500): Fix Backend (`src/api/routes`).
    *   If State desyncs: Fix Frontend Store (`workspace-store.ts`).
    *   *Consult:* **Context7** for FastAPI/Pydantic patterns.
6.  **Gate:** All Phase 2 bugs fixed.

---

## 6. Phase 3: Production (Firestore)

**Goal:** Verify data persistence, security rules, and real cloud infrastructure behavior.
**Environment:** `VITE_MODE=production`, Backend with real `Firestore`.

### Workflow
1.  **Start:** `Start: Cloud Mode`.
2.  **Test:** Run E2E tests against Prod.
3.  **Monitor:** Check Cloud Run logs and Firestore indexes.
4.  **Fix:** Apply fixes (Indexes, Rules).
5.  **Finalize:** Consolidate `BUG_LIST.md` into `IMPLEMENTATION_LOG.md`.

---

## 7. Appendix: Tools Reference

### 7.1 Collider Bridge Protocol
**Purpose:** Bidirectional communication channel between Copilot and Host (DEV only).
**Access:** `window.__colliderBridge`.
**Console Tags:** `[BRIDGE→HOST]`, `[BRIDGE_RESULT]`.

### 7.2 Maintenance Rules
1.  **MCP First:** Consult Context7/AI Toolkit before writing tests.
2.  **Never Skip Phases:** Don't fix backend bugs in Phase 1.
3.  **Evidence Required:** Use Playwright traces/screenshots.
