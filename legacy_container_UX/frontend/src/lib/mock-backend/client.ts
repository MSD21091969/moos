import { mockStore } from './store'
import { 
  DefinitionResponse, 
  Container, 
  ResourceLink, 
  DefinitionType,
  ContainerType,
  WorkspaceResponse,
  ContainerChangedEvent,
  ApiClient
} from '../api'
import { ROOT_USER_SESSION, ROOT_SESSION_CONTAINER } from './data'

// ============================================================================
// Mock API Client Implementation (V5 UOM)
// Implements ApiClient interface for demo mode
// ============================================================================

export class MockApiClient implements ApiClient {
  // ==========================================================================
  // Workspace
  // ==========================================================================
  
  async getWorkspace(): Promise<WorkspaceResponse> {
    return {
      usersession: ROOT_USER_SESSION,
      resources: await mockStore.listResources(ROOT_SESSION_CONTAINER.instance_id)
    }
  }

  // ==========================================================================
  // Containers
  // ==========================================================================

  async listContainers(type: ContainerType): Promise<Container[]> {
    return mockStore.listOrphanContainers(type)
  }

  async getContainer(_type: ContainerType, id: string): Promise<Container> {
    const container = mockStore.getContainer(id)
    if (!container) throw new Error(`Container not found: ${id}`)
    return container
  }

  async createContainer(_type: ContainerType, req: { parent_id: string; title?: string; definition_id?: string | null }): Promise<Container> {
    return mockStore.createContainer(_type, req.parent_id, {
      title: req.title,
      definition_id: req.definition_id
    })
  }

  async updateContainer(_type: ContainerType, id: string, _req: any): Promise<Container> {
    const container = mockStore.getContainer(id)
    if (!container) throw new Error(`Container not found: ${id}`)
    return container
  }

  async deleteContainer(_type: ContainerType, _id: string): Promise<void> {
    // No-op in mock
  }

  // ==========================================================================
  // Resources
  // ==========================================================================

  async listResources(containerId: string): Promise<ResourceLink[]> {
    return mockStore.listResources(containerId)
  }

  async addResource(containerId: string, req: { resource_id: string; resource_type: string; instance_id?: string; metadata?: Record<string, unknown> }): Promise<string> {
    const linkId = `link_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    await mockStore.addResourceLink(containerId, req)
    return linkId
  }

  async updateResource(_containerId: string, _linkId: string, _req: any): Promise<void> {
    // No-op in mock
  }

  async removeResource(_containerId: string, _linkId: string): Promise<void> {
    // No-op in mock
  }

  // ==========================================================================
  // Events
  // ==========================================================================

  subscribeToContainerEvents(
    _containerId: string,
    _onEvent: (event: ContainerChangedEvent) => void,
    _onError?: (error: any) => void
  ): () => void {
    return () => {}
  }

  // ==========================================================================
  // Extra Mock Methods (demo-only features)
  // ==========================================================================

  async getUserSession(_userId: string): Promise<Container> {
    return ROOT_USER_SESSION
  }

  async listWorkspaceResources(_userId: string): Promise<ResourceLink[]> {
    return mockStore.listResources(ROOT_SESSION_CONTAINER.instance_id)
  }

  async listDefinitions(type: DefinitionType): Promise<DefinitionResponse[]> {
    return mockStore.listDefinitions(type)
  }

  async getDefinition(_type: DefinitionType, id: string): Promise<DefinitionResponse> {
    const def = mockStore.getDefinition(id)
    if (!def) throw new Error(`Definition not found: ${id}`)
    return def
  }

  async listOrphanContainers(type?: string): Promise<Container[]> {
    return mockStore.listOrphanContainers(type)
  }

  async listAvailableResources(_userId: string, currentSessionId: string): Promise<Container[]> {
    return mockStore.listAvailableResources(_userId, currentSessionId)
  }
}
