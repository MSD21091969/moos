/**
 * SDK Agent Types
 *
 * Shared type definitions for the Anthropic SDK-based agent runtime.
 * These types bridge the Collider NodeContainer model (from gRPC/JSON)
 * to the Anthropic Messages API.
 */

// ---------------------------------------------------------------------------
// Context types — mirror Collider NodeContainer / AgentBootstrap fields
// ---------------------------------------------------------------------------

/** Skill definition as delivered from Collider backend (JSON, not SKILL.md). */
export interface SkillDefinition {
  name: string;
  description: string;
  emoji?: string;
  namespace?: string;
  version?: string;
  kind?: "procedural" | "navigation" | "workflow" | "composite";
  scope?: "local" | "inherited" | "composed" | "global";
  source_node_path?: string;
  source_node_id?: string;
  requires_bins?: string[];
  requires_env?: string[];
  inputs?: string[];
  outputs?: string[];
  depends_on?: string[];
  exposes_tools?: string[];
  child_skills?: string[];
  user_invocable: boolean;
  model_invocable: boolean;
  markdown_body: string;
  tool_ref?: string;
  invocation_policy?: "auto" | "confirm" | "disabled";
}

/** Tool schema in OpenAI-compatible function-calling format. */
export interface ToolSchema {
  type: "function";
  function: {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
  };
}

/** MCP server configuration (replaces .mcp.json file). */
export interface McpServerConfig {
  name: string;
  type: "sse" | "stdio";
  url?: string;
  command?: string;
  args?: string[];
}

/** Session metadata from the Collider AgentRunner. */
export interface SessionMeta {
  role: string;
  app_id: string;
  composed_nodes: string[];
  username?: string;
}

/** Full composed context delivered from AgentRunner (via gRPC or REST). */
export interface ComposedContext {
  /** Agent identity / instructions (from NodeContainer.instructions). */
  agents_md: string;
  /** Rules / guardrails (from NodeContainer.rules). */
  soul_md: string;
  /** Knowledge / reference docs (from NodeContainer.knowledge). */
  tools_md: string;
  /** Skill definitions from merged NodeContainers. */
  skills: SkillDefinition[];
  /** Tool schemas for function calling. */
  tool_schemas: ToolSchema[];
  /** MCP server configs. */
  mcp_servers: McpServerConfig[];
  /** Session metadata. */
  session_meta: SessionMeta;
}

// ---------------------------------------------------------------------------
// Context delta — for mid-session context injection
// ---------------------------------------------------------------------------

export type ContextDelta =
  | { type: "system_prompt"; section: "agents_md" | "soul_md" | "tools_md"; operation: "replace" | "append"; content: string }
  | { type: "skill"; operation: "add" | "update" | "remove"; skill: SkillDefinition }
  | { type: "tool_schema"; operation: "add" | "update" | "remove"; tool_schema: ToolSchema }
  | { type: "full_replace"; context: ComposedContext };

// ---------------------------------------------------------------------------
// Agent session types
// ---------------------------------------------------------------------------

/** Configuration for creating an SDK agent session. */
export interface SdkSessionConfig {
  sessionId: string;
  context: ComposedContext;
  model?: string;
  maxTokens?: number;
  maxTurns?: number;
}

/** Conversation message stored for resume. */
export interface StoredMessage {
  role: "user" | "assistant";
  content: string | ContentBlock[];
}

/** Anthropic content block shapes we handle. */
export type ContentBlock =
  | { type: "text"; text: string }
  | { type: "tool_use"; id: string; name: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool_use_id: string; content: string }
  | { type: "thinking"; thinking: string };
