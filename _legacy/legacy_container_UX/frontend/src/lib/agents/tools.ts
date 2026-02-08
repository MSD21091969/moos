/**
 * Tool Definitions
 * 
 * FunctionDeclarations for all agents to use.
 * Extracted from legacy gemini-live-client.ts and organized by category.
 * 
 * NOTE: Schema types use uppercase to match @google/genai SDK Type enum
 */

import type { FunctionDeclaration, ToolCall, ToolResult } from './types';

// ============================================================================
// Tool Categories
// ============================================================================

export const TOOL_CATEGORIES = {
  BRIDGE: 'Bridge Tools',
  SESSION: 'Session & Workspace',
  CANVAS: 'Canvas & Layout',
  CONTAINERS: 'Containers & Nodes',
  DEFINITIONS: 'Tool & Agent Definitions',
  FILE: 'File Operations',
} as const;

// ============================================================================
// Bridge Tools (Copilot ↔ Host communication)
// ============================================================================

export const bridgeTools: FunctionDeclaration[] = [
  {
    name: 'write_report',
    description: 'Write a report to the Collider Bridge outbox for Copilot to read. Use this to share findings, test results, or state snapshots with external tools.',
    parameters: {
      type: 'OBJECT',
      properties: {
        report_type: {
          type: 'STRING',
          enum: ['test_result', 'state_snapshot', 'finding', 'suggestion'],
          description: 'Type of report',
        },
        title: { type: 'STRING', description: 'Report title' },
        content: { type: 'STRING', description: 'Report content (markdown supported)' },
        data: { type: 'OBJECT', description: 'Structured data to include' },
      },
      required: ['report_type', 'title'],
    },
  },
  {
    name: 'read_bridge_inbox',
    description: 'Read any pending commands from the Collider Bridge inbox. Returns commands queued by Copilot.',
    parameters: {
      type: 'OBJECT',
      properties: {},
    },
  },
];

// ============================================================================
// Session & Workspace Tools
// ============================================================================

export const sessionTools: FunctionDeclaration[] = [
  {
    name: 'create_session',
    description: 'Create a new Session (Sticky Note) on the L0 canvas.',
    parameters: {
      type: 'OBJECT',
      properties: {
        title: { type: 'STRING', description: 'Session title/name' },
        position_x: { type: 'NUMBER', description: 'X coordinate for session' },
        position_y: { type: 'NUMBER', description: 'Y coordinate for session' },
        theme_color: { type: 'STRING', description: 'Hex color for session theme' },
      },
    },
  },
  {
    name: 'list_sessions',
    description: 'List all available Sessions (Sticky Notes) with their positions and status.',
    parameters: {
      type: 'OBJECT',
      properties: {},
    },
  },
  {
    name: 'query_sessions',
    description: 'SEMANTIC SEARCH: Find sessions by meaning, color, tags, or shared status. Use this when the user asks for "finance stuff" or "red notes".',
    parameters: {
      type: 'OBJECT',
      properties: {
        color: { type: 'STRING', description: 'Filter by theme color (e.g., "red", "#ff0000")' },
        tags: { type: 'ARRAY', items: { type: 'STRING' }, description: 'Filter by tags' },
        is_shared: { type: 'BOOLEAN', description: 'Filter by shared status' },
        search_term: { type: 'STRING', description: 'Semantic search term (e.g., "finance", "urgent")' },
      },
    },
  },
  {
    name: 'get_user_session',
    description: 'Get details of the current UserSession (Root L0 Container). Returns user info, permissions, and root resources.',
    parameters: {
      type: 'OBJECT',
      properties: {},
    },
  },
  {
    name: 'switch_session',
    description: 'Dive into a different Session (Sticky Note) by ID or title.',
    parameters: {
      type: 'OBJECT',
      properties: {
        session_id: { type: 'STRING', description: 'Session ID to switch to' },
        session_title: { type: 'STRING', description: 'Session title to search for' },
      },
    },
  },
  {
    name: 'delete_session',
    description: 'Delete a Session (Sticky Note) by ID.',
    parameters: {
      type: 'OBJECT',
      properties: {
        session_id: { type: 'STRING', description: 'Session ID to delete' },
        confirm: { type: 'BOOLEAN', description: 'Confirmation required' },
      },
      required: ['session_id'],
    },
  },
];

// ============================================================================
// Canvas & Layout Tools
// ============================================================================

