export type ToolArgs = Record<string, any>;

function toSnake(key: string): string {
  return key.replace(/([A-Z])/g, '_$1').replace(/-/g, '_').toLowerCase();
}

export function normalizeArgs(args: ToolArgs = {}): ToolArgs {
  const normalized: ToolArgs = {};
  for (const [k, v] of Object.entries(args)) {
    normalized[toSnake(k)] = v;
  }
  return normalized;
}

function requireArray(name: string, value: any): string | null {
  if (!Array.isArray(value) || value.length === 0) {
    return `${name} must be a non-empty array`;
  }
  return null;
}

export type ValidationResult = { ok: true; normalized: ToolArgs } | { ok: false; errors: string[] };

/**
 * Lightweight arg/schema validation for ChatAgent tool calls.
 * This is a test-only helper (Option B) and does not affect runtime UI.
 */
export function validateToolArgs(tool: string, rawArgs: ToolArgs = {}): ValidationResult {
  const args = normalizeArgs(rawArgs);
  const errors: string[] = [];

  const requireNodeIds = () => {
    const nodeIds = args.node_ids ?? args.nodeids ?? args.node_ids_list ?? args.nodeIds;
    const err = requireArray('node_ids', nodeIds);
    if (err) errors.push(err);
  };

  switch (tool) {
    case 'apply_layout':
    case 'move_nodes':
    case 'delete_nodes':
      requireNodeIds();
      break;

    case 'create_session':
      // title optional; accept snake/camel position fields
      if (args.position_x !== undefined && typeof args.position_x !== 'number') {
        errors.push('position_x must be a number');
      }
      if (args.position_y !== undefined && typeof args.position_y !== 'number') {
        errors.push('position_y must be a number');
      }
      break;

    case 'find_resources':
      if (!args.scope_id) errors.push('scope_id is required');
      break;

    case 'batch_delete_resources':
      if (!args.items || !Array.isArray(args.items)) errors.push('items array is required');
      break;

    default:
      // For unrecognized tools, we accept but return normalized args
      break;
  }

  if (errors.length) {
    return { ok: false, errors };
  }

  return { ok: true, normalized: args };
}

