
import { chromium } from 'playwright';
// import { fetch } from 'undici'; // Or native fetch if Node 18+

async function getAuthToken() {
  const res = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      username: 'enterprise@test.com',
      password: 'test123'
    }).toString()
  });
  
  if (!res.ok) throw new Error('Login failed');
  const data = await res.json();
  return data.access_token;
}

async function debug() {
  console.log('🔑 Getting token...');
  const token = await getAuthToken();
  console.log('✅ Got token');

  console.log('🚀 Launching browser (Edge)...');
  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log(`[Browser] ${msg.type()}: ${msg.text()}`));
  page.on('pageerror', err => console.error(`[Browser Error] ${err.message}`));

  console.log('💉 Injecting token...');
  await page.addInitScript((token) => {
    localStorage.setItem('auth_token', token);
    localStorage.setItem('user_id', 'user_enterprise');
    console.log('✅ Token injected into localStorage');
  }, token);

  console.log('🌐 Navigating to workspace...');
  await page.goto('http://localhost:5173/workspace');
  
  console.log('⏳ Waiting for 10 seconds...');
  await page.waitForTimeout(10000);
  
  console.log('📸 Taking screenshot...');
  await page.screenshot({ path: 'debug-screenshot.png' });
  
  await browser.close();
  console.log('👋 Done');
}

debug().catch(console.error);
