import { test, expect } from '@playwright/test';

test('Debug Environment', async ({ page }) => {
  await page.goto('/');
  
  // Check localStorage
  const storage = await page.evaluate(() => localStorage.getItem('workspace-storage'));
  console.log('Storage Length:', storage?.length);
  
  // Dump body text
  const bodyText = await page.locator('body').innerText();
  console.log('Body Text Preview:', bodyText.substring(0, 500));
});
