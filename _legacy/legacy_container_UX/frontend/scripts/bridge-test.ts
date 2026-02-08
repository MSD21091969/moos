/**
 * Bridge Test Script - Demo of Copilot ↔ Host communication
 * 
 * Run: npx tsx scripts/bridge-test.ts
 * 
 * This script demonstrates:
 * 1. Connecting to Edge via CDP
 * 2. Injecting test commands into bridge inbox
 * 3. Polling for results from bridge outbox
 * 4. Reporting pass/fail status
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
// @ts-expect-error - puppeteer-core types not installed, script runs with tsx
import puppeteer from 'puppeteer-core';

declare const process: { exit: (code: number) => never };
declare const window: Window & { __colliderBridge?: any };

const CDP_URL = 'http://localhost:9222';
const APP_URL = 'http://localhost:5173';

interface ColliderTestCommand {
  id: string;
  command: string;
  params: Record<string, unknown>;
  timestamp: number;
}

interface ColliderTestResult {
  id: string;
  command: string;
  success: boolean;
  data?: unknown;
  error?: string;
  duration: number;
  snapshots?: unknown;
  timestamp: number;
}

async function main() {
  console.log('🔗 Connecting to Edge via CDP...');
  
  let browser;
  try {
    browser = await puppeteer.connect({
      browserURL: CDP_URL,
      defaultViewport: null,
    });
  } catch {
    console.error('❌ Failed to connect. Is Edge running with --remote-debugging-port=9222?');
    console.log('   Run: .\\scripts\\launch-debug-edge.ps1');
    process.exit(1);
  }

  const pages = await browser.pages();
  const page = pages.find((p: any) => p.url().includes('localhost:5173')) || pages[0];
  
  if (!page.url().includes('localhost:5173')) {
    console.log(`📍 Navigating to ${APP_URL}...`);
    await page.goto(APP_URL, { waitUntil: 'networkidle0' });
  }

  console.log(`📍 Connected to: ${page.url()}`);

  // Check if bridge is initialized
  const bridgeStatus = await page.evaluate(() => {
    return {
      exists: !!(window as any).__colliderBridge,
      ready: (window as any).__colliderBridge?.ready,
      version: (window as any).__colliderBridge?.version,
      inboxCount: (window as any).__colliderBridge?.inbox?.length,
      outboxCount: (window as any).__colliderBridge?.outbox?.length,
    };
  });

  console.log('🌉 Bridge Status:', bridgeStatus);

  if (!bridgeStatus.exists) {
    console.error('❌ Bridge not initialized. Are you in DEV mode?');
    process.exit(1);
  }

  // =========================================================================
  // TEST SUITE: Basic Navigation
  // =========================================================================

  console.log('\n📋 Running Test Suite: Basic Navigation\n');

  const tests: ColliderTestCommand[] = [
    // Test 1: Ping
    {
      id: 'test_ping',
      command: 'ping',
      params: {},
      timestamp: Date.now(),
    },
    // Test 2: Capture initial state
    {
      id: 'test_capture_state',
      command: 'capture_state',
      params: {},
      timestamp: Date.now(),
    },
    // Test 3: Get all nodes
    {
      id: 'test_get_nodes',
      command: 'get_nodes',
      params: {},
      timestamp: Date.now(),
    },
    // Test 4: Assert URL contains workspace or localhost
    {
      id: 'test_assert_url',
      command: 'assert_url',
      params: { pattern: 'localhost' },
      timestamp: Date.now(),
    },
  ];

  // Inject all tests
  console.log(`📥 Injecting ${tests.length} test commands...`);
  
  await page.evaluate((commands: ColliderTestCommand[]) => {
    commands.forEach((cmd: ColliderTestCommand) => {
      (window as any).__colliderBridge!.inbox.push(cmd);
    });
  }, tests);

  // Poll for results
  console.log('⏳ Waiting for results...\n');
  
  const maxWait = 10000;
  const startTime = Date.now();
  let results: ColliderTestResult[] = [];

  while (results.length < tests.length && Date.now() - startTime < maxWait) {
    await new Promise(r => setTimeout(r, 500));
    
    results = await page.evaluate(() => {
      const r = (window as any).__colliderBridge?.outbox || [];
      return [...r] as ColliderTestResult[];
    });
  }

  // Report results
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(' TEST RESULTS');
  console.log('═══════════════════════════════════════════════════════════════\n');

  let passed = 0;
  let failed = 0;

  for (const result of results) {
    const icon = result.success ? '✅' : '❌';
    const status = result.success ? 'PASS' : 'FAIL';
    console.log(`${icon} [${status}] ${result.command} (${result.id})`);
    console.log(`   Duration: ${result.duration}ms`);
    
    if (result.success) {
      console.log(`   Data: ${JSON.stringify(result.data).slice(0, 100)}`);
      passed++;
    } else {
      console.log(`   Error: ${result.error}`);
      if (result.snapshots) {
        console.log(`   Snapshot: ${JSON.stringify(result.snapshots).slice(0, 200)}`);
      }
      failed++;
    }
    console.log('');
  }

  console.log('═══════════════════════════════════════════════════════════════');
  console.log(` Summary: ${passed} passed, ${failed} failed, ${tests.length} total`);
  console.log('═══════════════════════════════════════════════════════════════');

  // Clear outbox
  await page.evaluate(() => {
    (window as any).__colliderBridge!.outbox = [];
  });

  // Disconnect (don't close - Edge is shared)
  await browser.disconnect();
  
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(console.error);
