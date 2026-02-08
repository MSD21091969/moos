---
description: Testing guidelines for Playwright and Pytest
applyTo: "**/*.{ts,tsx,py},**/tests/**"
---

# Testing Instructions

## Philosophy
"Watch → Reproduce → Test → Fix"

## Scope Discipline (Phase 1)
- **Step 2 (Observe):** collect evidence and log findings only; do **not** add/modify tests.
- **Step 3 (Analyze):** propose the minimal test(s) that would catch the bug/regression; agree on the plan.
- **Step 4 (Fix):** implement the test(s) and fix together, then verify.

## 3-Phase Workflow
| Phase | Task | Backend | Firestore |
|-------|------|---------|-----------|
| **1. UX** | `🚀 Launch: Phase 1 (Demo)` | None | None (localStorage) |
| **2. Integration** | `🚀 Start: Dev Environment (Golden Path)` | Local (8000) | **Real** |
| **3. Production** | `🚀 Launch: Phase 3 (Cloud)` | Cloud Run | **Real** |

## Playwright (E2E)
- **Location:** `frontend/tests/`
- **Run All:** `npx playwright test --project=msedge`
- **Run UOM Rules:** `npx playwright test uom- --project=msedge`
- **Golden Path:** Always use `scripts/start-dev-environment.ps1` to start the environment before running Phase 2 tests.

## Pytest (Backend)
- **Location:** `backend/tests/`
- **Run:** `pytest`
- **Coverage:** `pytest --cov=src`


## Playwright Best Practices (E2E)
### Good Patterns
- **Setup:** Use `test.beforeEach` for repetitive setup (login, navigation).
- **Locators:** Use **User-Facing Locators** (`getByRole`, `getByText`, `getByLabel`).
  - `page.getByRole('button', { name: 'Save' })`
- **Assertions:** Use **Web-First Assertions** (auto-retrying).
  - `await expect(locator).toBeVisible()`
  - `await expect(locator).toHaveText('Success')`
- **Isolation:** Tests should be independent. Use `test.describe` to group related tests.
- **Mocking:** Use `page.route` to mock backend responses for pure UI tests (Phase 1).
- **Trace:** Use `trace: 'on-first-retry'` in config for debugging failures.
- **Soft Assertions:** Use `expect.soft` for non-blocking checks (e.g., checking multiple UI elements).

### Bad Patterns
- **Manual Waits:** `await page.waitForTimeout(1000)` (Flaky!). Use assertions instead.
- **XPath/CSS:** Avoid brittle selectors like `div > div:nth-child(3)`.
- **Manual Assertions:** `expect(await locator.isVisible()).toBe(true)` (No retry!).
- **Over-Mocking:** Avoid mocking everything in Phase 2/3; test real integrations.

## Pytest Best Practices (Backend)
### Good Patterns
- **TestClient:** Use `fastapi.testclient.TestClient` for API integration tests.
- **Fixtures:** Use `conftest.py` for shared fixtures (db client, auth headers).
- **Parametrization:** Use `@pytest.mark.parametrize` to test multiple inputs.
- **Dependency Overrides:** Use `app.dependency_overrides` to mock auth or db in tests.

### Bad Patterns
- **Real External Services:** Mock external APIs (OpenAI, Stripe) in unit tests.
- **State Leakage:** Ensure DB is cleaned up after tests (use `cleanup_firestore.py` logic).
- **Complex Logic in Tests:** Keep tests simple: Arrange, Act, Assert.
