/**
 * MCP State Poller Script
 * 
 * This script provides a quick snapshot of the current browser state
 * for debugging purposes. It reads and displays:
 * - Current URL and breadcrumb
 * - Zustand store state (sessions, nodes, selected)
 * - localStorage data
 * - Recent console messages
 * 
 * Usage: npx tsx scripts/poll-state.ts
 */

import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';

function findVitePages(pages: import('playwright').Page[]) {
  return pages
    .filter((p) => {
      const url = p.url();
      if (!url || url === 'about:blank') return false;
      return /^(https?:\/\/)(localhost|127\.0\.0\.1):517\d\b/.test(url);
    })
    // Prefer the shortest URL (usually the app root) over assets.
    .sort((a, b) => a.url().length - b.url().length);
}

async function pollState() {
  const reportLines: string[] = [];
  const logLine = (line: string) => {
    reportLines.push(line);
    console.log(line);
  };
  const logJson = (label: string, value: unknown) => {
    const json = JSON.stringify(value, null, 2);
    reportLines.push(`${label} ${json}`);
    console.log(label, value);
  };

  const reportPath = 'test-results/mcp/poll-state.txt';

  logLine('🔍 Polling browser state...');
  
  try {
    const browser = await chromium.connectOverCDP('http://localhost:9222');
    const contexts = browser.contexts();
    
    if (contexts.length === 0) {
      logLine('❌ No browser contexts found');
      await browser.close();
      return;
    }
    
    const context = contexts[0];
    let pages = context.pages();

    // Ensure the CDP-controlled Edge instance actually has the Vite tab open.
    let vitePages = findVitePages(pages);
    if (vitePages.length === 0) {
      const tryPorts = [5174, 5173, 5175, 5176, 5177, 5178, 5179];
      const page = await context.newPage();
      let opened = false;

      for (const port of tryPorts) {
        const url = `http://localhost:${port}/`;
        try {
          await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 8000 });
          opened = true;
          break;
        } catch {
          // keep trying
        }
      }

      if (!opened) {
        logLine('❌ Could not open Vite app in the CDP browser (tried localhost:5173-5179)');
        logLine('Open tabs in CDP browser:');
        pages.forEach((p, i) => logLine(`  [${i}] ${p.url()}`));
        await browser.close();
        return;
      }

      pages = context.pages();
      vitePages = findVitePages(pages);
    }
    
    const targetPage = vitePages[0] ?? pages.find((p) => p.url() && p.url() !== 'about:blank') ?? pages[0];
    
    logLine('\n═══════════════════════════════════════');
    logLine('📍 CURRENT STATE');
    logLine('═══════════════════════════════════════\n');
    
    // URL
    logLine(`🌐 URL: ${targetPage.url()}`);

    // Title
    const title = await targetPage.title();
    if (title) {
      logLine(`📄 Title: ${title}`);
    }

    // Tabs (helps diagnose attaching to the wrong page)
    try {
      const tabs = await Promise.all(
        pages.slice(0, 10).map(async (p, i) => {
          let t = '';
          try {
            t = await p.title();
          } catch {
            // ignore
          }
          return { i, url: p.url(), title: t };
        })
      );
      logLine('\n🧾 OPEN TABS (first 10):');
      tabs.forEach((t) => logLine(`   [${t.i}] ${t.url}${t.title ? ` — ${t.title}` : ''}`));
    } catch {
      // ignore
    }

    // === "What's on screen" (text-only) ===
    // Best tool here is Playwright's accessibility (ARIA) snapshot.
    // It describes the current UI semantically (headings, buttons, dialogs, etc.) without screenshots.
    try {
      const dialogCount = await targetPage.locator('[role="dialog"]').count();
      const bannerCount = await targetPage.locator('banner, [role="banner"]').count();
      const mainCount = await targetPage.locator('main, [role="main"]').count();
      logLine(`\n🧩 UI REGIONS: banner=${bannerCount}, main=${mainCount}, dialogs=${dialogCount}`);
    } catch {
      // ignore
    }

    try {
      const focus = await targetPage.evaluate(() => {
        const el = document.activeElement as HTMLElement | null;
        if (!el) return null;
        const role = el.getAttribute?.('role');
        const ariaLabel = el.getAttribute?.('aria-label');
        const id = (el as any).id ? `#${(el as any).id}` : '';
        const tag = el.tagName?.toLowerCase?.() || 'unknown';
        const text = (el.textContent || '').trim().slice(0, 80);
        return { tag, id, role, ariaLabel, text: text || null };
      });
      if (focus) {
        logJson('\n🎯 FOCUSED ELEMENT:', focus);
      }
    } catch {
      // ignore
    }

    // ARIA snapshot (preferred)
    try {
      const root = targetPage.locator('body');
      // ariaSnapshot returns a YAML-like accessibility tree string.
      const aria = await (root as any).ariaSnapshot?.();
      if (typeof aria === 'string' && aria.trim()) {
        const lines = aria.split(/\r?\n/);
        const maxLines = 120;
        logLine('\n🧠 ARIA SNAPSHOT (body):');
        if (lines.length <= maxLines) {
          logLine(lines.join('\n'));
        } else {
          logLine(lines.slice(0, maxLines).join('\n'));
          logLine(`... (truncated, ${lines.length - maxLines} more lines)`);
        }
      }
    } catch (e) {
      logLine(`\n⚠️ ARIA snapshot unavailable: ${e instanceof Error ? e.message : String(e)}`);
    }

    // Visible text fallback (trimmed)
    try {
      const text = await targetPage.locator('body').innerText();
      const lines = text
        .split(/\r?\n/)
        .map((l) => l.trim())
        .filter(Boolean);
      const maxLines = 40;
      logLine('\n📝 VISIBLE TEXT (body, trimmed):');
      if (lines.length === 0) {
        logLine('   (no visible text found)');
      } else if (lines.length <= maxLines) {
        lines.forEach((l) => logLine(`   ${l}`));
      } else {
        lines.slice(0, maxLines).forEach((l) => logLine(`   ${l}`));
        logLine(`   ... (truncated, ${lines.length - maxLines} more lines)`);
      }
    } catch {
      // ignore
    }
    
    // Get Zustand state
    const state = await targetPage.evaluate(() => {
      const storeHook =
        (window as any).__workspaceStore ||
        (window as any).__ZUSTAND_STORE__ ||
        (window as any).__workspace_store__;

      const snapshot = storeHook?.getState?.();
      if (!snapshot) return null;

      const containers = snapshot.containers || snapshot.sessions || [];
      const activeContainerId = snapshot.activeContainerId ?? snapshot.activeSessionId ?? null;

      return {
        activeContainerId,
        activeContainerType: snapshot.activeContainerType ?? null,
        userSessionId: snapshot.userSessionId ?? null,
        containersCount: containers?.length || 0,
        nodesCount: snapshot.nodes?.length || 0,
        selectedNodeIds: snapshot.selectedNodeIds || [],
        breadcrumbs: snapshot.breadcrumbs?.map((b: any) => b.title || b.id) || [],
        containers: (containers || [])
          .map((c: any) => ({
            id: c.id,
            title: c.title,
            type: c.containerType ?? c.type,
            status: c.status,
            depth: c.depth,
          }))
          .slice(0, 10),
        nodes: (snapshot.nodes || [])
          .map((n: any) => ({
            id: n.id,
            type: n.type,
            label: n.data?.label || n.data?.title,
          }))
          .slice(0, 10),
      };
    });
    
    if (state) {
      logLine('\n📊 ZUSTAND STATE:');
      logLine(`   Active Container: ${state.activeContainerId || '(workspace root)'}`);
      logLine(`   Active Type: ${state.activeContainerType || '(unknown)'}`);
      logLine(`   User Session: ${state.userSessionId || '(none)'}`);
      logLine(`   Containers: ${state.containersCount}`);
      logLine(`   Nodes: ${state.nodesCount}`);
      logLine(`   Selected: ${state.selectedNodeIds.length} nodes`);

      if (state.breadcrumbs?.length) {
        logLine(`   Store Breadcrumbs: ${state.breadcrumbs.join(' > ')}`);
      }
      
      if (state.containers?.length > 0) {
        logLine('\n   Containers:');
        state.containers.forEach((c: any) => {
          logLine(`     - ${c.title || c.id} (${c.id}) [type: ${c.type || 'unknown'}, depth: ${c.depth ?? 'n/a'}]`);
        });
      }
      
      if (state.nodes?.length > 0) {
        logLine('\n   Visible Nodes:');
        state.nodes.forEach((n: any) => {
          logLine(`     - ${n.label || n.id} (${n.type})`);
        });
      }
    } else {
      logLine('\n⚠️ Zustand store not accessible');
    }
    
    // Get localStorage
    const localStorage = await targetPage.evaluate(() => {
      const data = window.localStorage.getItem('workspace-storage');
      if (!data) return null;
      try {
        const parsed = JSON.parse(data);
        return {
          hasData: true,
          stateKeys: Object.keys(parsed.state || parsed || {}),
          version: parsed.version
        };
      } catch {
        return { hasData: true, error: 'parse error' };
      }
    });
    
    logLine('\n💾 LOCALSTORAGE:');
    if (localStorage?.hasData) {
      logLine(`   Version: ${localStorage.version || 'unknown'}`);
      logLine(`   State keys: ${localStorage.stateKeys?.join(', ') || 'N/A'}`);
    } else {
      logLine('   (empty)');
    }
    
    // Get breadcrumb
    const breadcrumb = await targetPage.evaluate(() => {
      const nav = document.querySelector('nav[aria-label="breadcrumb"]');
      if (!nav) return null;
      const links = nav.querySelectorAll('a, span');
      return Array.from(links).map(el => el.textContent?.trim()).filter(Boolean);
    });
    
    if (breadcrumb && breadcrumb.length > 0) {
      logLine(`\n🧭 BREADCRUMB: ${breadcrumb.join(' > ')}`);
    }
    
    logLine('\n═══════════════════════════════════════\n');

    // Persist full report to disk so VS Code task output truncation doesn't hide the details.
    try {
      await mkdir(dirname(reportPath), { recursive: true });
      await writeFile(reportPath, reportLines.join('\n'), 'utf8');
      console.log(`📝 Full poll report saved to: ${reportPath}`);
    } catch (e) {
      console.log(`⚠️ Failed to write report file: ${e instanceof Error ? e.message : String(e)}`);
    }
    
    await browser.close();
  } catch (error) {
    console.error('❌ Failed to poll state:', error);
    try {
      await mkdir(dirname(reportPath), { recursive: true });
      await writeFile(
        reportPath,
        reportLines.join('\n') +
          `\n\nERROR: ${error instanceof Error ? error.stack || error.message : String(error)}`,
        'utf8'
      );
      console.log(`📝 Partial poll report saved to: ${reportPath}`);
    } catch {
      // ignore
    }
  }
}

pollState();
