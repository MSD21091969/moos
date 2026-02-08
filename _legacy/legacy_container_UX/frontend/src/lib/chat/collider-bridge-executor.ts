/**
 * Collider Bridge Executor - Command handler and polling loop
 * 
 * Processes commands from inbox and writes results to outbox.
 * Polls every 500ms when bridge.ready === true.
 */

/* eslint-disable no-console */
// Console logging is intentional for bridge debugging via browser_console_messages

import {
  ColliderCommand,
  ColliderTestCommand,
  ColliderTestResult,
  captureStateSnapshot,
} from './collider-bridge';

// =============================================================================
// COMMAND HANDLERS
// =============================================================================

type CommandHandler = (params: Record<string, unknown>) => Promise<unknown>;

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

const handlers: Record<ColliderCommand, CommandHandler> = {
  // ---------------------------------------------------------------------------
  // Navigation
  // ---------------------------------------------------------------------------
  navigate_into: async ({ nodeId }) => {
    const node = document.querySelector(`[data-id="${nodeId}"]`) as HTMLElement;
    if (!node) throw new Error(`Node ${nodeId} not found`);
    node.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
    await wait(500);
    return { url: location.href, pathname: location.pathname };
  },

  navigate_back: async () => {
    history.back();
    await wait(300);
    return { url: location.href };
  },

  goto_workspace_root: async () => {
    const rootLink = document.querySelector('nav a[href="/workspace"], .breadcrumb a:first-child') as HTMLAnchorElement;
    rootLink?.click();
    await wait(300);
    return { url: location.href };
  },

  goto_url: async ({ url }) => {
    location.href = url as string;
    await wait(500);
    return { url: location.href };
  },

  // ---------------------------------------------------------------------------
  // Node Interactions
  // ---------------------------------------------------------------------------
  click_node: async ({ nodeId }) => {
    const node = document.querySelector(`[data-id="${nodeId}"]`) as HTMLElement;
    if (!node) throw new Error(`Node ${nodeId} not found`);
    node.click();
    return { clicked: true, nodeId };
  },

  dblclick_node: async ({ nodeId }) => {
    const node = document.querySelector(`[data-id="${nodeId}"]`) as HTMLElement;
    if (!node) throw new Error(`Node ${nodeId} not found`);
    node.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
    await wait(300);
    return { url: location.href };
  },

  select_nodes: async ({ nodeIds }) => {
    const ids = nodeIds as string[];
    // Trigger selection via store if exposed, else click with ctrl
    const store = window.__workspaceStore?.getState();
    if (store && 'setSelectedNodeIds' in store) {
      (store as unknown as { setSelectedNodeIds: (ids: string[]) => void }).setSelectedNodeIds(ids);
    } else {
      // Fallback: click first node
      const node = document.querySelector(`[data-id="${ids[0]}"]`) as HTMLElement;
      node?.click();
    }
    return { selected: ids };
  },

  deselect_all: async () => {
    // Click on canvas background
    const canvas = document.querySelector('.react-flow__pane') as HTMLElement;
    canvas?.click();
    return { deselected: true };
  },

  // ---------------------------------------------------------------------------
  // Context Menu
  // ---------------------------------------------------------------------------
  open_context_menu: async ({ nodeId }) => {
    const node = document.querySelector(`[data-id="${nodeId}"]`) as HTMLElement;
    if (!node) throw new Error(`Node ${nodeId} not found`);
    const rect = node.getBoundingClientRect();
    node.dispatchEvent(
      new MouseEvent('contextmenu', {
        bubbles: true,
        clientX: rect.x + rect.width / 2,
        clientY: rect.y + rect.height / 2,
      })
    );
    await wait(200);
    const menu = document.querySelector('[role="menu"], [data-radix-menu-content]');
    return { menuVisible: !!menu };
  },

  click_menu_item: async ({ text }) => {
    const items = document.querySelectorAll('[role="menuitem"], [data-radix-collection-item]');
    let clicked = false;
    for (const item of items) {
      if (item.textContent?.includes(text as string)) {
        (item as HTMLElement).click();
        clicked = true;
        break;
      }
    }
    await wait(200);
    return { clicked, text };
  },

  close_menu: async () => {
    // Press Escape
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    await wait(100);
    return { closed: true };
  },

  // ---------------------------------------------------------------------------
  // Assertions
  // ---------------------------------------------------------------------------
  assert_url: async ({ pattern, exact }) => {
    const url = location.href;
    if (exact) {
      if (url !== pattern) throw new Error(`URL mismatch. Expected: "${pattern}", Got: "${url}"`);
    } else {
      const regex = new RegExp(pattern as string);
      if (!regex.test(url)) throw new Error(`URL does not match "${pattern}". Got: "${url}"`);
    }
    return { url, passed: true };
  },

  assert_breadcrumb: async ({ contains, notContains }) => {
    const nav = document.querySelector('nav[aria-label="breadcrumb"], .breadcrumb, [data-testid="breadcrumb"]');
    const text = nav?.textContent || '';
    if (contains && !text.includes(contains as string)) {
      throw new Error(`Breadcrumb does not contain "${contains}". Got: "${text}"`);
    }
    if (notContains && text.includes(notContains as string)) {
      throw new Error(`Breadcrumb should not contain "${notContains}". Got: "${text}"`);
    }
    return { breadcrumbText: text, passed: true };
  },

  assert_node_visible: async ({ nodeId }) => {
    const node = document.querySelector(`[data-id="${nodeId}"]`);
    if (!node) throw new Error(`Node ${nodeId} not visible`);
    return { visible: true, nodeId };
  },

  assert_node_not_visible: async ({ nodeId }) => {
    const node = document.querySelector(`[data-id="${nodeId}"]`);
    if (node) throw new Error(`Node ${nodeId} should not be visible`);
    return { notVisible: true, nodeId };
  },

  assert_menu_item: async ({ text, visible = true, disabled }) => {
    const items = document.querySelectorAll('[role="menuitem"], [data-radix-collection-item]');
    let found = false;
    let isDisabled = false;
    for (const item of items) {
      if (item.textContent?.includes(text as string)) {
        found = true;
        isDisabled = item.getAttribute('aria-disabled') === 'true' || item.hasAttribute('disabled');
        break;
      }
    }
    if (visible && !found) throw new Error(`Menu item "${text}" not found`);
    if (!visible && found) throw new Error(`Menu item "${text}" should not be visible`);
    if (disabled !== undefined && isDisabled !== disabled) {
      throw new Error(`Menu item "${text}" disabled=${isDisabled}, expected=${disabled}`);
    }
    return { found, disabled: isDisabled, passed: true };
  },

  assert_nodes_count: async ({ count, min, max }) => {
    const store = window.__workspaceStore?.getState();
    const actual = store?.nodes?.length ?? 0;
    if (count !== undefined && actual !== count) {
      throw new Error(`Node count mismatch. Expected: ${count}, Got: ${actual}`);
    }
    if (min !== undefined && actual < (min as number)) {
      throw new Error(`Node count ${actual} below minimum ${min}`);
    }
    if (max !== undefined && actual > (max as number)) {
      throw new Error(`Node count ${actual} above maximum ${max}`);
    }
    return { count: actual, passed: true };
  },

  assert_state: async ({ property, value, contains }) => {
    const store = window.__workspaceStore?.getState();
    const actual = getNestedProperty(store, property as string);
    if (value !== undefined && actual !== value) {
      throw new Error(`State ${property} mismatch. Expected: ${JSON.stringify(value)}, Got: ${JSON.stringify(actual)}`);
    }
    if (contains !== undefined) {
      const actualStr = JSON.stringify(actual);
      if (!actualStr.includes(contains as string)) {
        throw new Error(`State ${property} does not contain "${contains}". Got: ${actualStr}`);
      }
    }
    return { property, actual, passed: true };
  },

  // ---------------------------------------------------------------------------
  // State Capture
  // ---------------------------------------------------------------------------
  capture_state: async () => {
    return captureStateSnapshot();
  },

  get_nodes: async () => {
    const store = window.__workspaceStore?.getState();
    return (
      store?.nodes?.map((n) => ({
        id: n.id,
        type: n.type,
        label: n.data?.label,
      })) ?? []
    );
  },

  get_selected_nodes: async () => {
    const store = window.__workspaceStore?.getState();
    return store?.selectedNodeIds ?? [];
  },

  get_breadcrumbs: async () => {
    const store = window.__workspaceStore?.getState();
    return store?.breadcrumbs ?? [];
  },

  capture_dom: async ({ selector = '.react-flow' }) => {
    const el = document.querySelector(selector as string) || document.body;
    return { html: el.outerHTML.slice(0, 50000) }; // Truncate to 50KB
  },

  // ---------------------------------------------------------------------------
  // Store Actions
  // ---------------------------------------------------------------------------
  create_session: async (_params) => {
    // This would need store action - simplified for now
    console.log('[BRIDGE] create_session not implemented - use ChatAgent tools');
    return { created: false, reason: 'Use ChatAgent tools' };
  },

  delete_nodes: async (_params) => {
    console.log('[BRIDGE] delete_nodes not implemented - use ChatAgent tools');
    return { deleted: false, reason: 'Use ChatAgent tools' };
  },

  update_node: async (_params) => {
    console.log('[BRIDGE] update_node not implemented - use ChatAgent tools');
    return { updated: false, reason: 'Use ChatAgent tools' };
  },

  // ---------------------------------------------------------------------------
  // Utilities
  // ---------------------------------------------------------------------------
  wait: async ({ ms }) => {
    await wait(ms as number);
    return { waited: ms };
  },

  clear_storage: async () => {
    localStorage.clear();
    return { cleared: true };
  },

  reload_page: async () => {
    location.reload();
    return { reloading: true };
  },

  ping: async () => {
    return { pong: true, timestamp: Date.now() };
  },
};

