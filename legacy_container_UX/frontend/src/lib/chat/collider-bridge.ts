/**
 * Collider Bridge - Bidirectional communication between Copilot and Host
 * 
 * Protocol:
 * - Copilot injects commands into window.__colliderBridge.inbox via browser_evaluate
 * - Host polls inbox (500ms) and executes commands
 * - Host writes results to outbox + console.log('[BRIDGE_RESULT]')
 * - Copilot reads results via browser_evaluate or browser_console_messages
 * 
 * Security: Only active when import.meta.env.DEV === true
 */

// =============================================================================
// BRIDGE TYPES
// =============================================================================

export interface ColliderBridge {
  inbox: ColliderTestCommand[];
  outbox: ColliderTestResult[];
  ready: boolean;
  version: string;
}

export interface ColliderTestCommand {
  id: string;                     // Unique command ID (e.g., 'cmd_1733582400000')
  command: ColliderCommand;       // Command name (snake_case)
  params: Record<string, unknown>;// Command arguments
  timestamp: number;              // Unix timestamp (ms)
  priority?: 'high' | 'normal';   // Execution priority (default: normal)
  timeout?: number;               // Max wait time (ms, default: 5000)
}

export interface ColliderTestResult {
  id: string;                     // Matches command ID
  command: string;                // Echo of command name
  success: boolean;               // Pass/fail
  data?: unknown;                 // Return value on success
  error?: string;                 // Error message on failure
  duration: number;               // Execution time (ms)
  snapshots?: StateSnapshot;      // State context on failure
  timestamp: number;              // Completion timestamp
  _read?: boolean;                // Internal: marked after Copilot reads
}

export interface StateSnapshot {
  activeSessionId?: string | null;
  activeContainerId?: string | null;
  activeContainerType?: string | null;
  nodesCount?: number;
  selectedNodeIds?: string[];
  breadcrumbs?: Array<{ id: string; title: string; type: string }>;
  url?: string;
  localStorage?: Record<string, unknown>;
}

// =============================================================================
// COMMAND TYPES
// =============================================================================

export type ColliderCommand =
  // Navigation
  | 'navigate_into'           // Double-click to dive into container
  | 'navigate_back'           // Go back one level (breadcrumb)
  | 'goto_workspace_root'     // Return to workspace root
  | 'goto_url'                // Navigate to specific URL

  // Node Interactions
  | 'click_node'              // Single click on node
  | 'dblclick_node'           // Double click on node
  | 'select_nodes'            // Select one or more nodes
  | 'deselect_all'            // Clear selection

  // Context Menu
  | 'open_context_menu'       // Right-click on node
  | 'click_menu_item'         // Click menu item by text
  | 'close_menu'              // Close any open menu

  // Assertions
  | 'assert_url'              // Assert current URL matches pattern
  | 'assert_breadcrumb'       // Assert breadcrumb contains/excludes text
  | 'assert_node_visible'     // Assert node is visible on canvas
  | 'assert_node_not_visible' // Assert node is NOT visible
  | 'assert_menu_item'        // Assert menu item exists (visible/disabled)
  | 'assert_nodes_count'      // Assert number of nodes
  | 'assert_state'            // Assert Zustand state properties

  // State Capture
  | 'capture_state'           // Snapshot Zustand + localStorage + URL
  | 'get_nodes'               // Get all nodes (id, type, label)
  | 'get_selected_nodes'      // Get selected node IDs
  | 'get_breadcrumbs'         // Get current breadcrumb trail
  | 'capture_dom'             // Get DOM snapshot (heavy)

  // Store Actions (mirrors ChatAgent tools)
  | 'create_session'          // Create new session
  | 'delete_nodes'            // Delete selected nodes
  | 'update_node'             // Update node properties

  // Utilities
  | 'wait'                    // Wait for specified ms
  | 'clear_storage'           // Clear localStorage
  | 'reload_page'             // Refresh the page
  | 'ping';                   // Health check - returns { pong: true }

// =============================================================================
// GLOBAL DECLARATION
// =============================================================================

declare global {
  interface Window {
    __colliderBridge?: ColliderBridge;
    __workspaceStore?: {
      getState: () => WorkspaceStateMinimal;
    };
  }
}

// Minimal workspace state interface (for bridge - avoids circular import)
interface WorkspaceStateMinimal {
  activeSessionId: string | null;
  activeContainerId: string | null;
  activeContainerType: string | null;
  nodes: Array<{ id: string; type: string; data?: { label?: string } }>;
  selectedNodeIds: string[];
  breadcrumbs: Array<{ id: string; title: string; type: string }>;
}

// =============================================================================
// BRIDGE INITIALIZATION
// =============================================================================

export const BRIDGE_VERSION = '1.0.0';

/**
 * Initialize the Collider Bridge on window
 * Only runs in DEV mode
 */
export function initColliderBridge(): ColliderBridge | null {
  if (!import.meta.env.DEV) {
    console.log('[BRIDGE] Disabled in production');
    return null;
  }

  if (window.__colliderBridge) {
    console.log('[BRIDGE] Already initialized');
    return window.__colliderBridge;
  }

  const bridge: ColliderBridge = {
    inbox: [],
    outbox: [],
    ready: false,
    version: BRIDGE_VERSION,
  };

  window.__colliderBridge = bridge;
  console.log(`[BRIDGE] Initialized v${BRIDGE_VERSION}`);
  return bridge;
}

// =============================================================================
// HELPER: Create command ID
// =============================================================================

export function createCommandId(prefix: string = 'cmd'): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
}

// =============================================================================
// HELPER: Capture current state snapshot
// =============================================================================

export function captureStateSnapshot(): StateSnapshot {
  const store = window.__workspaceStore?.getState();
  return {
    activeSessionId: store?.activeSessionId ?? null,
    activeContainerId: store?.activeContainerId ?? null,
    activeContainerType: store?.activeContainerType ?? null,
    nodesCount: store?.nodes?.length ?? 0,
    selectedNodeIds: store?.selectedNodeIds ?? [],
    breadcrumbs: store?.breadcrumbs ?? [],
    url: location.href,
  };
}
