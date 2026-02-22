import type { Application, AppNodeTree, ColliderUser } from "~/types";

const DATA_SERVER_URL = "http://localhost:8000";

// ---------------------------------------------------------------------------
// Auth token cache
// ---------------------------------------------------------------------------
let _token: string | null = null;

async function getToken(): Promise<string> {
  if (_token) return _token;
  const stored = await chrome.storage.local.get("collider_token");
  if (stored.collider_token) {
    _token = stored.collider_token;
    return _token;
  }
  return login();
}

async function login(): Promise<string> {
  const response = await fetch(`${DATA_SERVER_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: "Sam", password: "Sam" }),
  });
  if (!response.ok) throw new Error(`Login failed: ${response.status}`);
  const data = await response.json();
  _token = data.access_token;
  await chrome.storage.local.set({ collider_token: _token });
  return _token;
}

function authHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export async function verifyAuth(): Promise<ColliderUser> {
  const token = await getToken();
  const response = await fetch(`${DATA_SERVER_URL}/api/v1/users/me`, {
    headers: authHeaders(token),
  });
  if (!response.ok) {
    _token = null;
    await chrome.storage.local.remove("collider_token");
    throw new Error(`Auth failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchApps(): Promise<Application[]> {
  const token = await getToken();
  const response = await fetch(`${DATA_SERVER_URL}/api/v1/apps/`, {
    headers: authHeaders(token),
  });
  if (!response.ok) throw new Error(`Failed to fetch apps: ${response.status}`);
  return response.json();
}

export async function fetchTree(appId: string): Promise<AppNodeTree[]> {
  const token = await getToken();
  const response = await fetch(
    `${DATA_SERVER_URL}/api/v1/apps/${appId}/nodes/tree`,
    { headers: authHeaders(token) }
  );
  if (!response.ok) throw new Error(`Failed to fetch tree: ${response.status}`);
  return response.json();
}

export async function fetchContext(
  appId: string,
  path: string = "/"
): Promise<Record<string, unknown>> {
  const token = await getToken();
  const params = new URLSearchParams({ app_id: appId, path });
  const response = await fetch(
    `${DATA_SERVER_URL}/api/v1/context?${params.toString()}`,
    { headers: authHeaders(token) }
  );
  if (!response.ok)
    throw new Error(`Failed to fetch context: ${response.status}`);
  return response.json();
}

export function connectSSE(
  onEvent: (event: MessageEvent) => void,
  onError?: (error: Event) => void
): EventSource {
  const source = new EventSource(`${DATA_SERVER_URL}/api/v1/sse/`);

  source.onmessage = onEvent;

  source.addEventListener("context_update", (e) => {
    onEvent(e);
  });

  source.addEventListener("node_modified", (e) => {
    onEvent(e);
  });

  source.addEventListener("keepalive", () => {
    // No-op for keepalive
  });

  if (onError) {
    source.onerror = onError;
  }

  return source;
}

