/**
 * MCP Observer Injection Script
 * 
 * This script injects a comprehensive observer into the running browser
 * that logs all user interactions, state changes, and navigation events
 * to the console. MCP Playwright can then read these via browser_console_messages.
 * 
 * Usage: npx tsx scripts/inject-observer.ts
 * 
 * After injection, Copilot uses `browser_console_messages` to see:
 * - [CLICK] element clicks with target info
 * - [NAV] route/URL changes
 * - [STATE] Zustand store mutations
 * - [ERROR] Any console errors
 * - [CONTEXT] Right-click context menu opens
 * - [MODAL] Modal open/close events
 */

import { chromium } from 'playwright';

function pickTargetPage(pages: import('playwright').Page[]) {
  const candidates = pages
    .filter((p) => {
      const url = p.url();
      if (!url || url === 'about:blank') return false;
      return /^(https?:\/\/)(localhost|127\.0\.0\.1):517\d\b/.test(url);
    })
    .sort((a, b) => a.url().length - b.url().length);

  return candidates[0] ?? pages.find((p) => p.url() && p.url() !== 'about:blank') ?? pages[0];
}

const OBSERVER_SCRIPT = `
(function() {
  const VERSION = 'v5-2025-12-15';

  // Cleanup any prior injection so we can safely reinject without duplicate logs.
  try {
    if (window.__MCP_OBSERVER__ && typeof window.__MCP_OBSERVER__.cleanup === 'function') {
      window.__MCP_OBSERVER__.cleanup();
    }
  } catch (e) {
    console.warn('[OBSERVER] Failed to cleanup prior observer:', e);
  }
  window.__MCP_OBSERVER_ACTIVE__ = true;
  window.__MCP_OBSERVER_VERSION__ = VERSION;
  
  console.log('[OBSERVER] ✅ MCP Observer injected - tracking all interactions', { version: VERSION });

  const stateForLogs = {
    lastUrl: location.href,
    unsubZustand: null,
    urlObserver: null,
    modalObserver: null,
    originalConsoleError: window.__MCP_ORIG_CONSOLE_ERROR__ || console.error,
    handlers: {}
  };

  // Provide a cleanup hook to avoid duplicate listeners on re-injection
  window.__MCP_OBSERVER__ = {
    version: VERSION,
    cleanup: () => {
      try {
        const h = stateForLogs.handlers;
        if (h.onClick) document.removeEventListener('click', h.onClick, true);
        if (h.onContextMenu) document.removeEventListener('contextmenu', h.onContextMenu, true);
        if (h.onDblClick) document.removeEventListener('dblclick', h.onDblClick, true);
        if (h.onKeyDown) document.removeEventListener('keydown', h.onKeyDown, true);
        if (h.onPopState) window.removeEventListener('popstate', h.onPopState, true);

        if (stateForLogs.urlObserver) stateForLogs.urlObserver.disconnect();
        if (stateForLogs.modalObserver) stateForLogs.modalObserver.disconnect();

        if (typeof stateForLogs.unsubZustand === 'function') stateForLogs.unsubZustand();
        if (typeof window.__MCP_ZUSTAND_UNSUB__ === 'function') window.__MCP_ZUSTAND_UNSUB__();

        // Restore console.error if we replaced it
        if (window.__MCP_ORIG_CONSOLE_ERROR__) {
          console.error = window.__MCP_ORIG_CONSOLE_ERROR__;
        }
      } catch (e) {
        console.warn('[OBSERVER] Cleanup error:', e);
      }
    }
  };
  
  // Track clicks
  stateForLogs.handlers.onClick = (e) => {
    const target = e.target;
    const tag = target.tagName?.toLowerCase() || 'unknown';
    const text = (target.textContent || '').slice(0, 50).trim();
    const classList = Array.from(target.classList || []).join('.');
    const id = target.id ? '#' + target.id : '';
    const dataAction = target.getAttribute('data-ai-action') || '';
    
    console.log('[CLICK]', {
      element: tag + id + (classList ? '.' + classList : ''),
      text: text || '(no text)',
      action: dataAction || '(none)',
      x: e.clientX,
      y: e.clientY
    });
  };
  document.addEventListener('click', stateForLogs.handlers.onClick, true);
  
  // Track right-clicks (context menu)
  stateForLogs.handlers.onContextMenu = (e) => {
    const target = e.target;
    console.log('[CONTEXT]', {
      element: target.tagName?.toLowerCase(),
      x: e.clientX,
      y: e.clientY
    });
  };
  document.addEventListener('contextmenu', stateForLogs.handlers.onContextMenu, true);
  
  // Track double-clicks (dive into container)
  stateForLogs.handlers.onDblClick = (e) => {
    const target = e.target;
    const text = (target.textContent || '').slice(0, 50).trim();
    console.log('[DBLCLICK]', {
      element: target.tagName?.toLowerCase(),
      text: text || '(no text)'
    });
  };
  document.addEventListener('dblclick', stateForLogs.handlers.onDblClick, true);
  
  // Track keyboard
  stateForLogs.handlers.onKeyDown = (e) => {
    if (e.key === 'Escape' || e.key === 'Enter' || e.key === 'Delete' || e.ctrlKey || e.metaKey) {
      console.log('[KEY]', {
        key: e.key,
        ctrl: e.ctrlKey,
        meta: e.metaKey,
        shift: e.shiftKey
      });
    }
  };
  document.addEventListener('keydown', stateForLogs.handlers.onKeyDown, true);
  
  // Track URL changes (SPA navigation)
  stateForLogs.lastUrl = location.href;
  stateForLogs.urlObserver = new MutationObserver(() => {
    if (location.href !== stateForLogs.lastUrl) {
      console.log('[NAV]', {
        from: stateForLogs.lastUrl,
        to: location.href,
        path: location.pathname
      });
      stateForLogs.lastUrl = location.href;
    }
  });
  stateForLogs.urlObserver.observe(document.body, { childList: true, subtree: true });
  
  // Also track popstate
  stateForLogs.handlers.onPopState = () => {
    console.log('[NAV]', {
      type: 'popstate',
      path: location.pathname
    });
  };
  window.addEventListener('popstate', stateForLogs.handlers.onPopState, true);
  
  // Track Zustand store changes
  const attachZustand = () => {
    const storeHook = window.__workspaceStore || window.__ZUSTAND_STORE__ || window.__workspace_store__;
    if (!storeHook?.subscribe || !storeHook?.getState) return false;

    // Replace prior subscription if present
    try {
      if (typeof window.__MCP_ZUSTAND_UNSUB__ === 'function') {
        window.__MCP_ZUSTAND_UNSUB__();
      }
    } catch (_) {}

    window.__MCP_ZUSTAND_UNSUB__ = storeHook.subscribe((state, prevState) => {
      const changes = {};

      const nextActive = state.activeContainerId ?? state.activeSessionId;
      const prevActive = prevState?.activeContainerId ?? prevState?.activeSessionId;
      if (nextActive !== prevActive) {
        changes.activeContainerId = nextActive;
      }

      if (state.activeContainerType !== prevState?.activeContainerType) {
        changes.activeContainerType = state.activeContainerType;
      }

      const nextContainers = state.containers || state.sessions;
      const prevContainers = prevState?.containers || prevState?.sessions;
      if ((nextContainers?.length || 0) !== (prevContainers?.length || 0)) {
        changes.containersCount = nextContainers?.length || 0;
      }

      if ((state.nodes?.length || 0) !== (prevState?.nodes?.length || 0)) {
        changes.nodesCount = state.nodes?.length || 0;
      }

      if ((state.selectedNodeIds?.length || 0) !== (prevState?.selectedNodeIds?.length || 0)) {
        changes.selectedCount = state.selectedNodeIds?.length || 0;
      }

      if ((state.breadcrumbs?.length || 0) !== (prevState?.breadcrumbs?.length || 0)) {
        changes.breadcrumbs = state.breadcrumbs?.map(b => b.title || b.id) || [];
      }

      if (Object.keys(changes).length > 0) {
        console.log('[STATE]', changes);
      }
    });

    console.log('[OBSERVER] Zustand subscription active');
    return true;
  };

  if (!attachZustand()) {
    console.warn('[OBSERVER] Zustand store not found - retrying in 1s');
    setTimeout(() => {
      if (!attachZustand()) {
        console.warn('[OBSERVER] Zustand store still not found after retry');
      } else {
        console.log('[OBSERVER] Zustand subscription active (delayed)');
      }
    }, 1000);
  }
  
  // Track modal open/close by watching DOM for modal elements
  stateForLogs.modalObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) {
          const el = node;
          if (el.getAttribute('role') === 'dialog' || 
              el.classList?.contains('modal') ||
              el.querySelector?.('[role="dialog"]')) {
            console.log('[MODAL]', { action: 'open', element: el.tagName });
          }
        }
      });
      mutation.removedNodes.forEach((node) => {
        if (node.nodeType === 1) {
          const el = node;
          if (el.getAttribute('role') === 'dialog' || el.classList?.contains('modal')) {
            console.log('[MODAL]', { action: 'close' });
          }
        }
      });
    });
  });
  stateForLogs.modalObserver.observe(document.body, { childList: true, subtree: true });
  
  // Track console errors
  window.__MCP_ORIG_CONSOLE_ERROR__ = stateForLogs.originalConsoleError;
  console.error = function(...args) {
    console.log('[ERROR]', args.map(a => String(a).slice(0, 200)).join(' '));
    stateForLogs.originalConsoleError.apply(console, args);
  };
  
  // Report initial state
  const storeHook = window.__workspaceStore || window.__ZUSTAND_STORE__ || window.__workspace_store__;
  const store = storeHook?.getState?.();
  const containers = store?.containers || store?.sessions || [];
  console.log('[OBSERVER] Initial state:', {
    url: location.pathname,
    activeContainer: store?.activeContainerId ?? store?.activeSessionId ?? 'none',
    activeType: store?.activeContainerType || 'unknown',
    nodes: store?.nodes?.length || 0,
    containers: containers?.length || 0
  });
})();
`;

