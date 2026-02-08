/**
 * Coding Agent - Gemini 3 Pro with Thinking
 * 
 * Complex reasoning agent for code generation, analysis, and problem solving.
 * Uses extended thinking budget for high-quality responses.
 */

import { GoogleGenAI } from '@google/genai';
import type {
  CodingAgentConfig,
  CodingRequest,
  CodingResponse,
  CodeArtifact,
  FunctionDeclaration,
  ToolCall,
  AgentContext,
  AgentEvent,
  AgentEventHandler,
  TokenUsage,
} from './types';

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_MODEL = 'gemini-3-pro-preview';
const DEFAULT_THINKING_BUDGET = 24576; // Max tokens for thinking
const DEFAULT_TEMPERATURE = 1.0; // Recommended for Gemini 3

// ============================================================================
// Coding Agent Class
// ============================================================================

export class CodingAgent {
  private ai: GoogleGenAI | null = null;
  private eventHandler: AgentEventHandler | null = null;
  
  private config: CodingAgentConfig;
  private tools: FunctionDeclaration[] = [];
  private systemInstruction: string = '';

  constructor(apiKey: string, config?: Partial<CodingAgentConfig>) {
    this.ai = new GoogleGenAI({ apiKey });
    this.config = {
      model: config?.model ?? DEFAULT_MODEL,
      thinkingConfig: config?.thinkingConfig ?? { thinkingBudget: DEFAULT_THINKING_BUDGET },
      temperature: config?.temperature ?? DEFAULT_TEMPERATURE,
      tools: config?.tools,
    };
    if (config?.tools) this.tools = config.tools;
  }

  // ==========================================================================
  // Public API
  // ==========================================================================

  /**
   * Set event handler for agent lifecycle events
   */
  onEvent(handler: AgentEventHandler): void {
    this.eventHandler = handler;
  }

  /**
   * Update tools available to the coding agent
   */
  setTools(tools: FunctionDeclaration[]): void {
    this.tools = tools;
  }

  /**
   * Update system instruction
   */
  setSystemInstruction(instruction: string): void {
    this.systemInstruction = instruction;
  }

  /**
   * Generate a response for a coding task
   */
  async generate(request: CodingRequest): Promise<CodingResponse> {
    if (!this.ai) {
      throw new Error('Coding agent not initialized');
    }

    this.emit({ type: 'thinking', agent: 'coding' });

    try {
      // Build the full prompt with context
      const contents = this.buildContents(request);
      
      // Generate with thinking enabled
      const response = await this.ai.models.generateContent({
        model: this.config.model,
        contents,
        config: {
          temperature: this.config.temperature,
          thinkingConfig: {
            thinkingBudget: this.config.thinkingConfig.thinkingBudget,
          },
          // Tools with thought signatures for Gemini 3
          tools: this.tools.length > 0 ? [{ functionDeclarations: this.tools as any }] : undefined,
        },
      });

      return this.parseResponse(response);
    } catch (error) {
      this.emit({ type: 'error', agent: 'coding', error: error as Error });
      throw error;
    }
  }

  /**
   * Stream a response for a coding task
   */
  async *generateStream(request: CodingRequest): AsyncGenerator<Partial<CodingResponse>> {
    if (!this.ai) {
      throw new Error('Coding agent not initialized');
    }

    this.emit({ type: 'thinking', agent: 'coding' });

    try {
      const contents = this.buildContents(request);

      const stream = await this.ai.models.generateContentStream({
        model: this.config.model,
        contents,
        config: {
          temperature: this.config.temperature,
          thinkingConfig: {
            thinkingBudget: this.config.thinkingConfig.thinkingBudget,
          },
          tools: this.tools.length > 0 ? [{ functionDeclarations: this.tools as any }] : undefined,
        },
      });

      let accumulatedText = '';
      let accumulatedThinking = '';

      for await (const chunk of stream) {
        const candidate = chunk.candidates?.[0];
        if (!candidate?.content?.parts) continue;

        for (const part of candidate.content.parts) {
          // Handle thinking content (Gemini 3 includes this in a special format)
          if ('thought' in part && part.thought) {
            accumulatedThinking += part.thought;
            yield { thinking: accumulatedThinking };
          }

          // Handle text content
          if (part.text) {
            accumulatedText += part.text;
            yield { text: accumulatedText };
          }

          // Handle function calls
          if (part.functionCall) {
            const toolCall = this.functionCallToToolCall(part.functionCall);
            this.emit({ type: 'tool_call', agent: 'coding', call: toolCall });
            yield { toolCalls: [toolCall] };
          }
        }
      }

      // Extract artifacts from final text
      const artifacts = this.extractArtifacts(accumulatedText);
      if (artifacts.length > 0) {
        for (const artifact of artifacts) {
          this.emit({ type: 'artifact', agent: 'coding', artifact });
        }
        yield { artifacts };
      }
    } catch (error) {
      this.emit({ type: 'error', agent: 'coding', error: error as Error });
      throw error;
    }
  }

  // ==========================================================================
  // Private Methods
  // ==========================================================================

  private emit(event: AgentEvent): void {
    this.eventHandler?.(event);
  }

