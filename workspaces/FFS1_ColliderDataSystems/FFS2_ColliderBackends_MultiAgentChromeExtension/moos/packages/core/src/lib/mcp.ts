export const JSON_RPC_VERSION = '2.0' as const;

export type JsonRpcId = string | number | null;

export interface JsonRpcError {
  code: number;
  message: string;
}

export interface JsonRpcRequest<TParams = Record<string, unknown>> {
  jsonrpc: typeof JSON_RPC_VERSION;
  id?: JsonRpcId;
  method: string;
  params?: TParams;
}

export interface JsonRpcResponse<TResult = unknown> {
  jsonrpc: typeof JSON_RPC_VERSION;
  id: JsonRpcId;
  result?: TResult;
  error?: JsonRpcError;
}

export interface ToolExecutionResult {
  output: unknown;
  error?: string;
}

export interface McpToolsListResult {
  tools: Array<{
    name: string;
    description?: string;
  }>;
}

export interface McpToolsCallParams {
  name: string;
  input?: unknown;
}

export const MCP_METHODS = {
  toolsList: 'tools/list',
  toolsCall: 'tools/call',
  serverReady: 'server.ready',
} as const;

export const JSON_RPC_ERROR_CODES = {
  parseError: -32700,
  invalidRequest: -32600,
  methodNotFound: -32601,
  invalidParams: -32602,
  internalError: -32603,
} as const;

export const isJsonRpcId = (value: unknown): value is JsonRpcId =>
  value === null || typeof value === 'string' || typeof value === 'number';

export const isJsonRpcRequestShape = (
  value: unknown,
): value is JsonRpcRequest => {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  if (
    candidate.jsonrpc !== JSON_RPC_VERSION ||
    typeof candidate.method !== 'string'
  ) {
    return false;
  }
  if (candidate.id === undefined) {
    return true;
  }
  return isJsonRpcId(candidate.id);
};
