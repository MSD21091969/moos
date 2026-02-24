/**
 * SDK Anthropic Agent
 *
 * Replaces the CLI-based container-runner with a programmatic agent loop
 * using the Anthropic TypeScript SDK Messages API.
 *
 * Key differences from the CLI approach:
 *   - System prompt injected directly (no CLAUDE.md file)
 *   - Skills injected as system prompt sections (no SKILL.md files)
 *   - Tools registered programmatically (no .mcp.json file)
 *   - Mid-session context injection via injectContext()
 *   - Conversation history managed in-memory + SQLite persistence
 *   - Streaming events mapped to the same AgentEvent type
 */

import Anthropic from "@anthropic-ai/sdk";
import { buildSystemPrompt, applyDeltaToContext } from "./prompt-builder.js";
import {
  ToolExecutor,
  type ToolUseBlock,
  type ToolResultBlock,
} from "./tool-executor.js";
import type {
  ComposedContext,
  ContextDelta,
  SdkSessionConfig,
} from "./types.js";
import type { IAgentSession } from "./agent-session.js";
import type { AgentEvent } from "../event-parser.js";
import pino from "pino";

const log = pino({ name: "anthropic-agent" });

const DEFAULT_MODEL = "claude-sonnet-4-20250514";
const DEFAULT_MAX_TOKENS = 8192;
const DEFAULT_MAX_TURNS = 25;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ConversationMessage {
  role: "user" | "assistant";
  content: MessageContent;
}

type MessageContent = string | ContentBlock[];

type ContentBlock =
  | { type: "text"; text: string }
  | { type: "tool_use"; id: string; name: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool_use_id: string; content: string; is_error?: boolean }
  | { type: "thinking"; thinking: string };

interface AgentSession {
  id: string;
  context: ComposedContext;
  systemPrompt: string;
  model: string;
  maxTokens: number;
  maxTurns: number;
  history: ConversationMessage[];
  toolExecutor: ToolExecutor;
  status: "idle" | "running" | "error";
}

// ---------------------------------------------------------------------------
// Agent
// ---------------------------------------------------------------------------

export class AnthropicAgent implements IAgentSession {
  private client: Anthropic;
  private sessions: Map<string, AgentSession> = new Map();

  constructor(opts?: { apiKey?: string }) {
    this.client = new Anthropic({
      apiKey: opts?.apiKey ?? process.env.ANTHROPIC_API_KEY,
    });
  }

  // -----------------------------------------------------------------------
  // Session lifecycle
  // -----------------------------------------------------------------------

  /**
   * Create a new agent session from composed context.
   */
  createSession(config: SdkSessionConfig): string {
    const systemPrompt = buildSystemPrompt(config.context);
    const mcpUrl =
      config.context.mcp_servers[0]?.url ??
      process.env.COLLIDER_MCP_URL ??
      "http://localhost:8001/mcp/sse";

    const toolExecutor = new ToolExecutor({ mcpUrl });
    toolExecutor.setToolSchemas(config.context.tool_schemas);

    const session: AgentSession = {
      id: config.sessionId,
      context: config.context,
      systemPrompt,
      model: config.model ?? DEFAULT_MODEL,
      maxTokens: config.maxTokens ?? DEFAULT_MAX_TOKENS,
      maxTurns: config.maxTurns ?? DEFAULT_MAX_TURNS,
      history: [],
      toolExecutor,
      status: "idle",
    };

    this.sessions.set(config.sessionId, session);
    log.info(
      {
        sessionId: config.sessionId,
        model: session.model,
        skills: config.context.skills.length,
        tools: config.context.tool_schemas.length,
      },
      "SDK session created",
    );

    return config.sessionId;
  }

  /**
   * Resume a session by restoring conversation history.
   */
  resumeSession(
    sessionId: string,
    history: ConversationMessage[],
  ): void {
    const session = this.getSession(sessionId);
    session.history = history;
    log.info(
      { sessionId, messageCount: history.length },
      "Session resumed",
    );
  }

  /**
   * Inject a context delta mid-session —
   * updates the system prompt for the next turn.
   */
  injectContext(sessionId: string, delta: ContextDelta): void {
    const session = this.getSession(sessionId);
    session.context = applyDeltaToContext(session.context, delta);
    session.systemPrompt = buildSystemPrompt(session.context);

    // Update tool schemas if they changed
    if (delta.type === "tool_schema" || delta.type === "full_replace") {
      session.toolExecutor.setToolSchemas(session.context.tool_schemas);
    }

    log.info({ sessionId, deltaType: delta.type }, "Context injected");
  }

  /**
   * Terminate a session and free resources.
   */
  terminateSession(sessionId: string): void {
    this.sessions.delete(sessionId);
    log.info({ sessionId }, "Session terminated");
  }

  /**
   * Get current conversation history for persistence.
   */
  getHistory(sessionId: string): ConversationMessage[] {
    return this.getSession(sessionId).history;
  }

  hasHistory(sessionId: string): boolean {
    return this.getHistory(sessionId).length > 0;
  }

  // -----------------------------------------------------------------------
  // Message handling — agentic loop
  // -----------------------------------------------------------------------

