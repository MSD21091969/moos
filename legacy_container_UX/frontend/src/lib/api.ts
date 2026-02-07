/**
 * V5.0.0 API Client - Unified Container API with SSE
 * 
 * Replaces v4 API with unified endpoints:
 * - /api/v5/containers/{type} - All container CRUD
 * - /api/v5/containers/{type}/{id}/resources - Resource links
 * - /api/v5/containers/batch - Batch operations
 * - /api/v5/events/containers - SSE for real-time sync
 * - /api/v5/workspace - Convenience workspace endpoint
 */

import { toast } from './toast-store'

// ============================================================================
// Types
// ============================================================================

export type ContainerType = 'usersession' | 'session' | 'agent' | 'tool' | 'source'

export interface ACL {
  owner: string
  editors: string[]
  viewers: string[]
}

export interface ResourceLink {
  link_id?: string
  resource_type: string
  resource_id: string
  instance_id?: string | null
  role?: string | null
  description?: string | null
  enabled: boolean
  preset_params: Record<string, unknown>
  input_mappings: Record<string, string>
  metadata: Record<string, unknown>
  added_at?: string
  added_by?: string
}

export interface Container {
  instance_id: string
  definition_id?: string | null
  parent_id?: string | null
  depth: number
  acl: ACL
  created_at: string
  updated_at: string
  created_by: string
  // Type-specific fields
  [key: string]: unknown
}

export interface Session extends Container {
  session_id: string
  metadata: SessionMetadata
  status: string
  expires_at: string
}

export interface SessionMetadata {
  title: string
  description?: string | null
  tags: string[]
  session_type: string
  ttl_hours: number
  domain?: string | null
  visual_metadata?: Record<string, unknown>
  theme_color?: string | null
}

export interface ContainerResponse {
  success: boolean
  data?: Record<string, unknown> | null
  change_receipt?: {
    timestamp: string
    event_id?: string
  } | null
}

export interface BatchOperation {
  action: 'create' | 'update' | 'delete'
  container_type: string
  container_id?: string | null
  data: Record<string, unknown>
}

export interface BatchResponse {
  success: boolean
  results: Array<{
    success: boolean
    data?: Record<string, unknown>
    error?: string
  }>
}

export interface ContainerChangedEvent {
  event_id: string
  timestamp: string
  container_type: string
  container_id: string
  action: 'created' | 'updated' | 'deleted' | 'resource_added' | 'resource_removed' | 'acl_changed'
  user_id: string
  parent_id?: string | null
  data: Record<string, unknown>
}

export interface WorkspaceResponse {
  usersession: Container
  resources: ResourceLink[]
}

// ============================================================================
// Legacy V4 Compatibility Types
// ============================================================================

export type DefinitionType = 'agent' | 'tool' | 'source'

export interface DefinitionResponse {
  definition_id: string
  title: string
  description?: string | null
  tier: string
  category?: string | null
  tags?: string[]
  spec: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface CreateContainerRequest {
  parent_id: string
  definition_id?: string | null
  title?: string
  description?: string
  metadata?: Record<string, unknown>
  preset_params?: Record<string, unknown>
  input_mappings?: Record<string, string>
}

// ============================================================================
// Configuration
// ============================================================================

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getAuthToken(): string {
  return localStorage.getItem('auth_token') || import.meta.env.VITE_API_TOKEN || ''
}

// ============================================================================
// Core Fetch Helper
// ============================================================================

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken()
  
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    const message = error.detail || `API error: ${response.status}`
    
    if (response.status === 401) {
      toast.error('Authentication failed - please log in again')
    } else if (response.status === 403) {
      toast.error('Permission denied')
    } else if (response.status === 404) {
      toast.error('Resource not found')
    } else {
      toast.error(message)
    }
    
    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

// ============================================================================
// Container Type Detection
// ============================================================================

export function getContainerTypeFromId(id: string): ContainerType | null {
  if (id.startsWith('usersession_')) return 'usersession'
  if (id.startsWith('sess_')) return 'session'
  if (id.startsWith('agent_')) return 'agent'
  if (id.startsWith('tool_')) return 'tool'
  if (id.startsWith('source_')) return 'source'
  return null
}

export function isTerminalContainer(type: ContainerType): boolean {
  return type === 'source'
}

// ============================================================================
// API Client Interface & Factory
// ============================================================================

export interface ApiClient {
  // Workspace
  getWorkspace(): Promise<WorkspaceResponse>
  