// Helper: Get nested property from object
function getNestedProperty(obj: unknown, path: string): unknown {
  return path.split('.').reduce((acc, key) => (acc as Record<string, unknown>)?.[key], obj);
}

// =============================================================================
// EXECUTOR LOOP
// =============================================================================

let pollInterval: ReturnType<typeof setInterval> | null = null;

/**
 * Process a single command from the inbox
 */
async function processCommand(cmd: ColliderTestCommand): Promise<ColliderTestResult> {
  const startTime = Date.now();
  const handler = handlers[cmd.command];

  if (!handler) {
    return {
      id: cmd.id,
      command: cmd.command,
      success: false,
      error: `Unknown command: ${cmd.command}`,
      duration: Date.now() - startTime,
      timestamp: Date.now(),
    };
  }

  try {
    const data = await Promise.race([
      handler(cmd.params),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Command timeout')), cmd.timeout ?? 5000)
      ),
    ]);

    return {
      id: cmd.id,
      command: cmd.command,
      success: true,
      data,
      duration: Date.now() - startTime,
      timestamp: Date.now(),
    };
  } catch (error) {
    const snapshot = captureStateSnapshot();
    return {
      id: cmd.id,
      command: cmd.command,
      success: false,
      error: error instanceof Error ? error.message : String(error),
      duration: Date.now() - startTime,
      snapshots: snapshot,
      timestamp: Date.now(),
    };
  }
}

