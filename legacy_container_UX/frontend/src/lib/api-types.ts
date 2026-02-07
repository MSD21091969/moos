/**
 * Backend API Types (Refined from OpenAPI spec)
 * Source: generated-api-types.ts (auto-generated, do not edit that file)
 * This file: Manually maintained exports for cleaner imports
 *
 * NOTE: Backend OpenAPI doesn't expose typed schemas for custom tools/agents yet.
 * Using manual type definitions until backend adds schemas to openapi-spec.json.
 */

// ===== User-Level Custom Tool Definitions =====

// Manual definitions (backend doesn't expose these schemas yet)
export interface CustomToolDefinition {
  tool_id: string
  user_id: string
  name: string
  description: string
  type: 'builtin'  // Only builtin tool wrapping allowed
  builtin_tool_name: string  // Which built-in tool this wraps
  config: Record<string, unknown>  // Custom configuration
  tags: string[]
  created_at: string
  updated_at: string
  tier_required?: 'FREE' | 'PRO' | 'ENTERPRISE'
  metadata?: Record<string, unknown>
}

export interface CreateToolPayload {
  name: string
  description: string
  builtin_tool_name: string
  config: Record<string, unknown>
  tags?: string[]
  metadata?: Record<string, unknown>
}

// ===== User-Level Custom Agent Definitions =====

export interface CustomAgentDefinition {
  agent_id: string
  user_id: string
  name: string
  description: string
  system_prompt: string
  model?: string  // e.g., 'gpt-4', 'claude-3-opus'
  tags: string[]
  tier_required?: 'FREE' | 'PRO' | 'ENTERPRISE'
  created_at: string
  updated_at: string
  metadata?: Record<string, unknown>
}

export interface CreateAgentPayload {
  name: string
  description: string
  system_prompt: string
  model?: string
  tags?: string[]
  metadata?: Record<string, unknown>
}

export interface UpdateAgentPayload {
  name?: string
  description?: string
  system_prompt?: string
  model?: string
  tags?: string[]
  metadata?: Record<string, unknown>
}

// ===== Session Tool Instances =====

export interface SessionToolInstance {
  instance_id: string  // tool_inst_XXXXXXXXXXXX
  tool_id: string  // References system/user-global tool
  session_id: string
  display_name: string
  config_overrides?: Record<string, unknown>  // Override user's default config
  created_at: string
  metadata?: Record<string, unknown>
}

export interface AddToolInstanceRequest {
  tool_id: string
  tool_name: string
  display_name: string
  config_overrides?: Record<string, unknown>
  metadata?: Record<string, unknown>
}

// ===== Session Agent Instances =====

export interface SessionAgentInstance {
  instance_id: string  // agent_inst_XXXXXXXXXXXX
  agent_id: string  // References system/user-global agent
  session_id: string
  display_name: string
  is_active: boolean  // Only one active agent per session
  system_prompt_override?: string
  model_override?: string
  created_at: string
  metadata?: Record<string, unknown>
}

export interface AddAgentInstanceRequest {
  agent_id: string
  display_name: string
  system_prompt_override?: string
  model_override?: string
  set_as_active?: boolean  // Auto-activate this agent
  metadata?: Record<string, unknown>
}

// ===== Discovery Types (System + User-Global Tools/Agents) =====

export interface ToolDefinition {
  name: string
  description: string
  category: 'export' | 'text' | 'transform' | 'custom'
  is_system: boolean  // true for builtin, false for user custom
  tool_id?: string  // Present if user custom tool
  config_schema?: Record<string, unknown>  // JSON schema for config
  tier_required?: 'FREE' | 'PRO' | 'ENTERPRISE'
  tags: string[]
}

export interface AgentDefinition {
  agent_id: string
  name: string
  description: string
  is_system: boolean  // true for builtin, false for user custom
  tier_required?: 'FREE' | 'PRO' | 'ENTERPRISE'
  tags: string[]
}

// ===== Tier & Permission Types =====

export type Tier = 'FREE' | 'PRO' | 'ENTERPRISE'

export interface TierFeatures {
  tier: Tier
  custom_tools_allowed: boolean
  custom_agents_allowed: boolean
  max_custom_tools: number
  max_custom_agents: number
  max_session_tools: number
  max_session_agents: number
  quota_daily: number
}

export interface TierLimits {
  current_custom_tools: number
  current_custom_agents: number
  max_custom_tools: number
  max_custom_agents: number
}

// ===== Tool Execution Types =====

export interface ToolExecutionResponse {
  result: unknown
  execution_time_ms: number
  tool_name: string
  session_id: string
  instance_id: string
  timestamp: string
}

// ===== Existing Generated Types =====
// Manual definitions (backend OpenAPI has generic schemas)

export interface Session {
  session_id: string;
  user_id: string;
  title: string;
  status: 'active' | 'completed' | 'expired' | 'archived';
  session_type: 'chat' | 'analysis' | 'workflow' | 'simulation';
  tags: string[];
  created_at: string;
  updated_at: string;
  expires_at?: string;
  message_count?: number;
  metadata?: Record<string, unknown>;
  parent_session_id?: string;
}

export interface SessionCreate {
  title: string;
  session_type?: 'chat' | 'analysis' | 'workflow' | 'simulation';
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface SessionUpdate {
  title?: string;
  status?: 'active' | 'completed' | 'expired' | 'archived';
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface Message {
  message_id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface ErrorResponse {
  detail: string;
  error_code?: string;
}

export interface DatasourceAttachment {
  attachment_id: string;
  session_id: string;
  name: string;
  type: string;
  config: Record<string, unknown>;
  created_at: string;
}

export interface AddDatasourcePayload {
  name: string;
  type: string;
  config: Record<string, unknown>;
}

export interface UpdateDatasourcePayload {
  name?: string;
  config?: Record<string, unknown>;
}

export interface ACLAttachment {
  attachment_id: string;
  session_id: string;
  user_id: string;
  role: 'viewer' | 'editor' | 'owner';
  created_at: string;
}

export interface AddACLPayload {
  user_id: string;
  role: 'viewer' | 'editor' | 'owner';
}

export interface UpdateACLPayload {
  role: 'viewer' | 'editor' | 'owner';
}

// UserInfo type
export interface UserInfo {
  user_id: string;
  email: string;
  tier: Tier;
  quota_remaining: number;
  created_at: string;
}

// ===== Utility Types =====

export interface ApiResponse<T> {
  data: T;
  timestamp: string;
  request_id?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}
