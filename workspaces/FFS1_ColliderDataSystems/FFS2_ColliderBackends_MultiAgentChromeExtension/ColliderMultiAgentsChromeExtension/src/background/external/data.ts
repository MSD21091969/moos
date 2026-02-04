/**
 * Data Server client - REST + SSE
 */

const DATA_SERVER_URL = "http://localhost:8000"

export interface AuthResponse {
  user: {
    id: string
    email: string
    profile: { display_name?: string }
    container: Record<string, unknown>
  }
  permissions: {
    id: string
    application_id: string
    can_read: boolean
    can_write: boolean
    is_admin: boolean
  }[]
}

export interface AppResponse {
  id: string
  app_id: string
  display_name: string
  root_node_id: string | null
}

export interface NodeResponse {
  id: string
  application_id: string
  parent_id: string | null
  path: string
  container: {
    manifest: Record<string, unknown>
    instructions: string[]
    rules: string[]
    skills: string[]
    tools: unknown[]
    knowledge: string[]
    workflows: unknown[]
    configs: Record<string, unknown>
  }
  metadata: Record<string, unknown>
}

/**
 * Verify auth token and get user data
 */
export async function verifyAuth(token: string): Promise<AuthResponse> {
  const res = await fetch(`${DATA_SERVER_URL}/api/v1/auth/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: token }),
  })
  if (!res.ok) throw new Error(`Auth failed: ${res.status}`)
  return res.json()
}

/**
 * List all applications
 */
export async function listApps(): Promise<AppResponse[]> {
  const res = await fetch(`${DATA_SERVER_URL}/api/v1/apps`)
  if (!res.ok) throw new Error(`Failed to list apps: ${res.status}`)
  return res.json()
}

/**
 * Get node by path
 */
export async function getNode(appId: string, path: string): Promise<NodeResponse> {
  const res = await fetch(
    `${DATA_SERVER_URL}/api/v1/apps/${appId}/nodes?path=${encodeURIComponent(path)}`
  )
  if (!res.ok) throw new Error(`Failed to get node: ${res.status}`)
  return res.json()
}

/**
 * Get all nodes for an app
 */
export async function getNodeTree(appId: string): Promise<NodeResponse[]> {
  const res = await fetch(`${DATA_SERVER_URL}/api/v1/apps/${appId}/nodes/tree`)
  if (!res.ok) throw new Error(`Failed to get node tree: ${res.status}`)
  return res.json()
}

/**
 * SSE connection for real-time updates
 */
export function connectSSE(onEvent: (event: { type: string; data: unknown }) => void): EventSource {
  const eventSource = new EventSource(`${DATA_SERVER_URL}/api/v1/sse`)
  
  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      onEvent({ type: e.type || "message", data })
    } catch {
      onEvent({ type: e.type || "message", data: e.data })
    }
  }
  
  eventSource.onerror = (e) => {
    console.error("SSE error:", e)
  }
  
  return eventSource
}
