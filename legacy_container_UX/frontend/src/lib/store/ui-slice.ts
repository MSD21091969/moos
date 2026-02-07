import { WorkspaceSliceCreator } from './types';
import { generateId } from '../id-generator';
import { DEFAULT_UX_VOCABULARY, UserIdentityPreferences, MarqueeState, VisualMetadata } from '../types';

export const createUISlice: WorkspaceSliceCreator<any> = (set, get) => ({
  // State
  hasInitialized: false,
  userIdentity: null,
  marquee: { isActive: false, startPoint: null, currentPoint: null, selectedNodeIds: [] },
  visualMetadata: new Map(),
  editingSessionId: null,
  editingSessionTab: 'details',
  stagedOperations: [],
  pendingOperations: [],

  // Actions - Initialization
  setInitialized: (initialized: boolean) => set({ hasInitialized: initialized }),

  // Actions - User Identity
  setUserIdentity: (identity: UserIdentityPreferences) => set({ userIdentity: identity }),
  
  getUxVocabulary: () => {
    return get().userIdentity?.uxVocabulary || DEFAULT_UX_VOCABULARY;
  },

  // Actions - Marquee
  setMarquee: (marquee: MarqueeState) => set({ marquee }),

  // Actions - Visual Metadata
  setVisualMetadata: (sessionId: string, metadata: VisualMetadata) => {
    set((state) => {
      const newMap = new Map(state.visualMetadata);
      newMap.set(sessionId, metadata);
      return { visualMetadata: newMap };
    });
  },

  updateVisualMetadata: (sessionId: string, updates: Partial<VisualMetadata>) => {
    set((state) => {
      const newMap = new Map(state.visualMetadata);
      const current = newMap.get(sessionId) || { 
        position: { x: 0, y: 0 }, 
        size: { width: 0, height: 0 }, 
        color: '#000000', 
        icon: '', 
        isExpanded: false 
      };
      newMap.set(sessionId, { ...current, ...updates });
      return { visualMetadata: newMap };
    });
  },

  getVisualMetadata: (sessionId: string) => {
    return get().visualMetadata.get(sessionId);
  },

  // Actions - Editing Session
  setEditingSessionId: (sessionId: string | null, tab: 'details' | 'files' | 'dataflow' = 'details') => set({ editingSessionId: sessionId, editingSessionTab: tab }),
  setEditingSessionTab: (tab: 'details' | 'files' | 'dataflow') => set({ editingSessionTab: tab }),

  // Actions - Staged Operations
  addStagedOperation: (operation: any) =>
    set((state) => ({
      stagedOperations: [
        ...state.stagedOperations,
        {
          ...operation,
          id: generateId('op'),
          timestamp: new Date().toISOString(),
          status: 'pending' as const,
        },
      ],
    })),

  removeStagedOperation: (id: string) =>
    set((state) => ({
      stagedOperations: state.stagedOperations.filter((op) => op.id !== id),
    })),

  updateStagedOperation: (id: string, updates: any) =>
    set((state) => ({
      stagedOperations: state.stagedOperations.map((op) =>
        op.id === id ? { ...op, ...updates } : op
      ),
    })),

  executeStagedOperations: async () => {
    // TODO: Implement batch execution logic
    console.warn('executeStagedOperations not implemented yet');
  },

  clearStagedOperations: () => set({ stagedOperations: [] }),

  // Actions - Layout
  applyLayout: (layoutType: string) => {
    // Apply basic layout to nodes
    const nodes = get().nodes;
    if (!nodes || nodes.length === 0) return;
    
    let newNodes = [...nodes];
    const spacing = 180;
    
    switch (layoutType) {
      case 'grid': {
        const cols = Math.ceil(Math.sqrt(newNodes.length));
        newNodes = newNodes.map((node, i) => ({
          ...node,
          position: {
            x: (i % cols) * spacing,
            y: Math.floor(i / cols) * spacing,
          }
        }));
        break;
      }
      case 'horizontal': {
        newNodes = newNodes.map((node, i) => ({
          ...node,
          position: { x: i * spacing, y: 100 }
        }));
        break;
      }
      case 'vertical': {
        newNodes = newNodes.map((node, i) => ({
          ...node,
          position: { x: 100, y: i * spacing }
        }));
        break;
      }
      default:
        console.log('Unknown layout:', layoutType);
        return;
    }
    
    set({ nodes: newNodes });
  },

  // Actions - Pending Operations
  enqueuePendingOperation: (operation: any) => {
    const opId = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : generateId('pending_op');
    set((state) => ({
      pendingOperations: [
        ...state.pendingOperations,
        {
          id: opId,
          status: 'pending',
          retries: 0,
          createdAt: new Date().toISOString(),
          ...operation,
        },
      ],
    }));
    return opId;
  },

  updatePendingOperation: (id: string, updates: any) =>
    set((state) => ({
      pendingOperations: state.pendingOperations.map((op) =>
        op.id === id ? { ...op, ...updates } : op
      ),
    })),

  removePendingOperation: (id: string) =>
    set((state) => ({
      pendingOperations: state.pendingOperations.filter((op) => op.id !== id),
    })),
});

