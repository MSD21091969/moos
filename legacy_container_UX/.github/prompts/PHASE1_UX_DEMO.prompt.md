
# Phase 1: UX & Demo (Live)

**Philosophy:** "Tools follow us." Quick pace, live verification, reliable data.
**Setup:** Vite (5174) + Edge (CDP 9222).

## 1. The "Top Shelf" Workflow (Strict)

This workflow is intentionally strict to avoid "silent fixing" or accidental scope creep.

1. **User Request (Scope Lock):**
     - You ask for **Step 2 (observe)**, **Step 3 (analyze)**, or **Step 4 (fix)**.
     - If you say “stay in step 2”, I am **not allowed** to change implementation, tests, or specs.

2. **Step 2 — Live Inspection (Collect Data Only):**
     **Goal:** reproduce + capture evidence. **No fixes. No refactors. No tests.**
     - Use live tools (when available):
         - `mcp_microsoft_pla_browser_run_code` to query DOM/state
         - `mcp_microsoft_pla_browser_console_messages` to capture console errors
     - Prefer recorder-based evidence for tricky flows (CDP 9222):
         - Run the UX recorder to capture a timestamped event stream (NAV/CLICK/STATE/ERROR) into `frontend/test-results/mcp/*.jsonl`.
     - Capture *actionable* artifacts:
         - Exact repro steps
         - The error signature (e.g., `RangeError: Maximum call stack size exceeded`)
         - The most relevant stack/paths
         - Any correlated secondary errors (e.g., sync/update failures)
     - **Step 2 Evidence Checklist (5 bullets):**
         - Repro path: starting page → clicks → final page/route
         - Expected vs observed: what should have happened vs what did
         - Errors: console `error` + `pageerror` signature and top stack frames
         - Recorder: JSONL filename(s) + the exact timestamps of the key events
         - State snapshot: URL, `activeContainerId`, `activeContainerType`, node count, breadcrumbs, tier/mode
     - **Logging is allowed in Step 2:**
         - Add/append entries in `BUG_LIST.md` as **findings** with evidence links.
         - Do not mark as fixed; do not change status beyond “Open/In Progress”.

3. **Step 3 — Analysis & Strategy (Discuss First):**
     **Goal:** propose candidate causes + options, then agree on a fix plan.
     - Summarize findings from Step 2 (what we saw, when, how often).
     - Propose 1–3 plausible root causes with confidence levels.
     - Propose the smallest safe fix, and any follow-up refactors.
     - Propose targeted automated tests **before** implementation (Playwright/Pytest), but only after we agree to leave Step 2.
     - **Hard rule:** fixes are **only allowed** after we explicitly agree on them in Step 3.

4. **Step 4 — Action (Fixes + Verification):**
     **Only entered when you explicitly say so.**
     - Implement the agreed changes.
     - Verify:
         - live in the browser (same repro path)
         - plus automated tests (focused first, then broader)
     - If new issues appear, log them (don’t pile on unrelated fixes).

5. **Documentation Discipline:**
     - Step 2: log findings in `BUG_LIST.md` with evidence.
     - Step 4: once verified, update `IMPLEMENTATION_LOG.md` and/or mark the bug fixed.

---

## 2. Lessons Learned From Recent Runs (Good / Bad)

### Good (Keep Doing)
- Recorder-driven evidence (JSONL) makes crashes and timing issues reproducible.
- Logging precise error signatures + file references keeps debugging efficient.
- Separating issues (crash vs. creation reliability vs. spec intent) prevents "one mega bug".

### Bad (Don’t Repeat)
- Making implementation/spec/test changes while the user asked for Step 2-only.
- Letting “test alignment” drift into UI changes without an explicit Step 4 go-ahead.
- Assuming store state fields (e.g., container type) are trustworthy without validating via live state/recordings.

### Guardrails
- Before any edit: confirm we are in Step 3/4.
- After any edit (Step 4 only): re-run the shortest relevant tests and re-run the exact repro path.

---

## 3. Instruction Packs (Must Consult In Step 3/4)

These are the repo’s “real rules”. Even if we’re discussing work in a markdown file, when we move into Step 3/4 and touch code/tests, we must apply the right pack:

- Frontend work (`frontend/**`) → `.github/instructions/frontend.instructions.md`
- Backend work (`backend/**`) → `.github/instructions/backend.instructions.md`
- Any tests (`**/tests/**`, `*.ts/*.tsx/*.py`) → `.github/instructions/testing.instructions.md`
- Playwright test files (`**/*.spec.ts`, `**/*.test.ts`) → `.github/instructions/playwright-typescript.instructions.md`

Rule of thumb:
- Step 2: we may only log findings.
- Step 3: we explicitly reference the relevant instruction pack(s) while proposing the fix/test plan.
- Step 4: we execute the plan following those packs (no ad-hoc patterns).
