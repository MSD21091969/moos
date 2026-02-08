import { DefinitionResponse, Container, ResourceLink, ACL } from '../api'

// ============================================================================
// Mock Data Types (V5 UOM)
// ============================================================================

export interface MockDatabase {
  definitions: Record<string, DefinitionResponse>
  containers: Record<string, Container>
  links: Record<string, ResourceLink[]> // Keyed by parent_id
  userSessions: Record<string, Container> // UserSession is also a Container in V5
}

// Default ACL for demo data
const DEMO_ACL: ACL = {
  owner: 'enterprise@test.com',
  editors: [],
  viewers: []
}

// ============================================================================
// Seed Data
// ============================================================================

export const SYSTEM_DEFINITIONS: DefinitionResponse[] = [
  {
    definition_id: 'def_agent_base',
    title: 'Base Assistant',
    description: 'A general purpose AI assistant',
    tier: 'free',
    category: 'general',
    tags: ['chat', 'helper'],
    spec: { model: 'gpt-4o-mini' },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    definition_id: 'def_tool_search',
    title: 'Web Search',
    description: 'Search the internet for information',
    tier: 'free',
    category: 'search',
    tags: ['web', 'search'],
    spec: { provider: 'google' },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    definition_id: 'def_tool_calc',
    title: 'Calculator',
    description: 'Perform mathematical calculations',
    tier: 'free',
    category: 'utility',
    tags: ['math'],
    spec: {},
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
]

// V5: Orphans are containers with parent_id = null (in Library)
export const ORPHAN_CONTAINERS: Container[] = [
  {
    instance_id: 'agnt_orphan_1',
    definition_id: 'def_agent_base',
    parent_id: null,
    depth: 0,
    acl: DEMO_ACL,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    created_by: 'enterprise@test.com',
    // Type-specific
    title: 'Unassigned Helper',
    description: 'An agent created previously but not assigned to this session',
  },
  {
    instance_id: 'tool_orphan_1',
    definition_id: 'def_tool_search',
    parent_id: null,
    depth: 0,
    acl: DEMO_ACL,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    created_by: 'enterprise@test.com',
    // Type-specific
    title: 'Global Search Tool',
    description: 'A shared search tool instance',
  }
]

// V5: UserSession is a Container at depth 0
export const ROOT_USER_SESSION: Container = {
  instance_id: 'usersession_enterprise@test.com',
  definition_id: null,
  parent_id: null,
  depth: 0,
  acl: DEMO_ACL,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  created_by: 'enterprise@test.com',
  // Type-specific
  user_id: 'enterprise@test.com',
  tier: 'enterprise',
  email: 'enterprise@test.com',
  display_name: 'Demo User',
}

// V5: Root session container (child of UserSession)
export const ROOT_SESSION_CONTAINER: Container = {
  instance_id: 'sess_root',
  definition_id: null, // Sessions don't have definitions
  parent_id: 'usersession_enterprise@test.com',
  depth: 1,
  acl: DEMO_ACL,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  created_by: 'enterprise@test.com',
  // Type-specific (SessionMetadata)
  title: 'My Workspace',
  description: 'Root workspace session',
  status: 'active',
  session_type: 'workspace',
}