export const canvasTools: FunctionDeclaration[] = [
  {
    name: 'observe_canvas',
    description: 'See current visual state of the UserSessionSpace - selected Sticky Notes (Containers), viewport zoom, and topology. Use this to understand the visual graph.',
    parameters: {
      type: 'OBJECT',
      properties: {},
    },
  },
  {
    name: 'move_nodes',
    description: 'Move selected Sticky Notes (Containers) to a new position.',
    parameters: {
      type: 'OBJECT',
      properties: {
        node_ids: {
          type: 'ARRAY',
          items: { type: 'STRING' },
          description: 'IDs of Sticky Notes to move',
        },
        delta_x: { type: 'NUMBER', description: 'Horizontal movement in pixels' },
        delta_y: { type: 'NUMBER', description: 'Vertical movement in pixels' },
        animate: { type: 'BOOLEAN', description: 'Use smooth animation' },
      },
      required: ['node_ids', 'delta_x', 'delta_y'],
    },
  },
  {
    name: 'select_nodes',
    description: 'Select Sticky Notes (Containers) by ID, type, or label pattern.',
    parameters: {
      type: 'OBJECT',
      properties: {
        node_ids: {
          type: 'ARRAY',
          items: { type: 'STRING' },
          description: 'Specific Sticky Note IDs',
        },
        type: { type: 'STRING', description: 'Container type (session/agent/tool/source)' },
        label_pattern: { type: 'STRING', description: 'Regex pattern to match labels' },
        clear_existing: { type: 'BOOLEAN', description: 'Clear current selection first' },
      },
    },
  },
  {
    name: 'apply_layout',
    description: 'Auto-arrange Sticky Notes using layout algorithm.',
    parameters: {
      type: 'OBJECT',
      properties: {
        algorithm: {
          type: 'STRING',
          enum: ['force', 'circular', 'tree', 'grid'],
          description: 'Layout algorithm',
        },
        node_ids: {
          type: 'ARRAY',
          items: { type: 'STRING' },
          description: 'Nodes to layout (empty = all)',
        },
        spacing: { type: 'NUMBER', description: 'Space between nodes in pixels' },
        animate: { type: 'BOOLEAN', description: 'Animate to new positions' },
      },
      required: ['algorithm'],
    },
  },
  {
    name: 'update_theme',
    description: 'Change visual theme colors and styles',
    parameters: {
      type: 'OBJECT',
      properties: {
        preset: {
          type: 'STRING',
          enum: ['ocean', 'forest', 'sunset', 'professional', 'dark', 'light'],
        },
        primary_color: { type: 'STRING', description: 'Hex color for primary elements' },
        background_color: { type: 'STRING', description: 'Hex color for background' },
        node_style: {
          type: 'STRING',
          enum: ['rounded', 'sharp', 'soft'],
          description: 'Node border style',
        },
      },
    },
  },
];

// ============================================================================
// Container & Node Tools
// ============================================================================

export const containerTools: FunctionDeclaration[] = [
  {
    name: 'create_node',
    description: 'Create a new node in the workspace',
    parameters: {
      type: 'OBJECT',
      properties: {
        type: { type: 'STRING', enum: ['object', 'agent', 'tool'], description: 'Node type' },
        label: { type: 'STRING', description: 'Node label/name' },
        position_x: { type: 'NUMBER', description: 'X coordinate' },
        position_y: { type: 'NUMBER', description: 'Y coordinate' },
        connect_to: {
          type: 'ARRAY',
          items: { type: 'STRING' },
          description: 'Node IDs to connect to',
        },
      },
      required: ['type', 'label'],
    },
  },
  {
    name: 'delete_nodes',
    description: 'Delete nodes from workspace',
    parameters: {
      type: 'OBJECT',
      properties: {
        node_ids: {
          type: 'ARRAY',
          items: { type: 'STRING' },
          description: 'IDs of nodes to delete',
        },
        confirm: { type: 'BOOLEAN', description: 'Skip confirmation prompt' },
      },
      required: ['node_ids'],
    },
  },
];

// ============================================================================
// Tool & Agent Definition Tools
// ============================================================================

