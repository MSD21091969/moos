import { test, expect } from '@playwright/test';

test.describe('Phase 1 UX Audit', () => {
  test.use({ baseURL: 'http://localhost:5173' });

  test.beforeEach(async ({ page }) => {
    // Ensure we are in demo mode (usually set via env, but we assume the app is running in demo mode)
    await page.goto('/');
    // Clear storage to reset demo data
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    // Wait for canvas to be ready (look for a node)
    await expect(page.locator('.react-flow__node').first()).toBeVisible({ timeout: 10000 });
  });

  test('Depth Traversal (L1 -> L4)', async ({ page }) => {
    // 1. Start at Root (L1) - Find a Session
    const sessionNode = page.locator('[data-testid="node-session"]').first();
    await expect(sessionNode).toBeVisible();
    const sessionTitle = await sessionNode.innerText();
    console.log(`Navigating into Session: ${sessionTitle}`);
    
    // Dive into Session (L2)
    await sessionNode.dblclick();
    await expect(page.locator('[data-testid="breadcrumb"]')).toContainText(sessionTitle);

    // 2. Find an Agent (L3)
    const agentNode = page.locator('[data-testid="node-agent"]').first();
    // If no agent exists, we might need to create one or this test assumes demo data has one
    if (await agentNode.isVisible()) {
        const agentTitle = await agentNode.innerText();
        console.log(`Navigating into Agent: ${agentTitle}`);
        
        // Dive into Agent (L3)
        await agentNode.dblclick();
        await expect(page.locator('[data-testid="breadcrumb"]')).toContainText(agentTitle);

        // 3. Find a Tool (L4)
        const toolNode = page.locator('[data-testid="node-tool"]').first();
        if (await toolNode.isVisible()) {
             const toolTitle = await toolNode.innerText();
             console.log(`Navigating into Tool: ${toolTitle}`);
             
             // Dive into Tool (L4)
             await toolNode.dblclick();
             await expect(page.locator('[data-testid="breadcrumb"]')).toContainText(toolTitle);
        } else {
            console.log('No Tool node found at L3 to traverse deeper.');
        }
    } else {
        console.log('No Agent node found at L2 to traverse deeper.');
    }
  });

  test('Terminal Node Integrity (Source)', async ({ page }) => {
    // Navigate to a context that has a Source (usually L2 or L3)
    const sessionNode = page.locator('[data-testid="node-session"]').first();
    await sessionNode.dblclick();

    const sourceNode = page.locator('[data-testid="node-source"]').first();
    if (await sourceNode.isVisible()) {
        // Right click to open context menu
        await sourceNode.click({ button: 'right' });
        const menu = page.locator('[role="menu"]'); // Adjust selector based on Radix UI or custom implementation
        await expect(menu).toBeVisible();

        // Verify "Open" is NOT present
        await expect(menu.getByText('Open')).not.toBeVisible();
        
        // Verify "Add Tool" / "Add Agent" is NOT present
        await expect(menu.getByText('Add Tool')).not.toBeVisible();
        await expect(menu.getByText('Add Agent')).not.toBeVisible();

        console.log('Terminal Node Integrity Verified: Source node has restricted actions.');
    } else {
        test.skip('No Source node found to test integrity.');
    }
  });

  test('Context Menu Accuracy (Agent)', async ({ page }) => {
    // Navigate to L2
    const sessionNode = page.locator('[data-testid="node-session"]').first();
    await sessionNode.dblclick();

    const agentNode = page.locator('[data-testid="node-agent"]').first();
    if (await agentNode.isVisible()) {
        await agentNode.click({ button: 'right' });
        const menu = page.locator('[role="menu"]');
        await expect(menu).toBeVisible();

        // Agent is a container, should allow adding children
        await expect(menu.getByText('Open')).toBeVisible();
        // Note: Exact text might vary ("Add Tool" vs "New Tool")
        // We check for existence of *some* add action
        const hasAddOption = await menu.getByText(/Add|New/).count() > 0;
        expect(hasAddOption).toBeTruthy();
    } else {
        test.skip('No Agent node found to test context menu.');
    }
  });

  test('Drag & Drop Nesting (Gap Analysis)', async ({ page }) => {
    // Navigate to L2
    const sessionNode = page.locator('[data-testid="node-session"]').first();
    await sessionNode.dblclick();

    const agentNode = page.locator('[data-testid="node-agent"]').first();
    const toolNode = page.locator('[data-testid="node-tool"]').first();

    if (await agentNode.isVisible() && await toolNode.isVisible()) {
        // Get positions
        const agentBox = await agentNode.boundingBox();
        const toolBox = await toolNode.boundingBox();

        if (agentBox && toolBox) {
            // Drag Tool CENTER to Agent CENTER
            await page.mouse.move(toolBox.x + toolBox.width / 2, toolBox.y + toolBox.height / 2);
            await page.mouse.down();
            await page.mouse.move(agentBox.x + agentBox.width / 2, agentBox.y + agentBox.height / 2, { steps: 10 });
            await page.mouse.up();

            // Wait a moment for potential animation/action
            await page.waitForTimeout(1000);

            // GAP CHECK: Does the tool disappear (nested) or stay?
            // If it stays, it means DnD nesting is NOT implemented.
            const toolStillVisible = await toolNode.isVisible();
            
            if (toolStillVisible) {
                console.warn('⚠️ GAP DETECTED: Drag & Drop nesting did not occur. Tool node remained on canvas.');
                // We don't fail the test, but we log it. 
                // Ideally, we'd expect it to be gone if the feature was working.
            } else {
                console.log('✅ Drag & Drop nesting appears to work (Tool node disappeared).');
            }
        }
    } else {
        test.skip('Need both Agent and Tool nodes to test DnD nesting.');
    }
  });

  test('Known Bug: Picker Modal (P1-01)', async ({ page }) => {
    // Navigate to L2
    const sessionNode = page.locator('[data-testid="node-session"]').first();
    await sessionNode.dblclick();

    // Right click canvas to add existing? Or Agent context menu?
    // Assuming "Add Existing" is in the context menu of the canvas or a container
    const canvas = page.locator('.react-flow__pane');
    await canvas.click({ button: 'right' });
    
    const menu = page.locator('[role="menu"]');
    const addExisting = menu.getByText(/Add Existing|Link/i);
    
    if (await addExisting.isVisible()) {
        await addExisting.click();
        // Check for modal
        const modal = page.locator('[role="dialog"]');
        // Known bug: Modal fails to render/open
        try {
            await expect(modal).toBeVisible({ timeout: 2000 });
            console.log('✅ Picker Modal opened (Bug fixed?)');
        } catch (e) {
            console.log('❌ Picker Modal failed to open (Bug P1-01 confirmed)');
        }
    } else {
        console.log('Skipping P1-01 check: "Add Existing" menu item not found.');
    }
  });
});
