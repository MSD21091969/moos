import { StateCreator } from 'zustand';
import { 
  Viewport,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
} from '@xyflow/react';
import { 
  Container, 
  ResourceLink, 
  ContainerType, 
} from '../api';
import { 
  CustomNode, 
  CustomEdge, 
  CustomNodeData,
  ContainerVisualState, 
  UserIdentityPreferences,
  MarqueeState,
  DragLock,
  VisualMetadata
} from '../types';
import { 
  ToolDefinition, 
  AgentDefinition,
  CustomToolDefinition,
  CustomAgentDefinition,
  CreateToolPayload,
  CreateAgentPayload
} from '../api-types';

// =============================================================================
// Slice Interfaces
// =============================================================================

export interface CanvasSlice {
  // State
  nodes: CustomNode[];
  edges: CustomEdge[];
  viewport: Viewport;
  sessionViewports: Record<string, Viewport>; // Per-session viewport memory
  selectedNodeIds: string[];
  selectedEdgeIds: string[];
  dragLocks: Map<string, DragLock>;
  
  // Actions
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  setNodes: (nodes: CustomNode[]) => void;
  setEdges: (edges: CustomEdge[]) => void;
  addNode: (node: CustomNode) => void;
  deleteNodes: (nodeIds: string[]) => void;
  updateNodeData: (id: string, data: Partial<CustomNodeData>) => void;
  updateNodePosition: (id: string, position: { x: number; y: number }) => void;
  setViewport: (viewport: Viewport) => void;
  setSessionViewport: (sessionId: string, viewport: Viewport) => void;
  selectNode: (id: string, multi?: boolean) => void;
  setSelectedNodes: (ids: string[]) => void;
  clearSelection: () => void;
}

export interface ContainerSlice {
  // State
  containers: ContainerVisualState[]; // Flat list of all visual containers
  activeContainerId: string | null;   // Current "zoomed in" container
  activeContainerType: ContainerType | null;
  userSessionId: string | null;       // Root user session ID
  
  // Legacy support
  sessionDatasources: Record<string, any[]>;
  sessionACLs: Record<string, any[]>;

  // Registry Cache (Client-side "Database")
  containerRegistry: Record<string, {
    container: Container | null;
    resources: ResourceLink[];
    timestamp: number;
  }>;
  
  // Computed / Navigation
  breadcrumbs: { id: string; title: string; type: string }[];
  
  // Actions
  loadContainer: (id: string | null, type: ContainerType, forceRefresh?: boolean) => Promise<void>;
  loadUserSession: (userId: string) => Promise<void>;
  setActiveContainer: (id: string | null) => void;
  
  // V4 Compatibility Actions
  loadWorkspaceResources: () => Promise<void>;
  addToolToSessionV4: (sessionId: string, toolId: string, data: any) => Promise<void>;
  addAgentToSessionV4: (sessionId: string, agentId: string, data: any) => Promise<void>;
  addSourceToSessionV4: (sessionId: string, sourceId: string, data: any) => Promise<void>;
  
  // CRUD
  setDemoData: (data: { containers: ContainerVisualState[], nodes: CustomNode[], registry: Record<string, any> }) => void;
  createContainer: (
    type: ContainerType, 
    parentId: string, 
    data: { title: string; description?: string; position?: { x: number; y: number } }
  ) => Promise<string>;
  
  createChildSession: (
    parentId: string,
    title: string,
    position: { x: number; y: number },
    description?: string
  ) => Promise<string>;
  
  updateContainer: (id: string, updates: Partial<Container>) => Promise<void>;
  deleteContainer: (id: string) => Promise<void>;
  
  // Resource Management
  addResourceLink: (containerId: string, resource: Partial<ResourceLink>) => Promise<void>;
  updateResourceLink: (containerId: string, linkId: string, updates: Partial<ResourceLink>) => Promise<void>;
  removeResourceLink: (containerId: string, linkId: string) => Promise<void>;
  
  // Real-time Sync
  handleContainerEvent: (event: any) => void;
  
  // Library (Orphan Containers)
  loadOrphans: (type: ContainerType) => Promise<Container[]>;
}

export interface ResourceSlice {
  // State - Discovery & Definitions
  availableTools: ToolDefinition[];
  availableAgents: AgentDefinition[];
  userCustomTools: CustomToolDefinition[];
  userCustomAgents: CustomAgentDefinition[];
  
  // Caches
  toolsCache: { timestamp: number; category?: string } | null;
  agentsCache: { timestamp: number; sessionId?: string | null; search?: string } | null;
  
  // Actions
  loadAvailableTools: (category?: string, forceRefresh?: boolean) => Promise<void>;
  loadAvailableAgents: (sessionId?: string | null, search?: string, forceRefresh?: boolean) => Promise<void>;
  loadUserCustomDefinitions: (userId: string) => Promise<void>;
  createUserCustomTool: (tool: CreateToolPayload) => Promise<void>;
  createUserCustomAgent: (agent: CreateAgentPayload) => Promise<void>;
}

export interface UISlice {
  // State
  hasInitialized: boolean;
  userIdentity: UserIdentityPreferences | null;
  visualMetadata: Map<string, VisualMetadata>; // session_id -> visual attrs
  marquee: MarqueeState;
  
  // UI Flags
  editingSessionId: string | null;
  editingSessionTab: 'details' | 'files' | 'dataflow';
  
  // Operations
  stagedOperations: any[];
  pendingOperations: any[];
  
  // Actions
  setInitialized: (initialized: boolean) => void;
  setUserIdentity: (identity: UserIdentityPreferences) => void;
  setVisualMetadata: (id: string, metadata: VisualMetadata) => void;
  updateVisualMetadata: (id: string, updates: Partial<VisualMetadata>) => void;
  getVisualMetadata: (id: string) => VisualMetadata | undefined;
  setMarquee: (marquee: MarqueeState) => void;
  setEditingSessionId: (id: string | null, tab?: 'details' | 'files' | 'dataflow') => void;
  setEditingSessionTab: (tab: 'details' | 'files' | 'dataflow') => void;
  
  // Layout Action
  applyLayout: (layoutType: string) => void;
  
  // Operations Actions
  addStagedOperation: (op: any) => void;
  removeStagedOperation: (id: string) => void;
  updateStagedOperation: (id: string, updates: any) => void;
  executeStagedOperations: () => Promise<void>;
  clearStagedOperations: () => void;
  
  enqueuePendingOperation: (op: any) => string;
  updatePendingOperation: (id: string, updates: any) => void;
  removePendingOperation: (id: string) => void;

  // Helper to resolve Tier/Vocabulary
  getUxVocabulary: () => UserIdentityPreferences['uxVocabulary'];
}

// =============================================================================
// Combined Store Type
// =============================================================================

export type WorkspaceState = CanvasSlice & ContainerSlice & ResourceSlice & UISlice;

export type WorkspaceSliceCreator<T> = StateCreator<
  WorkspaceState,
  [['zustand/persist', unknown]],
  [],
  T
>;
