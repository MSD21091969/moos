import type { Application, AppNodeTree, ColliderUser } from "~/types";

const DATA_SERVER_URL = "http://localhost:8000";

export async function verifyAuth(): Promise<ColliderUser> {
  const response = await fetch(`${DATA_SERVER_URL}/api/v1/auth/verify`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`Auth failed: ${response.status}`);
  return response.json();
}

export async function fetchApps(): Promise<Application[]> {
  const response = await fetch(`${DATA_SERVER_URL}/api/v1/apps/`);
  if (!response.ok) throw new Error(`Failed to fetch apps: ${response.status}`);
  return response.json();
}

export async function fetchTree(appId: string): Promise<AppNodeTree[]> {
  const response = await fetch(
    `${DATA_SERVER_URL}/api/v1/apps/${appId}/nodes/tree`
  );
  if (!response.ok) throw new Error(`Failed to fetch tree: ${response.status}`);
  return response.json();
}

export async function fetchContext(
  appId: string,
  path: string = "/"
): Promise<Record<string, unknown>> {
  const params = new URLSearchParams({ app_id: appId, path });
  const response = await fetch(
    `${DATA_SERVER_URL}/api/v1/context?${params.toString()}`
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