  /**
   * Send a user message and run the agentic loop.
   * Yields AgentEvent objects as the agent processes the request.
   *
   * The agentic loop:
   *   1. Send message to Claude with tools
   *   2. If response contains tool_use → execute tools → append results → goto 1
   *   3. If response is pure text → yield text_delta → done
   */
  async *sendMessage(
    sessionId: string,
    message: string,
  ): AsyncGenerator<AgentEvent> {
    const session = this.getSession(sessionId);

    if (session.status === "running") {
      yield { kind: "error", message: "Session is already processing a message" };
      return;
    }

    session.status = "running";

    // Add user message to history
    session.history.push({ role: "user", content: message });

    try {
      let turns = 0;

      while (turns < session.maxTurns) {
        turns++;

        // Call Messages API with streaming
        const events = this.streamCompletion(session);
        let assistantContent: ContentBlock[] = [];
        const toolUseBlocks: ToolUseBlock[] = [];

        for await (const event of events) {
          // Collect content blocks for history
          if (event.kind === "text_delta") {
            // Accumulate text for history (we'll finalize below)
          } else if (event.kind === "tool_use_start") {
            try {
              const args = JSON.parse(event.args);
              toolUseBlocks.push({
                id: `tool_${turns}_${toolUseBlocks.length}`,
                name: event.name,
                input: args,
              });
            } catch {
              toolUseBlocks.push({
                id: `tool_${turns}_${toolUseBlocks.length}`,
                name: event.name,
                input: {},
              });
            }
          }

          // Forward all events to caller
          yield event;
        }

        // Get the full response to build history
        assistantContent = await this.getFullResponse(session);

        // Store assistant message in history
        session.history.push({
          role: "assistant",
          content: assistantContent,
        });

        // Check if we need to execute tools
        const toolUses = assistantContent.filter(
          (b): b is ContentBlock & { type: "tool_use" } => b.type === "tool_use",
        );

        if (toolUses.length === 0) {
          // No tool calls — agent is done
          break;
        }

        // Execute tools
        const toolResults: ToolResultBlock[] =
          await session.toolExecutor.executeAll(
            toolUses.map((t) => ({
              id: t.id,
              name: t.name,
              input: t.input,
            })),
          );

        // Emit tool results as events
        for (const result of toolResults) {
          yield {
            kind: "tool_result",
            name: result.tool_use_id,
            result: result.content,
          };
        }

        // Add tool results to history as a user message (API requirement)
        session.history.push({
          role: "user",
          content: toolResults.map((r) => ({
            type: "tool_result" as const,
            tool_use_id: r.tool_use_id,
            content: r.content,
            is_error: r.is_error,
          })),
        });
      }

      if (turns >= session.maxTurns) {
        yield {
          kind: "error",
          message: `Agent reached maximum turns (${session.maxTurns})`,
        };
      }

      yield { kind: "message_end" };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      log.error({ sessionId, err: message }, "Agent error");
      yield { kind: "error", message };
      yield { kind: "message_end" };
    } finally {
      session.status = "idle";
    }
  }

  // -----------------------------------------------------------------------
  // Streaming completion
  // -----------------------------------------------------------------------

  private async *streamCompletion(
    session: AgentSession,
  ): AsyncGenerator<AgentEvent> {
    const tools = session.toolExecutor.getApiTools();

    const params: Anthropic.MessageCreateParamsStreaming = {
      model: session.model,
      max_tokens: session.maxTokens,
      system: session.systemPrompt,
      messages: session.history.map((m) => ({
        role: m.role,
        content: m.content as Anthropic.MessageCreateParams["messages"][number]["content"],
      })),
      stream: true,
      ...(tools.length > 0 ? { tools: tools as Anthropic.Tool[] } : {}),
    };

    const stream = this.client.messages.stream(params);

    // Track accumulated content for the full response
    let currentText = "";

    stream.on("text", (text: string) => {
      currentText += text;
    });

    for await (const event of stream) {
      if (event.type === "content_block_start") {
        if (event.content_block.type === "tool_use") {
          yield {
            kind: "tool_use_start",
            name: event.content_block.name,
            args: JSON.stringify(event.content_block.input ?? {}),
          };
        } else if (event.content_block.type === "thinking") {
          yield {
            kind: "thinking",
            text: (event.content_block as { thinking?: string }).thinking ?? "",
          };
        }
      } else if (event.type === "content_block_delta") {
        const delta = event.delta as unknown as Record<string, unknown>;
        if (delta.type === "text_delta" && typeof delta.text === "string") {
          yield { kind: "text_delta", text: delta.text };
        } else if (
          delta.type === "thinking_delta" &&
          typeof delta.thinking === "string"
        ) {
          yield { kind: "thinking", text: delta.thinking };
        } else if (
          delta.type === "input_json_delta" &&
          typeof delta.partial_json === "string"
        ) {
          // Tool input streaming — accumulate but don't emit as event
        }
      }
    }

    // Store the final message for history extraction
    const finalMessage = await stream.finalMessage();
    (session as unknown as { _lastResponse: Anthropic.Message })._lastResponse =
      finalMessage;
  }

  /**
   * Extract the full response content blocks from the last completion.
   */
  private async getFullResponse(
    session: AgentSession,
  ): Promise<ContentBlock[]> {
    const response = (
      session as unknown as { _lastResponse?: Anthropic.Message }
    )._lastResponse;
    if (!response) return [];

    return response.content.map((block: Anthropic.ContentBlock) => {
      if (block.type === "text") {
        return { type: "text" as const, text: block.text };
      } else if (block.type === "tool_use") {
        return {
          type: "tool_use" as const,
          id: block.id,
          name: block.name,
          input: block.input as Record<string, unknown>,
        };
      }
      // Thinking blocks
      return {
        type: "thinking" as const,
        thinking: (block as { thinking?: string }).thinking ?? "",
      };
    });
  }

  // -----------------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------------

  private getSession(sessionId: string): AgentSession {
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    return session;
  }
}
