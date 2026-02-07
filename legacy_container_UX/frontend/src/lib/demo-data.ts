import { ContainerVisualState, CustomNode, AgentNodeData, ToolNodeData } from './types'
import type { ResourceLinkNodeData, DefinitionResponse } from './api'

/**
 * Demo Data for Phase 1 Testing
 * 
 * V4.1 Architecture (from backend/src/models/containers.py):
 * - Container types: Session, Agent, Tool, Source (all can contain each other)
 * - Terminal types (NOT containers): User, Introspection
 * - Containment rules:
 *   - UserSession → only Sessions (L1)
 *   - Session → Agent, Tool, Source, Session
 *   - Agent → Tool, Source, Session, Agent (can nest!)
 *   - Tool → Agent, Source, Session, Tool (can nest!)
 *   - Source → NOTHING (terminal, deepest level)
 * 
 * Creates 5 UserSession-level sessions, each containing:
 * - 1 Agent (L2) — with nested Tool inside
 * - 1 Tool (L2) — with nested Source inside
 * - 1 Source (L2)
 * - 1 User ResourceLink (ACL, NOT a container)
 * 
 * This data is loaded when localStorage is empty and VITE_MODE='demo'.
 * Use "🔄 Reset: Demo Data" task to reload fresh demo data.
 */

// ============================================================================
// Demo Definitions - Model Definitions available in Demo Mode
// These are the "templates" from which Container Instances are created
// ============================================================================

