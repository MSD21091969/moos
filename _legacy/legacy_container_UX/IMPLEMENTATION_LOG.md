# Implementation Log

## 2025-12-15 - Cleanup: Remove DebugOverlay + Prune Instructions + Remove Workflows
**Phase:** 1
**Author:** Copilot

### Context
Phase 1 demo UX and repo hygiene needed cleanup: an old debug HUD obscured recordings, instruction files were consolidated/pruned, and GitHub Actions workflows were intentionally removed to be rebuilt.

### Changes
- **UI:** Removed the Demo-mode bottom-left DebugOverlay (“Runtime State” terminal HUD).
- **Demo mode correctness:** Standardized demo checks to use `isDemoMode()` instead of raw `import.meta.env.VITE_MODE` comparisons in critical paths.
- **Docs/Instructions:** Deleted legacy general instruction files and removed their references from `.github/copilot-instructions.md`.
- **CI/CD:** Deleted `.github/workflows/*.yml` workflows (kept `tests.yml.example`) to rebuild new pipelines.
- **TypeScript hygiene:** Removed unused `@ts-expect-error` directives so `npm run build` passes.

### Verification
- [x] `npm run build` succeeded for the frontend.
- [x] Changes pushed to `feature/rebuild-v2`.

## 2025-12-15 - Phase 1 UX Recorder (Option B) + CDP Port Alignment
**Phase:** 1
**Author:** Copilot

### Context
Phase 1 UX debugging required a fast, reliable way to capture “what happened in the browser” without repeatedly running fragile one-shot scripts or attaching to the wrong Vite tab.

### Changes
- **Frontend tooling:** Added a single long-running UX recorder at `frontend/scripts/mcp/record-ux.ts`.
	- Attaches to Edge via CDP (`http://localhost:9222`)
	- Ensures Vite page exists (prefers `localhost:5174/workspace`, then other 517x)
	- Injects observer (if missing) and records console/navigation/errors
	- Periodic minimal Zustand snapshots (with redaction + change-detection)
	- Outputs: `frontend/test-results/mcp/ux-<timestamp>.jsonl` + `ux-<timestamp>.summary.md`
- **TypeScript tooling:** Added `frontend/scripts/tsconfig.json` so Node built-ins + timers typecheck cleanly for scripts.
- **Frontend consolidation (V5-first):** Removed legacy V4 client surface and standardized imports/entrypoints.
	- Removed `frontend/src/lib/api-v4.ts`
	- Promoted V5 client to the default `frontend/src/lib/api.ts`
	- Added `frontend/src/pages/WorkspacePage.tsx` as the canonical workspace route
	- Updated store + components to align with the container-based UI (sessions → containers terminology)
- **VS Code tasks:** Updated `.vscode/tasks.json` to add:
	- `🎥 Record: UX (CDP 9222)`
	- `🚀 Phase 1 (Demo) + 🎥 UX Recorder`
- **Port drift fixes:** Aligned defaults to demo port 5174:
	- `.vscode/settings.json` (`vscode-edge-devtools.defaultUrl`)
	- `scripts/launch-edge.ps1` (default URL)
- **Non-interactive startup:** Updated `scripts/start-phase1.ps1` to use `Invoke-WebRequest -UseBasicParsing` when polling localhost to avoid interactive prompts.
- **Docs:** Updated `.github/prompts/PHASE1_UX_DEMO.prompt.md` and `frontend/README.md` to reflect the new workflow.

### Verification
- [x] Ran the UX recorder with `--duration=5` and confirmed JSONL + summary files were created under `frontend/test-results/mcp/`.
- [x] Confirmed recorder snapshots include Zustand state (no `page.evaluate` runtime errors).
- [x] `npm run build` succeeded for the frontend.

### Related Bugs (Verification Pending)
- P1-10: Option B recorder workflow implemented.
- P1-11: 5173/5174 drift eliminated in defaults.
- P1-12: Phase 1 launcher polling made non-interactive.

---

## 2025-12-15 - Mock Backend & Store Orphan Loading
**Phase:** 1
**Author:** Copilot

### Context
Phase 1 demo mode was missing orphan container support. The picker showed empty because orphans were never loaded into `containerRegistry`.

### Problem Analysis
1. `orphanContainers` memo in ContextMenu reads from `containerRegistry`
2. But orphans with `parent_id: null` were never loaded into registry
3. Mock backend had seed data but frontend never called `listContainers`

### Changes
- **Store (`types.ts`):** Added `loadOrphans(type)` method signature to `ContainerSlice`.
- **Store (`container-slice.ts`):** Implemented `loadOrphans()` - fetches containers via API, filters orphans, populates registry.
- **ContextMenu:** Updated `handleAddExistingContainer` to `await loadOrphans(type)` before opening picker.
- **Mock Backend (`store-v5.ts`):** Earlier session added `parent_id: null` to `ORPHAN_AGENT`, `ORPHAN_TOOL`.