async function injectObserver() {
  console.log('🔌 Connecting to browser on port 9222...');
  
  try {
    const browser = await chromium.connectOverCDP('http://localhost:9222');
    const contexts = browser.contexts();
    
    if (contexts.length === 0) {
      console.error('❌ No browser contexts found. Is Edge running with --remote-debugging-port=9222?');
      await browser.close();
      return;
    }
    
    const context = contexts[0];
    let pages = context.pages();

    // If the CDP-controlled Edge instance doesn't have the Vite tab, open it.
    const hasViteTab = pages.some((p) => /^(https?:\/\/)(localhost|127\.0\.0\.1):517\d\b/.test(p.url()));
    if (!hasViteTab) {
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
        console.error('❌ Could not open Vite app in the CDP browser (tried localhost:5173-5179)');
      }
      pages = context.pages();
    }
    
    if (pages.length === 0) {
      console.error('❌ No pages found in browser');
      await browser.close();
      return;
    }
    
    const targetPage = pickTargetPage(pages);
    if (!/^(https?:\/\/)(localhost|127\.0\.0\.1):517\d\b/.test(targetPage.url())) {
      console.log(`⚠️ No Vite page found, using: ${targetPage.url()}`);
    }
    
    console.log(`📄 Target page: ${targetPage.url()}`);
    
    // Inject the observer script
    await targetPage.evaluate(OBSERVER_SCRIPT);
    
    console.log('✅ MCP Observer injected successfully!');
    console.log('');
    console.log('📋 Copilot can now use browser_console_messages to see:');
    console.log('   [CLICK]   - User clicks with element info');
    console.log('   [DBLCLICK]- Double-clicks (dive into containers)');
    console.log('   [CONTEXT] - Right-click context menu');
    console.log('   [KEY]     - Keyboard shortcuts (Esc, Enter, Ctrl+X)');
    console.log('   [NAV]     - URL/route changes');
    console.log('   [STATE]   - Zustand store mutations');
    console.log('   [MODAL]   - Modal open/close events');
    console.log('   [ERROR]   - Console errors');
    
    await browser.close();
  } catch (error) {
    console.error('❌ Failed to inject observer:', error);
    console.log('');
    console.log('Make sure Edge is running with: .\\frontend\\scripts\\launch-debug-edge.ps1');
  }
}

injectObserver();