  // Containers
  listContainers(type: ContainerType): Promise<Container[]>
  getContainer(type: ContainerType, id: string): Promise<Container>
  createContainer(type: ContainerType, req: any): Promise<Container>
  updateContainer(type: ContainerType, id: string, req: any): Promise<Container>
  deleteContainer(type: ContainerType, id: string): Promise<void>
  
  // Resources
  listResources(containerId: string): Promise<ResourceLink[]>
  addResource(containerId: string, req: any): Promise<string>
  updateResource(containerId: string, linkId: string, req: any): Promise<void>
  removeResource(containerId: string, linkId: string): Promise<void>
  
  // Events
  subscribeToContainerEvents(
    containerId: string, 
    onEvent: (event: ContainerChangedEvent) => void, 
    onError?: (error: any) => void
  ): () => void
}

import { MockApiClient } from './mock-backend/client'
import { isDemoMode } from './env'

class RealApiClient implements ApiClient {
  async getWorkspace(): Promise<WorkspaceResponse> {
    return apiFetch<WorkspaceResponse>('/api/v5/workspace')
  }

  async listContainers(type: ContainerType): Promise<Container[]> {
    const response = await apiFetch<ContainerResponse>(`/api/v5/containers/${type}`)
    return (response.data?.containers as Container[]) || []
  }

  async getContainer(type: ContainerType, id: string): Promise<Container> {
    const response = await apiFetch<ContainerResponse>(`/api/v5/containers/${type}/${id}`)
    if (!response.data) throw new Error(`${type} ${id} not found`)
    return response.data as Container
  }

  async createContainer(type: ContainerType, req: any): Promise<Container> {
    const response = await apiFetch<ContainerResponse>(`/api/v5/containers/${type}`, {
      method: 'POST',
      body: JSON.stringify(req),
    })
    if (!response.data) throw new Error('Failed to create container')
    return response.data as Container
  }

  async updateContainer(type: ContainerType, id: string, req: any): Promise<Container> {
    const response = await apiFetch<ContainerResponse>(`/api/v5/containers/${type}/${id}`, {
      method: 'PUT',
      body: JSON.stringify(req),
    })
    if (!response.data) throw new Error('Failed to update container')
    return response.data as Container
  }

  async deleteContainer(type: ContainerType, id: string): Promise<void> {
    await apiFetch<ContainerResponse>(`/api/v5/containers/${type}/${id}`, {
      method: 'DELETE',
    })
  }

  async listResources(containerId: string): Promise<ResourceLink[]> {
    const type = getContainerTypeFromId(containerId)
    if (!type) throw new Error(`Invalid container ID: ${containerId}`)
    const response = await apiFetch<ContainerResponse>(`/api/v5/containers/${type}/${containerId}/resources`)
    return (response.data?.resources as ResourceLink[]) || []
  }

  async addResource(containerId: string, req: any): Promise<string> {
    const type = getContainerTypeFromId(containerId)
    if (!type) throw new Error(`Invalid container ID: ${containerId}`)
    const response = await apiFetch<ContainerResponse>(`/api/v5/containers/${type}/${containerId}/resources`, {
      method: 'POST',
      body: JSON.stringify(req),
    })
    return (response.data?.link_id as string) || ''
  }

  async updateResource(containerId: string, linkId: string, req: any): Promise<void> {
    const type = getContainerTypeFromId(containerId)
    if (!type) throw new Error(`Invalid container ID: ${containerId}`)
    await apiFetch<ContainerResponse>(`/api/v5/containers/${type}/${containerId}/resources/${linkId}`, {
      method: 'PUT',
      body: JSON.stringify(req),
    })
  }

  async removeResource(containerId: string, linkId: string): Promise<void> {
    const type = getContainerTypeFromId(containerId)
    if (!type) throw new Error(`Invalid container ID: ${containerId}`)
    await apiFetch<ContainerResponse>(`/api/v5/containers/${type}/${containerId}/resources/${linkId}`, {
      method: 'DELETE',
    })
  }

