import { chromium } from 'playwright';

(async () => {
  const targetUrl = process.env.TDC_URL ?? 'http://localhost:5173/workspace';

  try {
    const browser = await chromium.connectOverCDP('http://localhost:9222');
    const contexts = browser.contexts();

    if (contexts.length === 0) {
      console.error('[ERR] No browser context found');
      process.exit(1);
    }

    const context = contexts[0];
    const page = context.pages()[0] ?? (await context.newPage());

    await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });

    await page.evaluate(() => {
      localStorage.setItem('user_id', 'enterprise@test.com');
      localStorage.setItem('auth_token', 'test-token-for-skip-auth');
    });

    const userData = await page.evaluate(() => ({
      user_id: localStorage.getItem('user_id'),
      auth_token: localStorage.getItem('auth_token'),
    }));

    console.log('✅ Auth token successfully injected into browser');
    console.log('   user_id:', userData.user_id);
    console.log('   auth_token:', userData.auth_token);

    await page.reload({ waitUntil: 'domcontentloaded' });
    console.log('✅ Page reloaded with auth credentials');

    if (typeof browser.disconnect === 'function') {
      browser.disconnect();
    }
  } catch (err) {
    console.error('[ERR]', err.message);
    process.exit(1);
  }
})();
