export interface NodeContainer {
  manifest: Record<string, unknown>;
  instructions: string[];
  rules: string[];
  skills: string[];
  tools: Record<string, unknown>[];
  knowledge: string[];
  workflows: Record<string, unknown>[];
  configs: Record<string, unknown>;
}

export interface Application {
  id: string;
  owner_id: string | null;
  display_name: string | null;
  config: Record<string, unknown>;
  root_node_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppNode {
  id: string;
  application_id: string;
  parent_id: string | null;
  path: string;
  container: NodeContainer;
  metadata_: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AppNodeTree {
  id: string;
  path: string;
  container: NodeContainer;
  metadata_: Record<string, unknown>;
  children: AppNodeTree[];
}

export interface AppPermission {
  id: string;
  user_id: string;
  application_id: string;
  can_read: boolean;
  can_write: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface ColliderUser {
  id: string;
  email: string;
  firebase_uid: string;
  profile: Record<string, unknown>;
  container: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TabContext {
  tabId: number;
  url: string;
  title: string;
  dom_snapshot?: string;
  active_app_id?: string;
  active_node_path?: string;
}

export interface MainContext {
  user: ColliderUser | null;
  applications: Application[];
  permissions: AppPermission[];
  activeTabId: number | null;
  tabs: Map<number, TabContext>;
}

// ContextSet + WorkspaceBrowser types
export type ContextRole = "superadmin" | "collider_admin" | "app_admin" | "app_user";

export interface DiscoveredTool {
  name: string;
  description: string;
  score: number;
  origin_node_id: string;
}

export interface SessionPreview {
  node_count: number;
  skill_count: number;
  tool_count: number;
  role: string;
  vector_matches: number;
}

export interface SessionResponse {
  session_id: string;
  preview: SessionPreview;
  nanoclaw_ws_url?: string | null;  // Direct WebSocket URL for NanoClawBridge chat
}

export type ColliderMessageType =
  | "INIT"
  | "AUTH_VERIFY"
  | "FETCH_APPS"
  | "FETCH_TREE"
  | "DOM_QUERY"
  | "WORKFLOW_EXECUTE"
  | "TOOL_SEARCH"
  | "CONTEXT_UPDATE"
  | "NATIVE_MESSAGE"
  | "SSE_EVENT";

export interface ColliderMessage {
  type: ColliderMessageType;
  payload?: unknown;
  tabId?: number;
  requestId?: string;
}

export interface ColliderResponse {
  success: boolean;
  data?: unknown;
  error?: string;
  requestId?: string;
}
