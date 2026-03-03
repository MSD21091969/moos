/**
 * Collider REST API Client
 *
 * Thin wrapper around fetch for the DataServer (:8000) and AgentRunner (:8004).
 * Uses localStorage auth token (same pattern as ffs6).
 */

const DATA_SERVER = import.meta.env.VITE_DATA_SERVER_URL ?? "http://localhost:8000";
const AGENT_RUNNER = import.meta.env.VITE_AGENT_RUNNER_URL ?? "http://localhost:8004";
const MVP_USERNAME = import.meta.env.VITE_MVP_USERNAME ?? "Sam";
const MVP_PASSWORD = import.meta.env.VITE_MVP_PASSWORD ?? "Sam";

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = localStorage.getItem("auth_token");
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function authedFetch(url: string, init?: RequestInit): Promise<Response> {
  const first = await fetch(url, {
    ...(init ?? {}),
    headers: {
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  });

  if (first.status !== 401) {
    return first;
  }

  await login(MVP_USERNAME, MVP_PASSWORD);

  return fetch(url, {
    ...(init ?? {}),
    headers: {
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  });
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function login(username: string, password: string): Promise<string> {
  const resp = await fetch(`${DATA_SERVER}/api/v1/users/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!resp.ok) throw new Error(`Login failed: ${resp.status}`);
  const data = await resp.json();
  localStorage.setItem("auth_token", data.access_token);
  return data.access_token;
}

export async function getCurrentUser(): Promise<{ id: string; username: string; role: string }> {
  const resp = await authedFetch(`${DATA_SERVER}/api/v1/users/me`);
  if (!resp.ok) throw new Error(`Get user failed: ${resp.status}`);
  return resp.json();
}

// ---------------------------------------------------------------------------
// Applications
// ---------------------------------------------------------------------------

export interface Application {
  id: string;
  name: string;
  description?: string;
}

export async function listApps(): Promise<Application[]> {
  const resp = await authedFetch(`${DATA_SERVER}/api/v1/apps/`);
  if (!resp.ok) throw new Error(`List apps failed: ${resp.status}`);
  return resp.json();
}

// ---------------------------------------------------------------------------
// Node Tree
// ---------------------------------------------------------------------------

export interface TreeNode {
  id: string;
  path: string;
  children: TreeNode[];
  metadata_?: Record<string, unknown>;
  container?: {
    config?: { domain?: string };
    instructions?: string[];
    skills?: Array<{ name: string }>;
    tools?: Array<{ name: string }>;
  };
}

export async function getNodeTree(appId: string): Promise<TreeNode[]> {
  const resp = await authedFetch(`${DATA_SERVER}/api/v1/apps/${appId}/nodes/tree`);
  if (!resp.ok) throw new Error(`Get tree failed: ${resp.status}`);
  return resp.json();
}

// ---------------------------------------------------------------------------
// Agent Session (via AgentRunner)
// ---------------------------------------------------------------------------

export interface SessionResponse {
  session_id: string;
  nanoclaw_ws_url: string;
  preview?: {
    agents_md: string;
    soul_md: string;
    tools_md: string;
    skills: Array<{ name: string; description: string }>;
  };
}

export async function createAgentSession(params: {
  role: string;
  app_id: string;
  node_ids: string[];
  vector_query?: string;
  visibility_filter?: string[];
  inherit_ancestors?: boolean;
}): Promise<SessionResponse> {
  const resp = await authedFetch(`${AGENT_RUNNER}/agent/session`, {
    method: "POST",
    body: JSON.stringify({
      ...params,
      visibility_filter: params.visibility_filter ?? ["global", "group"],
      inherit_ancestors: params.inherit_ancestors ?? true,
    }),
  });
  if (!resp.ok) throw new Error(`Create session failed: ${resp.status}`);
  return resp.json();
}
