import { chromium } from 'playwright';

async function clearStorage() {
  console.log('🧹 Connecting to Edge to clear localStorage...');
    const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const contexts = browser.contexts();
  
  const workspacePage = contexts
    .flatMap(ctx => ctx.pages())
    .find(p => p.url().includes('localhost:5173/workspace'));
  
  if (workspacePage) {
    console.log('✅ Found workspace page');
    await workspacePage.evaluate(() => {
      // Clear everything including the auth_token to force re-login
      localStorage.clear();
      console.log('🗑️ localStorage fully cleared via CDP');
      window.location.reload();
    });
    console.log('✨ Storage cleared and page reloaded');
  } else {
    console.error('❌ Workspace page not found');
  }
  
  await browser.close();
}

clearStorage().catch(console.error);
