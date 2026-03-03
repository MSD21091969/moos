import {
  JSON_RPC_VERSION,
  MCP_METHODS,
  type ToolExecutionResult,
} from '@moos/core';

import type {
  Completion,
  ExecutionFunctor,
  Message,
  Prompt,
  ProviderFunctor,
  ToolUse,
} from './types.js';

/** Extract the text content from the last user message in a messages array. */
function extractLastUserText(messages: Message[]): string {
  const last = messages[messages.length - 1];
  if (!last) return '';
  if (typeof last.content === 'string') return last.content;
  const textBlock = last.content.find((b) => b.type === 'text');
  return textBlock?.text ?? '';
}

// --- Test / stub providers ---

export class EchoProviderFunctor implements ProviderFunctor {
  readonly name = 'echo-provider' as const;

  async *modelCall(prompt: Prompt): AsyncGenerator<Completion, void, void> {
    const lastMessage = extractLastUserText(prompt.messages);
    yield {
      content: `echo:${lastMessage}`,
      stopReason: 'end_turn',
    };
  }
}

export class ToolFirstProviderFunctor implements ProviderFunctor {
  readonly name = 'tool-first-provider' as const;

  async *modelCall(prompt: Prompt): AsyncGenerator<Completion, void, void> {
    const firstTool = prompt.tools[0];
    if (firstTool) {
      yield {
        content: 'requesting tool execution',
        stopReason: 'tool_use',
        toolUses: [
          {
            id: 'tool-1',
            name: firstTool.name,
            input: { source: 'tool-first-provider' },
          },
        ],
      };
    }
    const lastMessage = extractLastUserText(prompt.messages);
    yield {
      content: `complete:${lastMessage}`,
      stopReason: 'end_turn',
    };
  }
}

// --- Execution functors ---

export class NoopExecutionFunctor implements ExecutionFunctor {
  readonly name = 'noop-executor' as const;

  async toolExecute(toolUse: ToolUse): Promise<ToolExecutionResult> {
    return {
      output: {
        acknowledged: true,
        tool: toolUse.name,
        input: toolUse.input,
      },
    };
  }
}

export class HttpExecutionFunctor implements ExecutionFunctor {
  readonly name = 'http-executor' as const;

  constructor(private readonly baseUrl: string) {}

  async toolExecute(toolUse: ToolUse): Promise<ToolExecutionResult> {
    const response = await fetch(`${this.baseUrl}/execute`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
      },
      body: JSON.stringify(toolUse),
    });
    if (!response.ok) {
      return {
        output: null,
        error: `http_${response.status}`,
      };
    }
    return (await response.json()) as ToolExecutionResult;
  }
}

export class McpJsonRpcExecutionFunctor implements ExecutionFunctor {
  readonly name = 'mcp-jsonrpc-executor' as const;

  constructor(
    private readonly baseUrl: string,
    private readonly fallback?: ExecutionFunctor,
  ) {}

  async toolExecute(toolUse: ToolUse): Promise<ToolExecutionResult> {
    try {
      const response = await fetch(`${this.baseUrl}/mcp/messages`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
        },
        body: JSON.stringify({
          jsonrpc: JSON_RPC_VERSION,
          id: toolUse.id,
          method: MCP_METHODS.toolsCall,
          params: {
            name: toolUse.name,
            input: toolUse.input,
          },
        }),
      });
      if (!response.ok) {
        return this.executeFallback(toolUse, `http_${response.status}`);
      }
      const payload = (await response.json()) as {
        result?: ToolExecutionResult;
        error?: { code: number };
      };
      if (payload.error) {
        return this.executeFallback(toolUse, `rpc_${payload.error.code}`);
      }
      if (!payload.result) {
        return this.executeFallback(toolUse, 'rpc_missing_result');
      }
      return payload.result;
    } catch {
      return this.executeFallback(toolUse, 'rpc_transport_error');
    }
  }

  private async executeFallback(
    toolUse: ToolUse,
    errorCode: string,
  ): Promise<ToolExecutionResult> {
    if (this.fallback) {
      return this.fallback.toolExecute(toolUse);
    }
    return {
      output: null,
      error: errorCode,
    };
  }
}
