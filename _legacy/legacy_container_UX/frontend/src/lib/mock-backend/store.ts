import { MockDatabase, SYSTEM_DEFINITIONS, ORPHAN_CONTAINERS, ROOT_USER_SESSION, ROOT_SESSION_CONTAINER } from './data'
import { DefinitionResponse, Container, ResourceLink, ACL } from '../api'
import { v4 as uuidv4 } from 'uuid'

// Default ACL for new containers
const DEFAULT_ACL: ACL = {
  owner: 'enterprise@test.com',
  editors: [],
  viewers: []
}

class MockBackendStore {
  private db: MockDatabase

  constructor() {
    this.db = {
      definitions: {},
      containers: {},
      links: {},
      userSessions: {}
    }
    this.seed()
  }

  private seed() {
    // Seed Definitions
    SYSTEM_DEFINITIONS.forEach(def => {
      this.db.definitions[def.definition_id] = def
    })

    // Seed UserSession (V5: Container at depth 0)
    this.db.userSessions[ROOT_USER_SESSION.instance_id] = ROOT_USER_SESSION
    this.db.containers[ROOT_SESSION_CONTAINER.instance_id] = ROOT_SESSION_CONTAINER
    this.db.links[ROOT_SESSION_CONTAINER.instance_id] = []

    // Seed Orphans (containers with parent_id = null)
    ORPHAN_CONTAINERS.forEach(container => {
      this.db.containers[container.instance_id] = container
    })
  }

  // ==========================================================================
  // Definitions
  // ==========================================================================

  listDefinitions(_type: string): DefinitionResponse[] {
    return Object.values(this.db.definitions).filter(d => {
      if (_type === 'agent') return d.definition_id.startsWith('def_agent')
      if (_type === 'tool') return d.definition_id.startsWith('def_tool')
      if (_type === 'source') return d.definition_id.startsWith('def_source')
      return false
    })
  }

  getDefinition(id: string): DefinitionResponse | null {
    return this.db.definitions[id] || null
  }

  // ==========================================================================
  // Containers (V5 UOM)
  // ==========================================================================

  createContainer(type: string, parentId: string, data: { title?: string; description?: string; definition_id?: string | null }): Container {
    const idPrefix = type === 'session' ? 'sess_' : type === 'agent' ? 'agnt_' : type === 'tool' ? 'tool_' : 'src_'
    const id = `${idPrefix}${uuidv4().substring(0, 8)}`
    
    // Calculate depth from parent
    const parent = this.db.containers[parentId]
    const depth = parent ? (parent.depth + 1) : 1

    const container: Container = {
      instance_id: id,
      definition_id: data.definition_id || null,
      parent_id: parentId,
      depth,
      acl: DEFAULT_ACL,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      created_by: 'enterprise@test.com',
      // Type-specific
      title: data.title || id,
      description: data.description || '',
    }

    this.db.containers[id] = container
    return container
  }

  getContainer(id: string): Container | null {
    return this.db.containers[id] || null
  }

  // ==========================================================================
  // Resources (ResourceLinks)
  // ==========================================================================

  listResources(parentId: string): ResourceLink[] {
    return this.db.links[parentId] || []
  }

  addResourceLink(parentId: string, req: { resource_id: string; resource_type: string; instance_id?: string; metadata?: Record<string, unknown> }): ResourceLink {
    const linkId = `link_${uuidv4().substring(0, 8)}`
    const link: ResourceLink = {
      link_id: linkId,
      resource_type: req.resource_type,
      resource_id: req.resource_id,
      instance_id: req.instance_id || null,
      enabled: true,
      preset_params: {},
      input_mappings: {},
      metadata: req.metadata || { x: 100, y: 100 },
      added_at: new Date().toISOString(),
      added_by: 'enterprise@test.com'
    }

    if (!this.db.links[parentId]) {
      this.db.links[parentId] = []
    }
    this.db.links[parentId].push(link)
    return link
  }

  // ==========================================================================
  // Workspace Logic (Orphan Containers for "Add Existing")
  // ==========================================================================

  /**
   * V5 UOM: Returns orphan containers (parent_id = null) that can be adopted
   */
  listOrphanContainers(type?: string): Container[] {
    const orphans = Object.values(this.db.containers).filter(c => c.parent_id === null)
    if (type) {
      return orphans.filter(c => {
        if (type === 'agent') return c.instance_id.startsWith('agnt_')
        if (type === 'tool') return c.instance_id.startsWith('tool_')
        if (type === 'source') return c.instance_id.startsWith('src_')
        return false
      })
    }
    return orphans
  }

  /**
   * Legacy: Returns all containers not linked in current session
   * @deprecated Use listOrphanContainers for V5
   */
  listAvailableResources(_userId: string, currentSessionId: string): Container[] {
    const allContainers = Object.values(this.db.containers)
    const currentLinks = this.db.links[currentSessionId] || []
    const linkedIds = new Set(currentLinks.map(l => l.resource_id))

    return allContainers.filter(c => 
      !linkedIds.has(c.instance_id) &&
      c.instance_id !== currentSessionId &&
      !c.instance_id.startsWith('sess_') // Don't list sessions as "available resources"
    )
  }
}

export const mockStore = new MockBackendStore()