### Verification
- [x] `get_errors` returned no errors in modified files.
- [x] Code review confirms lazy-load pattern matches "Library synced on menu open" design.
- [ ] E2E test pending for demo mode picker flow.

### Related Bugs (Verification Pending)
- P1-09: Demo mock orphan support implemented; needs E2E validation in UI.

---

## 2025-12-15 - Library Feature (Orphan-Only Adoption)
**Phase:** 1
**Author:** Copilot
**Commit:** `743204c`

### Context
Implemented the "Library" feature where "Add Existing" menu reads from SSE-synced local registry, filtered for orphans (`parent_id=null`). Enforces strict tree topology: containers must be explicitly orphaned before re-adoption.

### Changes
- **Backend (`container_registry.py`):** `add_resource()` now raises `ValidationError` if child has existing `parent_id`. Uses `UPDATED` event for SSE notification.
- **Frontend (`container-slice.ts`):** Added CASE 2 in `handleContainerEvent` to track `parent_id` changes in `containerRegistry`.
- **Frontend (`ContextMenu.tsx`):** Added `orphanContainers` memo, `getOrphansByType()` filter, updated `handleSelectExisting` to use `instance_id`.
- **Docs (`ARCHITECTURE.md`):** Documented Unified Grid Model and Context-Aware Menus patterns.

### Verification
- [x] `get_errors` returned no errors in modified files.
- [x] Code review confirmed orphan filtering logic.
- [ ] E2E test pending for SSE → Registry → Menu flow.

### Related Bugs (Verification Pending)
- P1-01: "Add Existing Agent" now reads from `orphanContainers`.
- P1-02: "Add Existing Tool" uses the same `getOrphansByType()` filter.
- P1-07: Backend rejects non-orphan adoption with `ValidationError`.
- P1-08: SSE handler now tracks `parent_id` changes.

---

## 2025-12-15 - Phase 1 Step 2/3 Discipline + Findings Logged (No Fixes)
**Phase:** 1
**Author:** Copilot

### Context
We explicitly enforced a strict Phase 1 workflow:
- **Step 2:** collect evidence only (no code/spec/test changes), but **logging findings is allowed**.
- **Step 3:** discuss root causes and agree on fix/tests.
- **Step 4:** implement fixes only after explicit approval.

This entry documents the data-gathering and documentation updates performed during recent Step 2/3 work.

### Changes
- **Docs/Workflow:** Updated `.github/prompts/PHASE1_UX_DEMO.prompt.md` to clearly separate Step 2/3/4 responsibilities and to prevent “silent fixes”.
	- Added a Step 2 evidence checklist (repro path, expected vs observed, error signatures, recorder timestamps, state snapshot).
- **Bug Logging (Step 2 allowed):** Updated `BUG_LIST.md` with new Phase 1 findings and evidence links.

### Findings Captured (Logged as Bugs)
- **P1-16:** Blank-screen crash returning to `/workspace` after creating a Session inside a Tool; console shows `RangeError: Maximum call stack size exceeded`.
- **P1-17:** “Create Session” often does not result in a visible new session node (multiple levels).
- **P1-18:** Runtime type/state drift (e.g., container type reported as `session` while in tool context), likely impacting gating + parent selection.
- **P1-19:** Spec/intent ambiguity requiring a decision: whether Sessions are allowed under Agent/Tool as context containers.

### Evidence Artifacts
- UX recorder JSONL files under `frontend/test-results/mcp/` were used as the primary evidence source for timestamps and state snapshots.

### Verification
- [x] Confirmed repo is in log-only mode (no implementation/spec/test edits retained) aside from documentation and bug logging.

---

## 2025-12-12 - Phase 1 Fresh Start
**Phase:** 1
**Author:** Copilot

### Context
Initiating "Fresh Start" for Phase 1. Resetting documentation and focusing on UX Guardrails.

### Changes
- **Docs:** Created `PHASE1_UX_DEMO.prompt.md`, `PHASE2_INTEGRATION.prompt.md`, `PHASE3_PRODUCTION.prompt.md`.
- **Docs:** Created `docs_maintenance.instructions.md`.
- **Docs:** Archived old `BUG_LIST.md`, `IMPLEMENTATION_LOG.md`, `TESTING_E2E_GUIDE.md`.
- **Docs:** Created new `BUG_LIST.md` and `IMPLEMENTATION_LOG.md`.

### Verification
- [x] Documentation structure verified.
- [x] Initial Phase 1 test/docs scaffolding verified.