  subscribeToContainerEvents(
    _containerId: string, 
    onEvent: (event: ContainerChangedEvent) => void, 
    _onError?: (error: any) => void
  ): () => void {
    return subscribeToContainerEvents(onEvent, _onError)
  }
}

const apiClient: ApiClient = isDemoMode()
  ? new MockApiClient() 
  : new RealApiClient()

// ============================================================================
// Container CRUD (Delegates)
// ============================================================================

/**
 * List all containers of a type the user has access to
 */
export async function listContainers(type: ContainerType): Promise<Container[]> {
  return apiClient.listContainers(type)
}

/**
 * Get a single container by ID
 */
export async function getContainer(type: ContainerType, id: string): Promise<Container> {
  return apiClient.getContainer(type, id)
}

/**
 * Create a new container
 */
export async function createContainer(
  type: ContainerType,
  request: {
    parent_id: string
    definition_id?: string | null
    title?: string
    metadata?: Record<string, unknown>
    preset_params?: Record<string, unknown>
    input_mappings?: Record<string, string>
    session_metadata?: SessionMetadata
  }
): Promise<Container> {
  return apiClient.createContainer(type, request)
}

/**
 * Update a container
 */
export async function updateContainer(
  type: ContainerType,
  id: string,
  updates: Partial<Container>
): Promise<Container> {
  return apiClient.updateContainer(type, id, updates)
}

/**
 * Delete a container
 */
export async function deleteContainer(type: ContainerType, id: string): Promise<void> {
  return apiClient.deleteContainer(type, id)
}

// ============================================================================
// Session Convenience Functions
// ============================================================================

/**
 * Create a new session
 */
export async function createSession(
  parentId: string,
  metadata: SessionMetadata
): Promise<Session> {
  return createContainer('session', {
    parent_id: parentId,
    session_metadata: metadata,
  }) as Promise<Session>
}

/**
 * Get a session by ID
 */
export async function getSession(sessionId: string): Promise<Session> {
  return getContainer('session', sessionId) as Promise<Session>
}

/**
 * Update a session
 */
export async function updateSession(sessionId: string, updates: Partial<Session>): Promise<Session> {
  return updateContainer('session', sessionId, updates) as Promise<Session>
}

/**
 * Delete a session
 */
export async function deleteSession(sessionId: string): Promise<void> {
  return deleteContainer('session', sessionId)
}

/**
 * List all user's sessions
 */
export async function listSessions(): Promise<Session[]> {
  return listContainers('session') as Promise<Session[]>
}

// ============================================================================
// Resource Link Operations
// ============================================================================

/**
 * List resources in a container
 */
export async function listContainerResources(
  _type: ContainerType,
  containerId: string,
  resourceType?: string
): Promise<ResourceLink[]> {
  const resources = await apiClient.listResources(containerId)
  if (resourceType) {
    return resources.filter(r => r.resource_type === resourceType)
  }
  return resources
}

/**
 * Add a resource to a container
 */
export async function addContainerResource(
  _type: ContainerType,
  containerId: string,
  resource: Omit<ResourceLink, 'link_id' | 'added_at' | 'added_by'>
): Promise<string> {
  return apiClient.addResource(containerId, resource)
}

/**
 * Remove a resource from a container
 */
export async function removeContainerResource(
  _type: ContainerType,
  containerId: string,
  linkId: string
): Promise<void> {
  return apiClient.removeResource(containerId, linkId)
}

/**
 * Update a resource in a container
 */
export async function updateContainerResource(
  _type: ContainerType,
  containerId: string,
  linkId: string,
  updates: {
    description?: string | null
    preset_params?: Record<string, unknown>
    input_mappings?: Record<string, string>
    metadata?: Record<string, unknown>
    enabled?: boolean
  }
): Promise<ResourceLink> {
  await apiClient.updateResource(containerId, linkId, updates)
  // Return updated resource (mock or fetch again)
  const resources = await apiClient.listResources(containerId)
  const updated = resources.find(r => r.link_id === linkId)
  if (!updated) throw new Error('Resource not found after update')
  return updated
}

// ============================================================================
// Batch Operations
// ============================================================================

/**
 * Execute multiple operations in a single request
 */
export async function batchContainerOperations(
  operations: BatchOperation[]
): Promise<BatchResponse> {
  return apiFetch<BatchResponse>('/api/v5/containers/batch', {
    method: 'POST',
    body: JSON.stringify({ operations }),
  })
}

// ============================================================================
// Workspace Convenience
// ============================================================================

/**
 * Get user's workspace (UserSession + resources)
 */
export async function getWorkspace(): Promise<WorkspaceResponse> {
  return apiClient.getWorkspace()
}

/**
 * Sync workspace with ACL-permitted sessions
 */
export async function syncWorkspace(): Promise<{
  changes: number
  resources: ResourceLink[]
}> {
  // For mock, we just return current state
  if (isDemoMode()) {
    const ws = await apiClient.getWorkspace()
    return { changes: 0, resources: ws.resources }
  }
  
  const response = await apiFetch<ContainerResponse>('/api/v5/workspace/sync', {
    method: 'POST',
  })
  return response.data as { changes: number; resources: ResourceLink[] }
}

// ============================================================================
// SSE Events Subscription
// ============================================================================

type EventCallback = (event: ContainerChangedEvent) => void

/**
 * Subscribe to container change events via SSE
 * 
 * @param onEvent Callback for each event
 * @param onError Callback for errors
 * @param since Optional timestamp for catch-up events
 * @returns Cleanup function to unsubscribe
 */
export function subscribeToContainerEvents(
  onEvent: EventCallback,
  onError?: (error: Error) => void,
  since?: number
): () => void {
  // EventSource doesn't support custom headers natively
  // Pass token as query param for SSE authentication
  const token = encodeURIComponent(getAuthToken())
  const params = new URLSearchParams()
  if (since) params.set('since', String(since))
  if (token) params.set('token', token)
  const queryString = params.toString() ? `?${params.toString()}` : ''
  const url = `${API_URL}/api/v5/events/containers${queryString}`
  
  const eventSource = new EventSource(url)
  
  // For production, you'd want to use a library like eventsource-polyfill
  // that supports Authorization headers, or pass token as query param
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as ContainerChangedEvent
      onEvent(data)
    } catch (error) {
      console.error('Failed to parse SSE event:', error)
    }
  }
  
  eventSource.onerror = (error) => {
    console.error('SSE connection error:', error)
    onError?.(new Error('SSE connection error'))
  }
  
  // Return cleanup function
  return () => {
    eventSource.close()
  }
}

