---
description: Generate Playwright Test
---
Generate a Playwright test for the selected component or feature.

# Test Structure
1.  **Setup:**
    -   Use `test.beforeEach` for repetitive setup.
    -   Mock backend calls using `page.route` if testing UI isolation (Phase 1).
    -   Use real backend if testing Integration (Phase 2).

2.  **Locators:**
    -   Prioritize **User-Facing Locators**: `getByRole`, `getByText`, `getByLabel`.
    -   Avoid CSS/XPath selectors unless absolutely necessary.

3.  **Assertions:**
    -   Use **Web-First Assertions**: `await expect(locator).toBeVisible()`.
    -   Do not use manual waits (`waitForTimeout`).

4.  **Example:**
    ```typescript
    test('should create a new container', async ({ page }) => {
      await page.goto('/');
      await page.getByRole('button', { name: 'New Note' }).click();
      await expect(page.getByTestId('container-node')).toBeVisible();
    });
    ```
