import { 
  applyNodeChanges, 
  applyEdgeChanges, 
  addEdge, 
  Connection, 
  EdgeChange, 
  NodeChange,
  Viewport
} from '@xyflow/react';
import { WorkspaceSliceCreator } from './types';
// import { generateId } from '../id-generator';
import * as api from '../api';
import { CustomNode, CustomEdge, CustomNodeData } from '../types';

export const createCanvasSlice: WorkspaceSliceCreator<any> = (set, get) => ({
  // State
  nodes: [],
  edges: [],
  viewport: { x: 0, y: 0, zoom: 1 },
  sessionViewports: {},
  selectedNodeIds: [],
  selectedEdgeIds: [],
  dragLocks: new Map(),

  // Actions
  onNodesChange: (changes: NodeChange[]) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes) as any,
    });
  },

  onEdgesChange: (changes: EdgeChange[]) => {
    set({
      edges: applyEdgeChanges(changes, get().edges) as any,
    });
  },

  onConnect: (connection: Connection) => {
    set({
      edges: addEdge(connection, get().edges) as any,
    });
  },

  setNodes: (nodes: CustomNode[]) => set({ nodes }),
  setEdges: (edges: CustomEdge[]) => set({ edges }),

  addNode: (node: CustomNode) => {
    set((state) => ({
      nodes: [...state.nodes, node],
    }));
  },

  deleteNodes: (nodeIds: string[]) => {
    set((state) => ({
      nodes: state.nodes.filter((node) => !nodeIds.includes(node.id)),
      edges: state.edges.filter(
        (edge) => !nodeIds.includes(edge.source) && !nodeIds.includes(edge.target)
      ),
      selectedNodeIds: state.selectedNodeIds.filter((id) => !nodeIds.includes(id)),
    }));
  },

  updateNodeData: (id: string, data: Partial<CustomNodeData>) => {
    set((state) => ({
      nodes: state.nodes.map((node) => {
        if (node.id === id) {
          return {
            ...node,
            data: { ...node.data, ...data },
          };
        }
        return node;
      }) as CustomNode[],
    }));
  },

  setViewport: (viewport: Viewport) => set({ viewport }),

  setSessionViewport: (sessionId: string, viewport: Viewport) => 
    set(state => ({ 
      sessionViewports: { ...state.sessionViewports, [sessionId]: viewport } 
    })),

  selectNode: (id: string, multi: boolean = false) => {
    set((state) => {
      const selected = multi 
        ? [...state.selectedNodeIds, id]
        : [id];
      return { selectedNodeIds: selected };
    });
  },

  setSelectedNodes: (ids: string[]) => set({ selectedNodeIds: ids }),

  clearSelection: () => set({ selectedNodeIds: [], selectedEdgeIds: [] }),

  // Drag Locks
  acquireDragLock: (nodeId: string, userId: string) => {
    const existingLock = get().dragLocks.get(nodeId);
    if (existingLock && existingLock.userId !== userId) {
      const now = new Date();
      const expiresAt = new Date(existingLock.expiresAt);
      if (now < expiresAt) {
        return false; // Lock held by another user
      }
    }

    const newLock = {
      nodeId,
      userId,
      timestamp: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 5000).toISOString(), // 5 second timeout
    };

    set((state) => ({
      dragLocks: new Map(state.dragLocks).set(nodeId, newLock),
    }));

    return true;
  },

  releaseDragLock: (nodeId: string) =>
    set((state) => {
      const newLocks = new Map(state.dragLocks);
      newLocks.delete(nodeId);
      return { dragLocks: newLocks };
    }),

  // Note: updateNodePosition logic with backend sync will be handled 
  // by a combined action or within the component that triggers it, 
  // or we can add a specific action here that calls API.
  // For now, we'll keep the visual update here.
  updateNodePosition: async (id: string, position: { x: number; y: number }) => {
    // 1. Optimistic update
    set((state) => ({
      nodes: state.nodes.map((node) => (node.id === id ? { ...node, position } : node)),
    }));

    const state = get();
    const { activeContainerId, activeContainerType, userSessionId, containerRegistry } = state;
    
    // Check mode
    const mode = import.meta.env.VITE_MODE || 'unknown';
    if (mode === 'demo') return;

    // 2. Sync to backend
    // We need to find the resource link to get the correct IDs
    // This logic relies on container-slice state (activeContainerId, etc.)
    
    // Helper to find resource in current context
    let resource;
    if (activeContainerId) {
      // Look in registry for active container
      const entry = containerRegistry[activeContainerId];
      if (entry) {
        resource = entry.resources.find(r => r.link_id === id || r.resource_id === id);
      }
    } else if (userSessionId) {
      // Look in registry for user session
      const entry = containerRegistry[userSessionId];
      if (entry) {
        resource = entry.resources.find(r => r.link_id === id || r.resource_id === id);
      }
    }

    if (resource) {
      const linkId = resource.link_id || id;
      const containerId = activeContainerId || userSessionId;
      const type = activeContainerId ? activeContainerType : 'usersession';

      if (containerId && type) {
        try {
          if (type === 'usersession') {
             await api.updateWorkspaceResource(containerId, linkId, {
               metadata: { x: position.x, y: position.y }
             });
          } else {
             await api.updateContainerResource(type, containerId, linkId, {
               metadata: { x: position.x, y: position.y }
             });
          }
        } catch (err) {
          console.error('Failed to sync node position:', err);
        }
      }
    }
  }
});
