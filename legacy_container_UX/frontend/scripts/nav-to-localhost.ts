import { chromium } from 'playwright';

async function nav() {
  try {
    const browser = await chromium.connectOverCDP('http://localhost:9222');
    const context = browser.contexts()[0];
    const page = context.pages()[0]; // Use the first page (which was chrome-error)
    
    console.log('Navigating to http://localhost:5173 ...');
    await page.goto('http://localhost:5173');
    console.log('✅ Navigated');
    await browser.close();
  } catch (e) {
    console.error(e);
  }
}
nav();