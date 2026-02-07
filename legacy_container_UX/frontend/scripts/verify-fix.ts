
import { chromium } from 'playwright';

async function run() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const context = browser.contexts()[0];
  const page = context.pages()[0];

  console.log('🔄 Reloading page...');
  await page.reload();
  await page.waitForTimeout(2000);

  console.log('📸 Snapshot 1: Workspace');
  // Click "Trip to Santorini" (session-1)
  // We need to find the node. It's likely a div with text "Trip to Santorini"
  // But in ReactFlow it's canvas.
  // We can use URL navigation for reliability in this script.
  
  console.log('🚀 Diving into Session 1...');
  await page.goto('http://localhost:5173/session/session-1');
  await page.waitForTimeout(2000);
  
  // Check for Agent Node
  const agentNode = page.locator('text=Trip Planner');
  if (await agentNode.count() > 0) {
      console.log('✅ Found Agent Node: Trip Planner');
  } else {
      console.error('❌ Agent Node NOT found');
  }

  // Dive into Agent (session-1-agent)
  console.log('🚀 Diving into Agent...');
  await page.goto('http://localhost:5173/session/session-1-agent');
  await page.waitForTimeout(2000);

  // Check for Memory Node
  const memoryNode = page.locator('text=Agent Memory');
  if (await memoryNode.count() > 0) {
      console.log('✅ Found Memory Node inside Agent');
  } else {
      console.error('❌ Memory Node NOT found inside Agent');
  }

  // Test Zoom/Pan Persistence
  console.log('🔍 Testing Zoom/Pan...');
  
  // Pan the Agent view
  await page.mouse.move(100, 100);
  await page.mouse.down();
  await page.mouse.move(300, 300); // Pan
  await page.mouse.up();
  await page.waitForTimeout(1000);
  
  // Go back to Session 1
  console.log('⬅️ Going back to Session 1...');
  await page.goto('http://localhost:5173/session/session-1');
  await page.waitForTimeout(2000);
  
  // Go back to Agent
  console.log('➡️ Returning to Agent...');
  await page.goto('http://localhost:5173/session/session-1-agent');
  await page.waitForTimeout(2000);
  
  // We can't easily check viewport programmatically without evaluating JS
  const viewport = await page.evaluate(() => {
      // @ts-expect-error - accessing Zustand store injected on window for test-only verification
      const store = window.__ZUSTAND_STORE__.getState();
      return store.sessionViewports['session-1-agent'];
  });
  
  console.log('📊 Agent Viewport:', viewport);
  if (viewport && viewport.x !== 0) {
      console.log('✅ Viewport persisted (x != 0)');
  } else {
      console.log('⚠️ Viewport might be default (x=0) or not saved');
  }

  await browser.close();
}

run().catch(console.error);
