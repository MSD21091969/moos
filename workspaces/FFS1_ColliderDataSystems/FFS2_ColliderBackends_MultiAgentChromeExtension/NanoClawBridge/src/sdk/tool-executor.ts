/**
 * SDK Tool Executor
 *
 * Routes tool_use content blocks from the Anthropic Messages API to the
 * appropriate execution backend:
 *
 *   - Collider tools → HTTP POST to GraphToolServer MCP endpoint at :8001
 *   - Built-in tools  → local execution (future: file, exec, browser)
 *
 * Returns results formatted for the Messages API tool_result content block.
 */

import type { ToolSchema } from "./types.js";
import pino from "pino";

const log = pino({ name: "tool-executor" });

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ToolUseBlock {
  id: string;
  name: string;
  input: Record<string, unknown>;
}

export interface ToolResultBlock {
  type: "tool_result";
  tool_use_id: string;
  content: string;
  is_error?: boolean;
}

// ---------------------------------------------------------------------------
// Executor
// ---------------------------------------------------------------------------

export class ToolExecutor {
  private mcpUrl: string;
  private toolSchemas: Map<string, ToolSchema> = new Map();
  private authToken: string | null = null;

  constructor(opts: { mcpUrl: string; authToken?: string }) {
    this.mcpUrl = opts.mcpUrl;
    this.authToken = opts.authToken ?? null;
  }

  /**
   * Register available tool schemas. Used to validate tool calls and
   * to build the `tools` parameter for the Messages API.
   */
  setToolSchemas(schemas: ToolSchema[]): void {
    this.toolSchemas.clear();
    for (const schema of schemas) {
      this.toolSchemas.set(schema.function.name, schema);
    }
  }

  /**
   * Get tool definitions formatted for the Anthropic Messages API.
   */
  getApiTools(): Array<{
    name: string;
    description: string;
    input_schema: Record<string, unknown>;
  }> {
    return Array.from(this.toolSchemas.values()).map((schema) => ({
      name: schema.function.name,
      description: schema.function.description,
      input_schema: schema.function.parameters,
    }));
  }

  /**
   * Execute a tool_use block and return a tool_result block.
   * Routes to MCP endpoint or local handler based on tool name.
   */
  async execute(block: ToolUseBlock): Promise<ToolResultBlock> {
    log.info({ tool: block.name, id: block.id }, "Executing tool");

    try {
      // Route to MCP endpoint via HTTP POST (JSON-RPC to GraphToolServer)
      const result = await this.executeMcpTool(block);
      return {
        type: "tool_result",
        tool_use_id: block.id,
        content: typeof result === "string" ? result : JSON.stringify(result),
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      log.error({ tool: block.name, err: message }, "Tool execution failed");
      return {
        type: "tool_result",
        tool_use_id: block.id,
        content: `Error: ${message}`,
        is_error: true,
      };
    }
  }

  /**
   * Execute multiple tool_use blocks in parallel.
   */
  async executeAll(blocks: ToolUseBlock[]): Promise<ToolResultBlock[]> {
    return Promise.all(blocks.map((b) => this.execute(b)));
  }

  // -----------------------------------------------------------------------
  // MCP tool execution via HTTP
  // -----------------------------------------------------------------------

  private async executeMcpTool(block: ToolUseBlock): Promise<unknown> {
    // The DataServer exposes tool execution at /execution/tool/{name}
    // which internally routes to GraphToolServer.
    const dataServerUrl =
      process.env.COLLIDER_DATA_SERVER_URL ?? "http://localhost:8000";
    const url = `${dataServerUrl}/execution/tool/${encodeURIComponent(block.name)}`;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (this.authToken) {
      headers["Authorization"] = `Bearer ${this.authToken}`;
    }

    const resp = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(block.input),
    });

    if (!resp.ok) {
      const body = await resp.text().catch(() => "");
      throw new Error(
        `Tool ${block.name} failed (${resp.status}): ${body.slice(0, 500)}`,
      );
    }

    return resp.json();
  }
}
