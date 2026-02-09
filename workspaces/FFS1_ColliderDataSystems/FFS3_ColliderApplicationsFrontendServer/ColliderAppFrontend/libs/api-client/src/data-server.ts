import type { Application, AppNode, AppNodeTree, ColliderUser } from "./types";

const DEFAULT_BASE_URL = "http://localhost:8000";

export class DataServerClient {
  private baseUrl: string;

  constructor(baseUrl: string = DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async verifyAuth(): Promise<ColliderUser> {
    const res = await fetch(`${this.baseUrl}/api/v1/auth/verify`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(`Auth failed: ${res.status}`);
    return res.json();
  }

  async listApps(): Promise<Application[]> {
    const res = await fetch(`${this.baseUrl}/api/v1/apps/`);
    if (!res.ok) throw new Error(`Failed to list apps: ${res.status}`);
    return res.json();
  }

  async getApp(appId: string): Promise<Application> {
    const res = await fetch(`${this.baseUrl}/api/v1/apps/${appId}`);
    if (!res.ok) throw new Error(`Failed to get app: ${res.status}`);
    return res.json();
  }

  async getAppTree(appId: string): Promise<AppNodeTree[]> {
    const res = await fetch(
      `${this.baseUrl}/api/v1/apps/${appId}/nodes/tree`
    );
    if (!res.ok) throw new Error(`Failed to get tree: ${res.status}`);
    return res.json();
  }

  async getNode(appId: string, nodeId: string): Promise<AppNode> {
    const res = await fetch(
      `${this.baseUrl}/api/v1/apps/${appId}/nodes/${nodeId}`
    );
    if (!res.ok) throw new Error(`Failed to get node: ${res.status}`);
    return res.json();
  }

  async createNode(
    appId: string,
    body: {
      path: string;
      parent_id?: string;
      container?: Record<string, unknown>;
      metadata?: Record<string, unknown>;
    }
  ): Promise<AppNode> {
    const res = await fetch(`${this.baseUrl}/api/v1/apps/${appId}/nodes/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`Failed to create node: ${res.status}`);
    return res.json();
  }

  connectSSE(
    onEvent: (event: MessageEvent) => void,
    onError?: (error: Event) => void
  ): EventSource {
    const source = new EventSource(`${this.baseUrl}/api/v1/sse/`);
    source.onmessage = onEvent;
    if (onError) source.onerror = onError;
    return source;
  }
}