export const definitionTools: FunctionDeclaration[] = [
  {
    name: 'create_custom_tool',
    description: 'Create a user-level custom tool definition that can be added to sessions.',
    parameters: {
      type: 'OBJECT',
      properties: {
        name: { type: 'STRING', description: 'Display name of the tool' },
        description: { type: 'STRING', description: 'What the tool does' },
        builtin_tool: { type: 'STRING', description: 'Backing builtin tool name (e.g., csv_analyzer)' },
        config: { type: 'OBJECT', description: 'Configuration payload for the tool' },
        tags: { type: 'ARRAY', items: { type: 'STRING' }, description: 'Tags for discovery' },
      },
      required: ['name', 'builtin_tool'],
    },
  },
  {
    name: 'create_custom_agent',
    description: 'Create a user-level custom agent definition.',
    parameters: {
      type: 'OBJECT',
      properties: {
        name: { type: 'STRING', description: 'Agent name' },
        description: { type: 'STRING', description: 'Agent summary' },
        system_prompt: { type: 'STRING', description: 'System prompt for the agent' },
        model: { type: 'STRING', description: 'Model identifier (e.g., gpt-4o)' },
        tags: { type: 'ARRAY', items: { type: 'STRING' }, description: 'Tags for discovery' },
      },
      required: ['name'],
    },
  },
  {
    name: 'add_tool_to_session',
    description: 'Attach an existing tool definition to a session.',
    parameters: {
      type: 'OBJECT',
      properties: {
        session_id: { type: 'STRING', description: 'Target session ID' },
        tool_name: { type: 'STRING', description: 'Tool definition name to attach' },
        display_name: { type: 'STRING', description: 'Override display title' },
        config_overrides: { type: 'OBJECT', description: 'Preset params or config overrides' },
      },
      required: ['session_id', 'tool_name'],
    },
  },
  {
    name: 'add_agent_to_session',
    description: 'Attach an existing agent definition to a session.',
    parameters: {
      type: 'OBJECT',
      properties: {
        session_id: { type: 'STRING', description: 'Target session ID' },
        agent_id: { type: 'STRING', description: 'Agent definition ID to attach' },
        display_name: { type: 'STRING', description: 'Override display title' },
        model_override: { type: 'STRING', description: 'Optional model override' },
        prompt_override: { type: 'STRING', description: 'Optional system prompt override' },
        active: { type: 'BOOLEAN', description: 'Mark as active agent' },
      },
      required: ['session_id', 'agent_id'],
    },
  },
  {
    name: 'browse_tools',
    description: 'List available tool definitions (optionally by category).',
    parameters: {
      type: 'OBJECT',
      properties: {
        category: { type: 'STRING', description: 'Filter tools by category' },
      },
    },
  },
  {
    name: 'browse_agents',
    description: 'List available agent definitions for a session (optionally search).',
    parameters: {
      type: 'OBJECT',
      properties: {
        session_id: { type: 'STRING', description: 'Session context for available agents' },
        search: { type: 'STRING', description: 'Search query for agent names or tags' },
      },
    },
  },
];

// ============================================================================
// File Operation Tools (Local Agent specific)
// ============================================================================

export const fileTools: FunctionDeclaration[] = [
  {
    name: 'read_file',
    description: 'Read contents of a file from the workspace. Requires workspace access permission.',
    parameters: {
      type: 'OBJECT',
      properties: {
        path: { type: 'STRING', description: 'File path relative to workspace root' },
      },
      required: ['path'],
    },
  },
  {
    name: 'write_file',
    description: 'Write content to a file in the workspace. Creates file if it does not exist.',
    parameters: {
      type: 'OBJECT',
      properties: {
        path: { type: 'STRING', description: 'File path relative to workspace root' },
        content: { type: 'STRING', description: 'Content to write' },
      },
      required: ['path', 'content'],
    },
  },
  {
    name: 'list_directory',
    description: 'List files and directories in a workspace folder.',
    parameters: {
      type: 'OBJECT',
      properties: {
        path: { type: 'STRING', description: 'Directory path relative to workspace root (empty for root)' },
      },
    },
  },
  {
    name: 'request_workspace_access',
    description: 'Request permission to access files in the workspace. Must be called before file operations.',
    parameters: {
      type: 'OBJECT',
      properties: {},
    },
  },
];

// ============================================================================
// Navigation Tools
// ============================================================================

export const navigationTools: FunctionDeclaration[] = [
  {
    name: 'navigate_to',
    description: 'Navigate to a specific view or page in the application.',
    parameters: {
      type: 'OBJECT',
      properties: {
        target: {
          type: 'STRING',
          enum: ['home', 'sessions', 'settings', 'help'],
          description: 'Target view to navigate to',
        },
        params: { type: 'OBJECT', description: 'Additional navigation parameters' },
      },
      required: ['target'],
    },
  },
  {
    name: 'open_modal',
    description: 'Open a modal dialog.',
    parameters: {
      type: 'OBJECT',
      properties: {
        modal_type: {
          type: 'STRING',
          enum: ['create_session', 'settings', 'help', 'confirm'],
          description: 'Type of modal to open',
        },
        props: { type: 'OBJECT', description: 'Modal properties' },
      },
      required: ['modal_type'],
    },
  },
  {
    name: 'close_modal',
    description: 'Close the currently open modal.',
    parameters: {
      type: 'OBJECT',
      properties: {},
    },
  },
];

