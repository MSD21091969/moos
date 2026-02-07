/**
 * Collider API Client
 *
 * Type-safe API client for the Collider Data Server.
 */

export interface ColliderAPIConfig {
  baseUrl: string;
  token?: string;
}

export interface User {
  id: string;
  email: string;
  profile: {
    display_name?: string;
    avatar_url?: string;
  };
  created_at: string;
}

export interface Application {
  id: string;
  app_id: string;
  display_name?: string;
  domain?: string;
  root_node_id?: string;
  created_at: string;
  updated_at: string;
}

export interface AppPermission {
  id: string;
  user_id: string;
  application_id: string;
  can_read: boolean;
  can_write: boolean;
  is_admin: boolean;
}

export interface NodeContainer {
  manifest: Record<string, unknown>;
  instructions: string[];
  rules: string[];
  skills: string[];
  tools: unknown[];
  knowledge: string[];
  workflows: unknown[];
  configs: Record<string, unknown>;
}

export interface Node {
  id: string;
  application_id: string;
  parent_id?: string;
  path: string;
  container: NodeContainer;
  node_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: User;
  permissions: AppPermission[];
}

export interface SSEEvent {
  type: string;
  app_id?: string;
  node_path?: string;
  user_id?: string;
  data?: Record<string, unknown>;
}

export interface SSEConnection {
  close: () => void;
  readyState: () => number;
}

export class ColliderAPI {
  private baseUrl: string;
  private token?: string;

  constructor(config: ColliderAPIConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '');
    this.token = config.token;
  }

  setToken(token: string | undefined): void {
    this.token = token;
  }

  private async fetch<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new APIError(
        error.detail || `HTTP ${response.status}`,
        response.status,
        error
      );
    }

    return response.json();
  }

  // Auth endpoints
  async verifyToken(idToken: string): Promise<AuthResponse> {
    return this.fetch<AuthResponse>('/api/v1/auth/verify', {
      method: 'POST',
      body: JSON.stringify({ id_token: idToken }),
    });
  }

  // Application endpoints
  async listApplications(): Promise<Application[]> {
    return this.fetch<Application[]>('/api/v1/apps');
  }

  async getApplication(appId: string): Promise<Application> {
    return this.fetch<Application>(`/api/v1/apps/${appId}`);
  }

  async createApplication(data: {
    app_id: string;
    display_name?: string;
  }): Promise<Application> {
    return this.fetch<Application>('/api/v1/apps', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteApplication(appId: string): Promise<void> {
    await this.fetch(`/api/v1/apps/${appId}`, { method: 'DELETE' });
  }

  // Node endpoints
  async getNode(appId: string, path: string): Promise<Node> {
    return this.fetch<Node>(
      `/api/v1/apps/${appId}/nodes?path=${encodeURIComponent(path)}`
    );
  }

  async getNodeTree(appId: string): Promise<Node[]> {
    return this.fetch<Node[]>(`/api/v1/apps/${appId}/nodes/tree`);
  }

  async getResolvedContainer(
    appId: string,
    path: string
  ): Promise<{ path: string; container: NodeContainer; ancestry: string[] }> {
    return this.fetch(`/api/v1/apps/${appId}/nodes/resolved?path=${encodeURIComponent(path)}`);
  }

  async createNode(
    appId: string,
    data: {
      path: string;
      parent_id?: string;
      container?: Partial<NodeContainer>;
      node_metadata?: Record<string, unknown>;
    }
  ): Promise<Node> {
    return this.fetch<Node>(`/api/v1/apps/${appId}/nodes`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateNode(
    appId: string,
    nodeId: string,
    data: {
      container?: Partial<NodeContainer>;
      node_metadata?: Record<string, unknown>;
    }
  ): Promise<Node> {
    return this.fetch<Node>(`/api/v1/apps/${appId}/nodes/${nodeId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Secrets endpoints
  async listAppSecrets(appId: string): Promise<{ name: string; scope: string }[]> {
    return this.fetch(`/api/v1/secrets/app/${appId}`);
  }

  async setAppSecret(appId: string, name: string, value: string): Promise<void> {
    await this.fetch(`/api/v1/secrets/app/${appId}`, {
      method: 'POST',
      body: JSON.stringify({ name, value }),
    });
  }

  async deleteAppSecret(appId: string, name: string): Promise<void> {
    await this.fetch(`/api/v1/secrets/app/${appId}/${name}`, {
      method: 'DELETE',
    });
  }

  async validateSecrets(container: NodeContainer): Promise<{
    required: string[];
    missing: string[];
    valid: boolean;
  }> {
    return this.fetch('/api/v1/secrets/validate', {
      method: 'POST',
      body: JSON.stringify(container),
    });
  }

  // SSE (Server-Sent Events) streaming
  createSSE(onEvent: (event: SSEEvent) => void): SSEConnection {
    const url = `${this.baseUrl}/api/v1/sse`;
    const eventSource = new EventSource(
      this.token ? `${url}?token=${encodeURIComponent(this.token)}` : url
    );

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as SSEEvent;
        onEvent(data);
      } catch {
        console.warn('[SSE] Failed to parse event:', e.data);
      }
    };

    eventSource.onerror = () => {
      console.warn('[SSE] Connection error, will retry...');
    };

    return {
      close: () => eventSource.close(),
      readyState: () => eventSource.readyState,
    };
  }
}

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Factory function
export function createColliderAPI(config: ColliderAPIConfig): ColliderAPI {
  return new ColliderAPI(config);
}
