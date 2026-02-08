---
description: 'Playwright with TypeScript testing instructions'
applyTo: '**/*.spec.ts, **/*.test.ts, playwright.config.ts'
---

# Playwright & TypeScript Testing

## Core Principles
- **Reliability:** Tests must be deterministic. Avoid `waitForTimeout`. Use web-first assertions (`expect(locator).toBeVisible()`).
- **Isolation:** Each test should run independently. Use `test.beforeEach` to set up state.
- **Readability:** Use Page Object Models (POM) to abstract page details.
- **Type Safety:** Leverage TypeScript for strong typing in tests and POMs.

## Repo Defaults
- Prefer the `msedge` project: `npx playwright test --project=msedge`.
- Prefer user-facing locators; use `data-testid` only when roles/names aren’t stable.
- Avoid “menu item count == 0” assertions when possible; prefer asserting the correct items are visible for the current context.

## Best Practices

### Locators
- Prefer user-facing locators:
  - `page.getByRole('button', { name: 'Submit' })`
  - `page.getByLabel('Username')`
  - `page.getByText('Welcome')`
- Avoid XPath or CSS selectors tied to implementation details (e.g., `.div > .span`).

### Assertions
- Use async assertions:
  ```typescript
  await expect(page.getByRole('heading')).toHaveText('Dashboard');
  ```
- Avoid manual polling loops.

### Page Object Model (POM)
- Structure POMs in `tests/pages/`.
- Example:
  ```typescript
  export class LoginPage {
    readonly page: Page;
    readonly submitButton: Locator;

    constructor(page: Page) {
      this.page = page;
      this.submitButton = page.getByRole('button', { name: 'Login' });
    }

    async login() { ... }
  }
  ```

### Configuration
- Use `playwright.config.ts` for global settings (base URL, timeouts, retries).
- Run tests in parallel (`fullyParallel: true`).

## Debugging
- Use `npx playwright test --ui` for interactive debugging.
- Use `page.pause()` to stop execution and inspect the page.
- Use Trace Viewer for post-mortem analysis.
