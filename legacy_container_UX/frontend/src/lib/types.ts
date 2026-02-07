import { Node, Edge } from '@xyflow/react'

// ===== Coordinate-based Parameters =====
export interface Position {
  x: number
  y: number
}

export interface Size {
  width: number
  height: number
}

// ===== Visual Node Types =====
export type NodeType = 'session' | 'object' | 'agent' | 'tool'

// Container type discriminator - explicit type for all visual containers
export type ContainerType = 'session' | 'agent' | 'tool' | 'source'

export type ResourceCategory = 'general' | 'data' | 'ai' | 'system' | string;

// ===== User Identity & Preferences =====
// Stored in UserSession metadata, drives ChatAgent persona and UX vocabulary
export interface UxVocabulary {
  // User's preferred terms for UI display
  session: string          // e.g., "sticky note", "note", "session"
  sessionPlural: string    // e.g., "sticky notes", "stickies", "sessions"
  container: string        // e.g., "sticky", "card", "container"
  containerPlural: string  // e.g., "stickies", "cards", "containers"
  workspace: string        // e.g., "collider space", "workspace", "board"
  agent: string            // e.g., "agent", "assistant", "bot"
  tool: string             // e.g., "tool", "action", "function"
  source: string           // e.g., "source", "data source", "connection"
}

export interface UserIdentityPreferences {
  // User ID (optional, for cloud sync)
  id?: string
  
  // User display name (shown in UI, referenced by agent)
  displayName: string           // e.g., "Sam"
  
  // ChatAgent persona
  agentName: string             // e.g., "HAL", "Navigator", "Assistant"
  agentPersonality?: string     // e.g., "helpful", "concise", "formal"
  
  // UX terminology - how user refers to elements
  uxVocabulary: UxVocabulary
  
  // Additional preferences
  voiceEnabled?: boolean
  preferredModel?: 'cloud' | 'local'
  thinkingVisible?: boolean     // Show Gemini 3 thinking in UI
}

// Default vocabulary (fallback)
export const DEFAULT_UX_VOCABULARY: UxVocabulary = {
  session: 'session',
  sessionPlural: 'sessions',
  container: 'container',
  containerPlural: 'containers',
  workspace: 'workspace',
  agent: 'agent',
  tool: 'tool',
  source: 'source',
}

// Sam's vocabulary (enterprise@test.com)
export const SAM_UX_VOCABULARY: UxVocabulary = {
  session: 'sticky note',
  sessionPlural: 'sticky notes',
  container: 'sticky',
  containerPlural: 'stickies',
  workspace: 'collider space',
  agent: 'agent',
  tool: 'tool',
  source: 'source',
}

// ===== Container Visual State =====
// Renamed from SessionVisualState - represents ALL visual containers
export interface ContainerVisualState {
  id: string
  title: string
  position: Position
  size: Size
  themeColor: string
  status: 'active' | 'completed' | 'expired' | 'archived'
  expanded: boolean
  description?: string
  tags?: string[]
  sessionType?: 'chat' | 'analysis' | 'workflow' | 'simulation'
  zoneId?: string
  createdAt: string
  updatedAt: string
  expiresAt?: string
  messageCount?: number
  metadata?: Record<string, unknown>
  parentSessionId?: string
  
  // NEW: Explicit container type discriminator
  containerType: ContainerType
  
  [key: string]: unknown
}

// Legacy alias for backward compatibility during migration
export type SessionVisualState = ContainerVisualState

export interface ObjectNodeData {
  id: string
  type: 'document' | 'data' | 'result'
  label: string
  sessionId?: string
  fileType?: string
  size?: number
  preview?: string
  [key: string]: unknown
}

export interface AgentNodeData {
  id: string
  name: string
  role: string
  sessionId?: string
  status: 'idle' | 'working' | 'error'
  capabilities: string[]
  [key: string]: unknown
}

export interface ToolNodeData {
  id: string
  name: string
  category: string
  sessionId?: string
  inputs: string[]
  outputs: string[]
  [key: string]: unknown
}

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
  [key: string]: unknown
}

