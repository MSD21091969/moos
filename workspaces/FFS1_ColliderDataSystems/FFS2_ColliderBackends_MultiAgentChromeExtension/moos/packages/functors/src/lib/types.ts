import { type ToolExecutionResult } from '@moos/core';

export interface Message {
  role: 'user' | 'assistant';
  content: string | ContentBlock[];
}

export interface ContentBlock {
  type: 'text' | 'tool_use' | 'tool_result';
  text?: string;
  id?: string;
  name?: string;
  input?: unknown;
  tool_use_id?: string;
  content?: string;
}

export interface ToolSchema {
  name: string;
  description?: string;
  input_schema?: Record<string, unknown>;
}

export interface Prompt {
  system: string;
  messages: Message[];
  tools: ToolSchema[];
}

export interface ToolUse {
  id: string;
  name: string;
  input: unknown;
}

export type StopReason = 'end_turn' | 'tool_use' | 'max_tokens' | 'error';

export interface Completion {
  content: string;
  stopReason: StopReason;
  toolUses?: ToolUse[];
  usage?: { inputTokens: number; outputTokens: number };
}

export interface ProviderFunctor {
  readonly name: string;
  modelCall(prompt: Prompt): AsyncGenerator<Completion, void, void>;
}

export interface ExecutionFunctor {
  readonly name: string;
  toolExecute(toolUse: ToolUse): Promise<ToolExecutionResult>;
}