/**
 * Create an SSE subscription with automatic reconnection
 */
export function createContainerEventSubscription(
  onEvent: EventCallback,
  options?: {
    onError?: (error: Error) => void
    onReconnect?: () => void
    maxRetries?: number
    retryDelayMs?: number
  }
): { start: () => void; stop: () => void } {
  let cleanup: (() => void) | null = null
  // lastEventTimestamp reserved for reconnection catch-up (future feature)
  let retryCount = 0
  let stopped = false
  
  const maxRetries = options?.maxRetries ?? 5
  const retryDelayMs = options?.retryDelayMs ?? 3000
  
  const connect = () => {
    if (stopped) return
    
    // Use apiClient for subscription
    // Note: We pass a dummy ID for now as the V5 endpoint is global/user-scoped
    cleanup = apiClient.subscribeToContainerEvents(
      'global', 
      (event) => {
        // Track last event for reconnection catch-up (future feature)
        // lastEventTimestamp = new Date(event.timestamp).getTime() / 1000
        retryCount = 0 // Reset on successful event
        onEvent(event)
      },
      (error) => {
        options?.onError?.(error)
        
        // Attempt reconnection
        if (!stopped && retryCount < maxRetries) {
          retryCount++
          console.warn(`SSE reconnecting (attempt ${retryCount}/${maxRetries})...`)
          setTimeout(() => {
            options?.onReconnect?.()
            connect()
          }, retryDelayMs * retryCount)
        }
      }
    )
  }
  
  return {
    start: () => {
      stopped = false
      connect()
    },
    stop: () => {
      stopped = true
      cleanup?.()
      cleanup = null
    },
  }
}

// ============================================================================
// Legacy Compatibility (maps to v4 patterns)
// ============================================================================

/**
 * Get user session - now uses workspace endpoint
 * @deprecated Use getWorkspace() instead
 */
export async function getUserSession(_userId: string): Promise<Container> {
  const workspace = await getWorkspace()
  return workspace.usersession
}

/**
 * List workspace resources - now uses workspace endpoint
 * @deprecated Use getWorkspace() instead
 */
export async function listWorkspaceResources(
  _userId: string,
  resourceType?: string
): Promise<ResourceLink[]> {
  const workspace = await getWorkspace()
  if (resourceType) {
    return workspace.resources.filter(
      (r) => r.resource_type.toLowerCase() === resourceType.toLowerCase()
    )
  }
  return workspace.resources
}

/**
 * Add resource to workspace
 * @param userSessionId - The full usersession instance ID (e.g., "usersession_enterprise@test.com")
 */
export async function addWorkspaceResource(
  userSessionId: string,
  resource: Omit<ResourceLink, 'link_id' | 'added_at' | 'added_by'>
): Promise<string> {
  return addContainerResource('usersession', userSessionId, resource)
}

/**
 * Remove resource from workspace
 * @param userSessionId - The full usersession instance ID (e.g., "usersession_enterprise@test.com")
 */
export async function removeWorkspaceResource(
  userSessionId: string,
  linkId: string
): Promise<void> {
  return removeContainerResource('usersession', userSessionId, linkId)
}

/**
 * Update resource in workspace
 * @param userSessionId - The full usersession instance ID (e.g., "usersession_enterprise@test.com")
 */