/**
 * Poll the inbox and process commands
 */
async function pollInbox(): Promise<void> {
  const bridge = window.__colliderBridge;
  if (!bridge?.ready || bridge.inbox.length === 0) return;

  // Process commands in order (FIFO)
  while (bridge.inbox.length > 0) {
    const cmd = bridge.inbox.shift()!;
    console.log(`[BRIDGE→HOST] Processing: ${cmd.command} (${cmd.id})`);

    const result = await processCommand(cmd);
    bridge.outbox.push(result);

    // Log for browser_console_messages
    const status = result.success ? '✅' : '❌';
    const summary = result.success
      ? JSON.stringify(result.data).slice(0, 100)
      : result.error;
    console.log(`[BRIDGE_RESULT] ${cmd.id} ${status} ${summary}`);
  }
}

/**
 * Start the bridge executor polling loop
 * Polls every 500ms when import.meta.env.DEV
 */
export function startBridgeExecutor(): void {
  if (!import.meta.env.DEV) {
    console.log('[BRIDGE] Executor disabled in production');
    return;
  }

  if (pollInterval) {
    console.log('[BRIDGE] Executor already running');
    return;
  }

  pollInterval = setInterval(pollInbox, 500);
  console.log('[BRIDGE] Executor started (500ms poll)');

  // Mark bridge as ready
  if (window.__colliderBridge) {
    window.__colliderBridge.ready = true;
    console.log('[BRIDGE] Ready for commands');
  }
}

/**
 * Stop the bridge executor
 */
export function stopBridgeExecutor(): void {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
    console.log('[BRIDGE] Executor stopped');
  }
  if (window.__colliderBridge) {
    window.__colliderBridge.ready = false;
  }
}
