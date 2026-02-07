/**
 * Console/State Dump - Connects to running Edge and dumps state
 */
import { test, expect, chromium } from '@playwright/test';
import * as fs from 'fs';

test('dump browser state', async () => {
  // Connect to existing Edge via CDP
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const contexts = browser.contexts();
  
  if (contexts.length === 0) {
    console.log('No browser contexts found');
    return;
  }

  const pages = contexts[0].pages();
  const page = pages.find(p => p.url().includes('localhost:5173'));
  
  if (!page) {
    console.log('App page not found');
    return;
  }

  console.log('=== CONNECTED TO PAGE ===');
  console.log('URL:', page.url());

  // Get Zustand state
  const state = await page.evaluate(() => {
    const store = (window as any).__ZUSTAND_STORE__ || (window as any).__workspaceStore;
    if (!store) return { error: 'Store not found' };
    const s = store.getState();
    return {
      containers: s.containers?.length || 0,
      nodes: s.nodes?.length || 0,
      edges: s.edges?.length || 0,
      activeContainerId: s.activeContainerId,
      mode: s.mode,
      containersList: s.containers?.map((c: any) => ({ id: c.id, title: c.title, type: c.type }))
    };
  });

  console.log('\n=== ZUSTAND STATE ===');
  console.log(JSON.stringify(state, null, 2));

  // Get console logs
  const logs: string[] = [];
  page.on('console', msg => logs.push(`[${msg.type()}] ${msg.text()}`));

  // Wait a moment to collect any new logs
  await page.waitForTimeout(1000);

  console.log('\n=== RECENT CONSOLE ===');
  logs.forEach(l => console.log(l));

  // Write to file for easy access
  fs.writeFileSync('browser-state.json', JSON.stringify(state, null, 2));
  console.log('\n✅ State written to browser-state.json');
});