export type CustomNodeData = (SessionVisualState | ObjectNodeData | AgentNodeData | ToolNodeData | ResourceLinkNodeData) & Record<string, unknown>

// Make CustomNode compatible with ReactFlow's Node type
export type CustomNode = Node<CustomNodeData, string>
export type CustomEdge = Edge

// ===== Chat Agent =====
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  operations?: AgentOperation[]
}

export interface AgentOperation {
  name: string
  params: Record<string, unknown>
  status: 'pending' | 'executing' | 'completed' | 'failed'
  result?: unknown
  error?: string
}

// ===== Visual Metadata (Frontend-only) =====
export interface VisualMetadata {
  position: Position
  size: Size
  color: string
  collapsed?: boolean
  isExpanded?: boolean
  icon?: string
  is_container?: boolean // UX flag: render as container box
  zoneId?: string
}

// ===== Backend API Types =====
export interface Session {
  session_id: string
  title: string
  status: 'active' | 'completed' | 'expired' | 'archived'
  session_type: 'chat' | 'analysis' | 'workflow' | 'simulation'
  tags: string[]
  metadata?: Record<string, unknown>
  parent_session_id?: string // For child sessions (containers)
  child_sessions?: string[] // Optional: list of child IDs
  created_at: string
  updated_at: string
}

// Container = Child session with visual rendering (frontend-only concept)
export interface Container extends Session {
  parent_session_id: string // Required for containers
}

export interface Document {
  document_id: string
  session_id: string
  title: string
  content_type: string
  size_bytes: number
  upload_status: 'pending' | 'completed' | 'failed'
  created_at: string
}

export interface Agent {
  agent_id: string
  name: string
  agent_type: string
  capabilities: string[]
  status: 'available' | 'busy' | 'offline'
}

export interface Tool {
  tool_id: string
  name: string
  category: string
  description: string
  input_schema: Record<string, unknown>
  output_schema: Record<string, unknown>
}

export interface SessionDatasourceAttachment {
  attachment_id: string
  session_id: string
  definition_id: string
  source_type: 'api' | 'file' | 'database' | 'stream' | 'custom'
  display_name?: string
  config: Record<string, unknown>
  context_preview?: Record<string, unknown>
  tags: string[]
  created_at: string
  created_by: string
  last_synced_at?: string | null
  sync_status: 'idle' | 'running' | 'error'
  visual_metadata?: Record<string, unknown>
}

export interface SessionACLAttachment {
  attachment_id: string
  session_id: string
  member_type: 'user' | 'group' | 'service'
  member_id: string
  display_name?: string
  role: 'owner' | 'editor' | 'viewer'
  status: 'pending' | 'active' | 'revoked'
  invited_email?: string
  expires_at?: string | null
  metadata?: Record<string, unknown>
  created_at: string
  created_by: string
  visual_metadata?: Record<string, unknown>
}

// ===== Real-time Sync =====
// PartykitMessage removed - dependency removed
// export interface PartykitMessage {
//   type: 'node_drag' | 'node_update' | 'edge_create' | 'edge_delete' | 'cursor_move' | 'lock_acquire' | 'lock_release'
//   userId: string
//   timestamp: string
//   data: unknown
// }

export interface DragLock {
  nodeId: string
  userId: string
  timestamp: string
  expiresAt: string
}

// ===== Marquee Selection =====
export interface MarqueeState {
  isActive: boolean
  startPoint: Position | null
  currentPoint: Position | null
  selectedNodeIds: string[]
}

export interface MarqueeBox {
  x: number
  y: number
  width: number
  height: number
}

// ===== Workspace State =====
export interface WorkspaceLayout {
  containers: ContainerVisualState[]  // Renamed from sessions
  viewport: {
    x: number
    y: number
    zoom: number
  }
  lastUpdated: string
}

// Legacy: UserPreferences for workspace settings (distinct from UserIdentityPreferences)
export interface UserPreferences {
  active_session_id?: string
  workspace_layout?: WorkspaceLayout
  theme: 'light' | 'dark'
  notifications_enabled: boolean
  auto_save: boolean
  
  // NEW: Link to user identity preferences
  identity?: UserIdentityPreferences
}
