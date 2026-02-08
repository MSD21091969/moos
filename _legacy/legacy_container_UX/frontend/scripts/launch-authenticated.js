import { chromium } from '@playwright/test';

(async () => {
  console.log('🚀 Launching Edge (Authenticated)...');
  
  try {
    // Launch Edge (channel: 'msedge')
    // headless: false to see the UI
    const browser = await chromium.launch({ 
      headless: false, 
      channel: 'msedge',
      args: ['--start-maximized'] 
    });
    
    const context = await browser.newContext({
      viewport: null // Allow window resizing
    });
    
    const page = await context.newPage();
    
    // Inject Auth Token
    await page.addInitScript(() => {
      console.log('🔑 Injecting Auth Tokens...');
      localStorage.clear();
      localStorage.setItem('auth_token', 'test-token-enterprise');
      localStorage.setItem('user_id', 'user_enterprise');
    });
    
    console.log('🌐 Navigating to Workspace...');
    await page.goto('http://localhost:5173/workspace');
    
    console.log('✅ Ready! Browser will stay open.');
    console.log('Press Ctrl+C in the terminal to close.');
    
    // Keep the script running so the browser doesn't close
    await new Promise(() => {});
  } catch (error) {
    console.error('❌ Error launching browser:', error);
    process.exit(1);
  }
})();