export async function updateWorkspaceResource(
  userSessionId: string,
  linkId: string,
  updates: {
    description?: string
    preset_params?: Record<string, unknown>
    input_mappings?: Record<string, string>
    metadata?: Record<string, unknown>
    enabled?: boolean
  }
): Promise<ResourceLink> {
  return updateContainerResource('usersession', userSessionId, linkId, updates)
}

// ============================================================================
// ResourceLink → Node Conversion (for ReactFlow)
// ============================================================================

export type AnyContainerType = 'session' | 'agent' | 'tool' | 'source' | 'user'

export interface ResourceLinkNodeData {
  linkId: string
  resourceId: string
  resourceType: string
  instanceId?: string
  title: string
  description?: string
  enabled: boolean
  presetParams: Record<string, unknown>
  inputMappings: Record<string, string>
  metadata: Record<string, unknown>
}

/**
 * Convert a ResourceLink to a ReactFlow CustomNode
 * Position comes from ResourceLink.metadata.x/y
 * 
 * IMPORTANT: For session resources, use instance_id as node ID (sess_* format)
 * because that's what the backend expects for API calls.
 * link_id is just a reference within the parent container.
 */
export function resourceLinkToNode(link: ResourceLink): {
  id: string
  type: string
  position: { x: number; y: number }
  data: ResourceLinkNodeData
  draggable?: boolean
} {
  const metadata = (link.metadata || {}) as Record<string, unknown>
  
  // For session resources, use instance_id (sess_*) as the node ID
  // because that's what backend APIs expect for fetching/navigation
  const nodeId = link.resource_type === 'session' 
    ? (link.instance_id || link.resource_id || link.link_id || '')
    : (link.link_id || link.resource_id)
  
  return {
    id: nodeId,
    type: link.resource_type,
    position: {
      x: typeof metadata.x === 'number' ? metadata.x : 100,
      y: typeof metadata.y === 'number' ? metadata.y : 100,
    },
    draggable: link.resource_type === 'user' ? false : undefined,
    data: {
      linkId: link.link_id || '',
      resourceId: link.resource_id,
      resourceType: link.resource_type,
      instanceId: link.instance_id || undefined,
      title: link.description || link.resource_id,
      description: link.description || undefined,
      enabled: link.enabled ?? true,
      presetParams: link.preset_params || {},
      inputMappings: link.input_mappings || {},
      metadata: metadata,
    },
  }
}

/**
 * Convert a CustomNode position back to ResourceLink metadata update
 */
export function nodePositionToMetadataUpdate(
  position: { x: number; y: number }
): { metadata: Record<string, unknown> } {
  return {
    metadata: { x: position.x, y: position.y },
  }
}

/**
 * Check if container type can have nested resources (is diveable)
 * Source containers can only have USER resources for ACL
 */
export function isContainerDiveable(type: ContainerType): boolean {
  return type !== 'source'
}

// ============================================================================
// Definitions API (Registry) - Templates for Agents/Tools/Sources
// ============================================================================

// Singleton for demo mode definitions access
const mockClientInstance = new MockApiClient()

/**
 * List available definitions (system + custom with tier/ACL filtering)
 * Used by resource-slice to populate add menus
 */
export async function listDefinitions(
  definitionType: DefinitionType,
  options?: {
    tier?: string
    tags?: string[]
    search?: string
  }
): Promise<DefinitionResponse[]> {
  // Demo Mode Bypass
  if (isDemoMode()) {
    return mockClientInstance.listDefinitions(definitionType)
  }

  const params = new URLSearchParams()
  if (options?.tier) params.set('tier', options.tier)
  if (options?.tags?.length) params.set('tags', options.tags.join(','))
  if (options?.search) params.set('search', options.search)
  
  const queryString = params.toString()
  const path = `/definitions/${definitionType}${queryString ? `?${queryString}` : ''}`
  
  const response = await apiFetch<{ definitions: DefinitionResponse[] }>(path)
  return response.definitions
}

// ============================================================================
// Session Resource API (Legacy compatibility)
// Sessions use /sessions/{id}/resources endpoint
// ============================================================================

/**
 * Add resource to session (V4 compatibility)
 * @deprecated Use addContainerResource('session', ...) for V5
 */
export async function addSessionResource(
  sessionId: string,
  request: {
    resource_type: string
    resource_id: string
    description?: string
    preset_params?: Record<string, unknown>
    input_mappings?: Record<string, string>
    metadata?: Record<string, unknown>
  }
): Promise<ResourceLink> {
  return apiFetch(`/sessions/${sessionId}/resources`, {
    method: 'POST',
    body: JSON.stringify(request),
  })
}