export const DEMO_AGENT_DEFINITIONS: DefinitionResponse[] = [
  {
    definition_id: 'demo_agent',
    title: 'Data Analysis Agent',
    description: 'General purpose data analysis and insights agent',
    tier: 'FREE',
    category: 'analysis',
    tags: ['data', 'analysis', 'insights'],
    spec: { model: 'gpt-4', temperature: 0.7 },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    definition_id: 'code_assistant',
    title: 'Code Assistant',
    description: 'Programming and code review agent',
    tier: 'FREE',
    category: 'development',
    tags: ['code', 'programming', 'review'],
    spec: { model: 'gpt-4', temperature: 0.3 },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    definition_id: 'research_agent',
    title: 'Research Agent',
    description: 'Deep research and knowledge synthesis agent',
    tier: 'PROFESSIONAL',
    category: 'research',
    tags: ['research', 'knowledge', 'synthesis'],
    spec: { model: 'gpt-4', temperature: 0.5 },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]

export const DEMO_TOOL_DEFINITIONS: DefinitionResponse[] = [
  {
    definition_id: 'data_cleaner',
    title: 'Data Cleaner',
    description: 'Clean and normalize messy datasets before analysis',
    tier: 'FREE',
    category: 'data',
    tags: ['clean', 'normalize', 'prep'],
    spec: { strategy: 'basic', maxRows: 5000 },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    definition_id: 'csv_analyzer',
    title: 'CSV Analyzer',
    description: 'Parse and analyze CSV data files',
    tier: 'FREE',
    category: 'data',
    tags: ['csv', 'data', 'parser'],
    spec: { maxRows: 10000, encoding: 'utf-8' },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    definition_id: 'json_transformer',
    title: 'JSON Transformer',
    description: 'Transform and manipulate JSON data',
    tier: 'FREE',
    category: 'data',
    tags: ['json', 'transform', 'data'],
    spec: { prettyPrint: true },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    definition_id: 'web_scraper',
    title: 'Web Scraper',
    description: 'Extract data from web pages',
    tier: 'PROFESSIONAL',
    category: 'extraction',
    tags: ['web', 'scrape', 'extract'],
    spec: { respectRobots: true, timeout: 30000 },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    definition_id: 'api_connector',
    title: 'API Connector',
    description: 'Connect to REST APIs and fetch data',
    tier: 'FREE',
    category: 'integration',
    tags: ['api', 'rest', 'connector'],
    spec: { retries: 3 },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]

export const DEMO_SOURCE_DEFINITIONS: DefinitionResponse[] = [
  {
    definition_id: 'postgres_source',
    title: 'PostgreSQL Database',
    description: 'Connect to PostgreSQL database',
    tier: 'FREE',
    category: 'database',
    tags: ['postgres', 'sql', 'database'],
    spec: { poolSize: 5 },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    definition_id: 'gcs_source',
    title: 'Google Cloud Storage',
    description: 'Connect to GCS buckets',
    tier: 'PROFESSIONAL',
    category: 'cloud',
    tags: ['gcs', 'cloud', 'storage'],
    spec: {},
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    definition_id: 'sharepoint_source',
    title: 'SharePoint',
    description: 'Connect to Microsoft SharePoint',
    tier: 'ENTERPRISE',
    category: 'enterprise',
    tags: ['sharepoint', 'microsoft', 'enterprise'],
    spec: {},
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]
export function createDemoSessions(): {
  containers: ContainerVisualState[]
  nodes: CustomNode[]
  registry: Record<string, { container: any, resources: any[] }>
} {
  // Root User Session (The "Workspace")
  const rootUserSession = {
    instance_id: 'demo-root',
    container_type: 'usersession',
    title: 'Demo Workspace',
    resources: [] as any[]
  };

  // Orphan Resources (Available for "Add Existing")
  const orphanAgent = {
    resource_id: 'orphan-agent-1',
    resource_type: 'agent',
    title: 'Shared Analysis Agent',
    description: 'An agent available at the workspace root',
    metadata: { x: 0, y: 0 }
  };
  
  const orphanTool = {
    resource_id: 'orphan-tool-1',
    resource_type: 'tool',
    title: 'Shared CSV Parser',
    description: 'A tool available at the workspace root',
    metadata: { x: 0, y: 0 }
  };

  rootUserSession.resources.push(orphanAgent, orphanTool);

  const containers: ContainerVisualState[] = [
    // Session 1: Trip Planning
    {
      id: 'session-1',
      title: 'Trip to Santorini',
      position: { x: 100, y: 100 },
      size: { width: 320, height: 400 },
      themeColor: '#3b82f6',
      status: 'active',
      expanded: true,
      zoneId: 'active',
      containerType: 'session',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    // Session 2: Data Analysis
    {
      id: 'session-2',
      title: 'Q4 Sales Analysis',
      position: { x: 500, y: 100 },
      size: { width: 320, height: 400 },
      themeColor: '#ef4444',
      status: 'active',
      expanded: true,
      zoneId: 'production',
      containerType: 'session',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    // Session 3: Code Project
    {
      id: 'session-3',
      title: 'React App Build',
      position: { x: 900, y: 100 },
      size: { width: 320, height: 400 },
      themeColor: '#22c55e',
      status: 'active',
      expanded: true,
      zoneId: 'active',
      containerType: 'session',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    // Session 4: Research
    {
      id: 'session-4',
      title: 'AI Research Notes',
      position: { x: 100, y: 550 },
      size: { width: 320, height: 400 },
      themeColor: '#a855f7',
      status: 'active',
      expanded: true,
      zoneId: 'sandbox',
      containerType: 'session',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    // Session 5: Client Project
    {
      id: 'session-5',
      title: 'Client Dashboard',
      position: { x: 500, y: 550 },
      size: { width: 320, height: 400 },
      themeColor: '#f59e0b',
      status: 'active',
      expanded: true,
      zoneId: 'production',
      containerType: 'session',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
  ]

  // Helper to create child nodes for each session
  // V4.1: Agent, Tool, Source are containers. User is ResourceLink (terminal).
  const createSessionChildren = (sessionId: string, sessionIndex: number): { nodes: CustomNode[], childContainers: ContainerVisualState[] } => {
    const baseX = containers[sessionIndex].position.x + 20
    const baseY = containers[sessionIndex].position.y + 60

    const agentId = `${sessionId}-agent`
    const toolId = `${sessionId}-tool`

    // Create L2 Sessions (Containers) for Agent and Tool so they can be dived into
    const childContainers: ContainerVisualState[] = [
      {
        id: agentId,
        title: ['Trip Planner', 'Data Analyst', 'Code Assistant', 'Researcher', 'Project Manager'][sessionIndex],
        position: { x: baseX, y: baseY },
        size: { width: 200, height: 100 },
        themeColor: '#10b981', // Emerald for Agents
        status: 'active',
        expanded: false,
        zoneId: containers[sessionIndex].zoneId,
        containerType: 'agent',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        parentSessionId: sessionId,
        sessionType: 'workflow',
        metadata: { type: 'agent', role: ['Planning', 'Analysis', 'Development', 'Research', 'Management'][sessionIndex] }
      },
      {
        id: toolId,
        title: ['Flight Search', 'Excel Parser', 'Code Linter', 'Web Scraper', 'Report Generator'][sessionIndex],
        position: { x: baseX + 160, y: baseY },
        size: { width: 200, height: 100 },
        themeColor: '#f59e0b', // Amber for Tools
        status: 'active',
        expanded: false,
        zoneId: containers[sessionIndex].zoneId,
        containerType: 'tool',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        parentSessionId: sessionId,
        sessionType: 'analysis',
        metadata: { type: 'tool', category: ['Travel', 'Data', 'Development', 'Research', 'Business'][sessionIndex] }
      }
    ]

    const nodes: CustomNode[] = [
      // Agent (L2 container - can contain Tools, Sources, nested Agents)
      {
        id: agentId,
        type: 'agent' as const,
        position: { x: baseX, y: baseY },
        data: {
          id: agentId,
          name: childContainers[0].title,
          role: (childContainers[0].metadata as any).role,
          sessionId: sessionId,
          status: 'idle' as const,
          capabilities: ['planning', 'analysis', 'execution'],
        } as AgentNodeData & Record<string, unknown>,
      },
      // Tool (L2 container - can contain Agents, Sources, nested Tools)
      {
        id: toolId,
        type: 'tool' as const,
        position: { x: baseX + 160, y: baseY },
        data: {
          id: toolId,
          name: childContainers[1].title,
          category: (childContainers[1].metadata as any).category,
          sessionId: sessionId,
          inputs: ['query'],
          outputs: ['results'],
        } as ToolNodeData & Record<string, unknown>,
      },
      // Source (L2 terminal - CANNOT contain anything)
      {
        id: `${sessionId}-source`,
        type: 'source' as const,
        position: { x: baseX, y: baseY + 80 },
        data: {
          linkId: `${sessionId}-source-link`,
          resourceId: `${sessionId}-source`,
          resourceType: 'source',
          sessionId: sessionId, // Link to parent session
          title: ['Booking API', 'Sales DB', 'GitHub Repo', 'Arxiv Papers', 'Client CRM'][sessionIndex],
          description: 'Data source (terminal - cannot contain children)',
          enabled: true,
          presetParams: { source_type: ['api', 'database', 'file', 'api', 'database'][sessionIndex] },
          inputMappings: {},
          metadata: { x: baseX, y: baseY + 80 },
        } as ResourceLinkNodeData & Record<string, unknown>,
      },
      // User ResourceLink (ACL member - NOT a container, just a link)
      // Rendered as 'user' type node
      {
        id: `${sessionId}-user`,
        type: 'user' as const, // Use user renderer for ResourceLinks
        position: { x: baseX + 160, y: baseY + 80 },
        data: {
          linkId: `${sessionId}-user-link`,
          resourceId: ['alice-id', 'bob-id', 'carol-id', 'dan-id', 'eve-id'][sessionIndex],
          resourceType: 'user', // USER type - not a container
          sessionId: sessionId, // Link to parent session
          title: ['Alice (Owner)', 'Bob (Editor)', 'Carol (Viewer)', 'Dan (Editor)', 'Eve (Owner)'][sessionIndex],
          description: 'ACL member (terminal - not a container)',
          enabled: true,
          presetParams: { 
            role: ['owner', 'editor', 'viewer', 'editor', 'owner'][sessionIndex],
            member_type: 'user'
          },
          inputMappings: {},
          metadata: { x: baseX + 160, y: baseY + 80 },
        } as ResourceLinkNodeData & Record<string, unknown>,
      },
    ]

    return { nodes, childContainers }
  }

  // Generate all children and L2 containers
  const allChildren = containers.map((container, index) => createSessionChildren(container.id, index))
  const childNodes = allChildren.flatMap(c => c.nodes)
  const childContainers = allChildren.flatMap(c => c.childContainers)

  // Create dummy children for L2 containers (to prove they are containers)
  const l3Nodes: CustomNode[] = childContainers.flatMap(l2Container => {
    // Add a "Memory" source to every Agent
    if ((l2Container.metadata as any)?.type === 'agent') {
      return [{
        id: `${l2Container.id}-memory`,
        type: 'source' as const,
        position: { x: 50, y: 50 },
        data: {
          linkId: `${l2Container.id}-memory-link`,
          resourceId: `${l2Container.id}-memory`,
          resourceType: 'source',
          sessionId: l2Container.id, // Link to L2 Agent Container
          title: 'Agent Memory',
          description: 'Internal memory state',
          enabled: true,
          presetParams: { source_type: 'memory' },
          inputMappings: {},
          metadata: { x: 50, y: 50 },
        } as ResourceLinkNodeData & Record<string, unknown>,
      }]
    }
    return []
  })

  // Create session nodes + their children
  const nodes: CustomNode[] = [
    // Session nodes at workspace level
    ...containers.map((container) => ({
      id: container.id,
      type: 'session' as const,
      position: container.position,
      data: container as ContainerVisualState & Record<string, unknown>,
    })),
    // Children for each session
    ...childNodes,
    // Children for L2 containers
    ...l3Nodes
  ]

  // Build Registry
  const registry: Record<string, { container: any, resources: any[] }> = {
    'demo-root': {
      container: rootUserSession,
      resources: rootUserSession.resources
    }
  };

  // Add sessions to registry
  containers.forEach((c, i) => {
    registry[c.id] = {
      container: c,
      resources: allChildren[i].nodes.map(n => ({
        resource_id: n.id,
        resource_type: n.type,
        title: n.data.label || n.data.title || n.id,
        description: (n.data as any).description || '',
        metadata: n.data
      }))
    };
  });

  return { containers: [...containers, ...childContainers], nodes, registry }
}