// ============================================================================
// All Tools Combined
// ============================================================================

export const allTools: FunctionDeclaration[] = [
  ...bridgeTools,
  ...sessionTools,
  ...canvasTools,
  ...containerTools,
  ...definitionTools,
  ...fileTools,
  ...navigationTools,
];

// ============================================================================
// Tool Executor Interface
// ============================================================================

export interface ToolExecutorContext {
  /** Zustand workspace store */
  workspaceStore: unknown;
  /** ReactFlow instance */
  reactFlowInstance: unknown;
  /** Local agent for file operations */
  localAgent?: {
    readFile: (path: string) => Promise<{ success: boolean; content?: string; error?: string }>;
    writeFile: (path: string, content: string) => Promise<{ success: boolean; error?: string }>;
    listDirectory: (path: string) => Promise<{ success: boolean; files?: string[]; error?: string }>;
    requestWorkspaceAccess: () => Promise<boolean>;
  };
  /** Collider Bridge */
  colliderBridge?: {
    push: (command: unknown) => void;
    poll: () => unknown | null;
  };
}

/**
 * Create a tool executor function for handling tool calls
 */
export function createToolExecutor(context: ToolExecutorContext) {
  return async (call: ToolCall): Promise<ToolResult> => {
    const { function: fn } = call;
    const args = JSON.parse(fn.arguments);
    const toolName = fn.name;

    try {
      const result = await executeToolByName(toolName, args, context);
      return {
        toolCallId: call.id,
        result,
      };
    } catch (error) {
      return {
        toolCallId: call.id,
        result: null,
        error: String(error),
      };
    }
  };
}

/**
 * Execute a tool by name
 */
async function executeToolByName(
  name: string,
  args: Record<string, unknown>,
  context: ToolExecutorContext
): Promise<unknown> {
  // File operations (Local Agent)
  if (name === 'read_file' && context.localAgent) {
    return context.localAgent.readFile(args.path as string);
  }
  if (name === 'write_file' && context.localAgent) {
    return context.localAgent.writeFile(args.path as string, args.content as string);
  }
  if (name === 'list_directory' && context.localAgent) {
    return context.localAgent.listDirectory((args.path as string) ?? '');
  }
  if (name === 'request_workspace_access' && context.localAgent) {
    const granted = await context.localAgent.requestWorkspaceAccess();
    return { success: granted };
  }

  // Bridge operations
  if (name === 'write_report' && context.colliderBridge) {
    context.colliderBridge.push({
      type: 'report',
      ...args,
    });
    return { success: true };
  }
  if (name === 'read_bridge_inbox' && context.colliderBridge) {
    const command = context.colliderBridge.poll();
    return { command };
  }

  // Workspace operations - these need to be implemented by the ChatAgent
  // Return a marker that tells ChatAgent to handle these
  return {
    _delegateToComponent: true,
    toolName: name,
    args,
  };
}

// ============================================================================
// Tool Lookup Helpers
// ============================================================================

export function getToolByName(name: string): FunctionDeclaration | undefined {
  return allTools.find(t => t.name === name);
}

export function getToolsByCategory(category: keyof typeof TOOL_CATEGORIES): FunctionDeclaration[] {
  switch (category) {
    case 'BRIDGE':
      return bridgeTools;
    case 'SESSION':
      return sessionTools;
    case 'CANVAS':
      return canvasTools;
    case 'CONTAINERS':
      return containerTools;
    case 'DEFINITIONS':
      return definitionTools;
    case 'FILE':
      return fileTools;
    default:
      return [];
  }
}

/**
 * Get tools available for a specific agent type
 */
export function getToolsForAgent(agentType: 'voice' | 'coding' | 'local'): FunctionDeclaration[] {
  switch (agentType) {
    case 'voice':
      // Voice agent gets all tools except file operations (handled by local)
      return [...bridgeTools, ...sessionTools, ...canvasTools, ...containerTools, ...definitionTools, ...navigationTools];
    case 'coding':
      // Coding agent gets everything
      return allTools;
    case 'local':
      // Local agent emphasizes file operations but can do everything
      return allTools;
    default:
      return allTools;
  }
}
