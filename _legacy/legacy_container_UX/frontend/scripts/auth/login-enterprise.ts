import { chromium } from 'playwright';

// Default credentials align with backend dev auto-create (password must be "test123")
const USERNAME = process.env.LOGIN_USERNAME || 'enterprise@test.com';
const PASSWORD = process.env.LOGIN_PASSWORD || 'test123';
const API_URL = process.env.API_URL || 'http://127.0.0.1:8000';

async function loginAndInject() {
  console.log('🔐 Authenticating as Enterprise User...');

  // 1. Get Token from Backend
  try {
    const formData = new URLSearchParams();
    formData.append('username', USERNAME);
    formData.append('password', PASSWORD);

    const controller = new AbortController();
    // Allow extra time in case backend cold-starts
    const timeout = setTimeout(() => controller.abort(), 30000);

    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!response.ok) {
      throw new Error(`Login failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    const token = data.access_token;
    console.log('✅ Token acquired from backend');

    // 2. Inject into Edge
    console.log('🔌 Connecting to Edge on port 9222...');
    const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
    const contexts = browser.contexts();
    const page = contexts.flatMap(ctx => ctx.pages()).find(p => p.url().includes('localhost:5173'));

    if (!page) {
      console.error('❌ Could not find workspace tab (localhost:5173)');
      await browser.close();
      process.exit(1);
    }

    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      console.log('💉 Token injected into localStorage');
      
      // Visual feedback
      const div = document.createElement('div');
      div.style.position = 'fixed';
      div.style.top = '80px';
      div.style.left = '50%';
      div.style.transform = 'translateX(-50%)';
      div.style.backgroundColor = '#2196F3'; // Blue
      div.style.color = 'white';
      div.style.padding = '10px 20px';
      div.style.borderRadius = '4px';
      div.style.zIndex = '99999';
      div.innerText = '🔐 Logged in as Enterprise';
      document.body.appendChild(div);
      setTimeout(() => div.remove(), 3000);
      
      // Force reload to pick up token if needed, or just let app react
      // location.reload(); // Optional: might be better to let user reload or app handle it
    }, token);

    console.log('✅ Token injected successfully');
    await browser.close();

  } catch (error) {
    console.error('❌ Login failed:', error);
    process.exit(1);
  }
}

loginAndInject();
