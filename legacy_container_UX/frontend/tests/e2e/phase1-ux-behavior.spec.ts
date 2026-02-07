import { test, expect } from '@playwright/test';

test.describe('Phase 1: UX Behavior & Gaps', () => {
  
  test.beforeEach(async ({ page }) => {
    // 1. Clean Slate
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    
    // 2. Wait for Canvas
    await expect(page.locator('.react-flow')).toBeVisible();
  });

  test('P1-04: Double-click Navigation (Diving)', async ({ page }) => {
    // Use "Trip to Santorini" from demo data
    const sessionNode = page.getByText('Trip to Santorini').first();
    await expect(sessionNode).toBeVisible();

    // Double click
    await sessionNode.dblclick();

    // Expectation: URL changes or Breadcrumbs appear
    // If broken, this will timeout or URL won't change
    await expect(page).toHaveURL(/\/workspace\/session-/); 
  });

  test('P1-01: Add Existing Agent Picker', async ({ page }) => {
    // Right click a session
    const sessionNode = page.getByText('Trip to Santorini').first();
    await sessionNode.click({ button: 'right' });

    // Click "Add Agent" -> "Add Existing..."
    await page.getByText('Add Agent').hover();
    await page.getByText('Add Existing...').click();

    // Expectation: Modal appears
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Select Agent')).toBeVisible();
  });

  test('P1-03: Drag & Drop Nesting', async ({ page }) => {
    // UOM Rule: Tools/Agents must be created INSIDE a session (L1+), not at workspace root
    // First, enter a session
    const sessionNode = page.getByText('Trip to Santorini').first();
    await expect(sessionNode).toBeVisible();
    await sessionNode.dblclick();
    await expect(page).toHaveURL(/\/workspace\/session-/);
    
    // Now create a Tool inside the session
    await page.locator('.react-flow__pane').click({ button: 'right' });
    await page.getByText('Add Tool', { exact: false }).click();
    await page.getByText('Create New...', { exact: false }).click();
    await page.getByText('Data Cleaner', { exact: false }).click();
    
    // Tool node should appear
    const toolNode = page.getByTestId('node-tool').first();
    await expect(toolNode).toBeVisible();
    
    // Create a nested session within this session to test drag & drop
    await page.locator('.react-flow__pane').click({ button: 'right' });
    await page.getByText('Add Session', { exact: false }).click();
    
    const nestedSession = page.getByTestId('node-session').last();
    await expect(nestedSession).toBeVisible();

    // Drag Tool over nested Session
    await toolNode.dragTo(nestedSession);

    // Expectation: Tool is removed from current view (nested into child session)
    await expect(toolNode).not.toBeVisible(); 
  });

  test('Background Context Menu: Create New Agent', async ({ page }) => {
    // UOM Rule: Agents must be created INSIDE a session (L1+), not at workspace root
    // First, enter a session
    const sessionNode = page.getByText('Trip to Santorini').first();
    await expect(sessionNode).toBeVisible();
    await sessionNode.dblclick();
    await expect(page).toHaveURL(/\/workspace\/session-/);
    
    // Now right click background INSIDE the session
    await page.locator('.react-flow__pane').click({ button: 'right' });
    
    // Click "Agent" (Create New)
    await page.getByText('Add Agent', { exact: false }).click();
    await page.getByText('Create New...', { exact: false }).click();
    await page.getByText('Data Analysis Agent', { exact: false }).click();

    // Expectation: New Agent node appears
    await expect(page.getByTestId('node-agent')).toBeVisible();
    await expect(page.getByText('New Agent')).toBeVisible();
  });

});