  private buildContents(request: CodingRequest): Array<{ role: string; parts: Array<{ text: string }> }> {
    const contents: Array<{ role: string; parts: Array<{ text: string }> }> = [];

    // Add system instruction as first user message (Gemini style)
    const systemParts: string[] = [];
    
    if (this.systemInstruction) {
      systemParts.push(this.systemInstruction);
    }

    // Add context
    if (request.context) {
      systemParts.push(this.formatContext(request.context));
    }

    // Add any existing artifacts as context
    if (request.artifacts && request.artifacts.length > 0) {
      systemParts.push(this.formatArtifacts(request.artifacts));
    }

    if (systemParts.length > 0) {
      contents.push({
        role: 'user',
        parts: [{ text: systemParts.join('\n\n') }],
      });
      contents.push({
        role: 'model',
        parts: [{ text: 'I understand the context. How can I help you?' }],
      });
    }

    // Add conversation history
    if (request.context?.messages) {
      for (const msg of request.context.messages) {
        if (msg.role === 'user' || msg.role === 'assistant') {
          contents.push({
            role: msg.role === 'assistant' ? 'model' : 'user',
            parts: [{ text: msg.content }],
          });
        }
      }
    }

    // Add the main prompt
    contents.push({
      role: 'user',
      parts: [{ text: request.prompt }],
    });

    return contents;
  }

  private formatContext(context: AgentContext): string {
    const parts: string[] = ['## Context'];

    if (context.workspaceState) {
      parts.push(`### Workspace`);
      parts.push(`- Current Session: ${context.workspaceState.currentSessionId ?? 'None'}`);
      parts.push(`- Selected Node: ${context.workspaceState.selectedNodeId ?? 'None'}`);
      parts.push(`- Breadcrumb: ${context.workspaceState.breadcrumb.map(b => b.label).join(' → ') || 'Root'}`);
    }

    if (context.canvasState) {
      parts.push(`### Canvas`);
      parts.push(`- Nodes: ${context.canvasState.nodes.length}`);
      parts.push(`- Edges: ${context.canvasState.edges.length}`);
      
      if (context.canvasState.nodes.length > 0 && context.canvasState.nodes.length <= 20) {
        parts.push(`- Node Details:`);
        for (const node of context.canvasState.nodes) {
          parts.push(`  - ${node.id}: ${node.type} "${node.label}"`);
        }
      }
    }

    if (context.systemContext) {
      parts.push(`### Additional Context`);
      parts.push(context.systemContext);
    }

    return parts.join('\n');
  }

  private formatArtifacts(artifacts: CodeArtifact[]): string {
    const parts: string[] = ['## Existing Artifacts'];

    for (const artifact of artifacts) {
      parts.push(`### ${artifact.filename ?? artifact.id} (${artifact.language})`);
      parts.push('```' + artifact.language);
      parts.push(artifact.content);
      parts.push('```');
    }

    return parts.join('\n');
  }

  private parseResponse(response: unknown): CodingResponse {
    // Type assertion for Gemini response structure
    const geminiResponse = response as {
      candidates?: Array<{
        content?: {
          parts?: Array<{
            text?: string;
            thought?: string;
            functionCall?: { name: string; args: Record<string, unknown> };
          }>;
        };
      }>;
      usageMetadata?: {
        promptTokenCount?: number;
        candidatesTokenCount?: number;
        thoughtsTokenCount?: number;
        totalTokenCount?: number;
      };
    };

    const candidate = geminiResponse.candidates?.[0];
    const parts = candidate?.content?.parts ?? [];

    let text = '';
    let thinking = '';
    const toolCalls: ToolCall[] = [];

    for (const part of parts) {
      if (part.thought) {
        thinking += part.thought;
      }
      if (part.text) {
        text += part.text;
      }
      if (part.functionCall) {
        toolCalls.push(this.functionCallToToolCall(part.functionCall));
      }
    }

    // Extract code artifacts from the response
    const artifacts = this.extractArtifacts(text);

    // Emit artifact events
    for (const artifact of artifacts) {
      this.emit({ type: 'artifact', agent: 'coding', artifact });
    }

    // Emit tool call events
    for (const call of toolCalls) {
      this.emit({ type: 'tool_call', agent: 'coding', call });
    }

    // Parse usage metadata
    const usage: TokenUsage | undefined = geminiResponse.usageMetadata
      ? {
          promptTokens: geminiResponse.usageMetadata.promptTokenCount ?? 0,
          completionTokens: geminiResponse.usageMetadata.candidatesTokenCount ?? 0,
          thinkingTokens: geminiResponse.usageMetadata.thoughtsTokenCount,
          totalTokens: geminiResponse.usageMetadata.totalTokenCount ?? 0,
        }
      : undefined;

    return {
      text,
      thinking: thinking || undefined,
      artifacts: artifacts.length > 0 ? artifacts : undefined,
      toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
      usage,
    };
  }

  private functionCallToToolCall(call: { name?: string; args?: Record<string, unknown> }): ToolCall {
    return {
      id: crypto.randomUUID(),
      type: 'function',
      function: {
        name: call.name ?? 'unknown',
        arguments: JSON.stringify(call.args ?? {}),
      },
    };
  }

  private extractArtifacts(text: string): CodeArtifact[] {
    const artifacts: CodeArtifact[] = [];
    
    // Match code blocks with optional filename
    // Pattern: ```language:filename or ```language
    const codeBlockRegex = /```(\w+)(?::([^\n]+))?\n([\s\S]*?)```/g;
    
    let match;
    while ((match = codeBlockRegex.exec(text)) !== null) {
      const [, language, filename, content] = match;
      
      // Skip if it's a small inline example
      if (content.trim().split('\n').length < 3) continue;

      artifacts.push({
        id: crypto.randomUUID(),
        type: 'code',
        language: language.toLowerCase(),
        filename: filename?.trim(),
        content: content.trim(),
      });
    }

    return artifacts;
  }
}

// ============================================================================
// Factory Function
// ============================================================================

export function createCodingAgent(
  apiKey: string,
  config?: Partial<CodingAgentConfig>
): CodingAgent {
  return new CodingAgent(apiKey, config);
}
