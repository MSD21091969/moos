import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { WorkspaceState } from './types';
import { createCanvasSlice } from './canvas-slice';
import { createContainerSlice } from './container-slice';
import { createResourceSlice } from './resource-slice';
import { createUISlice } from './ui-slice';

export const useWorkspaceStore = create<WorkspaceState>()(
  devtools(
    persist(
      (...a) => ({
        ...createCanvasSlice(...a),
        ...createContainerSlice(...a),
        ...createResourceSlice(...a),
        ...createUISlice(...a),
      }),
      {
        name: 'workspace-storage',
        partialize: (state) => ({
          // Persist only what's needed
          nodes: state.nodes,
          edges: state.edges,
          containers: state.containers,
          viewport: state.viewport,
          sessionViewports: state.sessionViewports,
          userIdentity: state.userIdentity,
          visualMetadata: Array.from(state.visualMetadata.entries()), // Serialize Map
          containerRegistry: state.containerRegistry,
          userCustomTools: state.userCustomTools,
          userCustomAgents: state.userCustomAgents,
          availableTools: state.availableTools,
          availableAgents: state.availableAgents,
          toolsCache: state.toolsCache,
          agentsCache: state.agentsCache,
        }),
        onRehydrateStorage: () => (state) => {
          // MIGRATION: If old 'sessions' key exists, wipe and force fresh demo data
          if (typeof window !== 'undefined') {
            try {
              const raw = localStorage.getItem('workspace-storage');
              if (raw) {
                const parsed = JSON.parse(raw);
                const storedState = parsed.state || parsed;
                // Detect old schema: has 'sessions' but no 'containers'
                if (storedState.sessions && !storedState.containers) {
                  console.warn('⚠️ Detected old sessions[] schema - clearing for migration');
                  localStorage.removeItem('workspace-storage');
                  window.location.reload();
                  return;
                }
              }
            } catch (e) {
              console.warn('Failed to check localStorage schema:', e);
            }
          }

          // Hydration logic (Map deserialization)
          if (state && state.visualMetadata && Array.isArray(state.visualMetadata)) {
            state.visualMetadata = new Map(state.visualMetadata);
        }

        // If we're in backend-connected modes (non-demo), discard any stale
        // persisted canvas state so the backend becomes the single source of truth.
        const mode = import.meta.env.VITE_MODE || 'demo';
        if (state && mode !== 'demo') {
          state.nodes = [];
          state.edges = [];
          state.containers = [];
          state.sessionDatasources = {};
          state.sessionACLs = {};
          state.visualMetadata = new Map();
        }

        // Multi-tab sync: listen for localStorage changes from OTHER tabs
        if (typeof window !== 'undefined') {
          let isLocalWrite = false;
          
          // Intercept setState to track when THIS tab is writing
          const originalSetState = useWorkspaceStore.setState;
          useWorkspaceStore.setState = (...args: any[]) => {
            isLocalWrite = true;
            (originalSetState as any)(...args);
            setTimeout(() => { isLocalWrite = false; }, 100);
          };
          
          window.addEventListener('storage', (e) => {
            // Only sync if change came from DIFFERENT tab (not this one)
            if (e.key === 'workspace-storage' && e.newValue && !isLocalWrite) {
              console.log('🔄 Cross-tab sync: loading changes from another tab');
              try {
                const data = JSON.parse(e.newValue);
                const state = data.state || data;
                // Use originalSetState to avoid triggering isLocalWrite flag again
                originalSetState(state);
              } catch (error) {
                console.error('Failed to sync cross-tab localStorage change:', error);
              }
            }
          });
        }
      },
    },
    ),
    { name: 'WorkspaceStore', enabled: true }
  )
);

// Expose store for debugging/testing
if (typeof window !== 'undefined') {
  (window as any).__workspaceStore = useWorkspaceStore;
}


/**
 * Helper: Get session level (depth in hierarchy)
 * Works with both localStorage (Demo Mode) and backend data
 * @param sessionId - Session ID to calculate level for
 * @returns Level number (0 = workspace/root, 1 = L1, 2 = L2, etc.)
 */
export const getSessionLevel = (sessionId: string): number => {
  const containers = useWorkspaceStore.getState().containers;
  let level = 0;
  let current = containers.find(c => c.id === sessionId);
  
  // Traverse up the parent chain
  while (current?.parentSessionId) {
    level++;
    current = containers.find(c => c.id === current!.parentSessionId);
    
    // Safety: prevent infinite loops from circular references
    if (level > 10) {
      console.warn(`⚠️ Session ${sessionId} has suspiciously deep nesting (>10 levels)`);
      break;
    }
  }
  
  return level;
};

/**
 * Helper: Get full session path (ancestry)
 * @param sessionId - Session ID to get path for
 * @returns Array of session IDs from root to current session
 */
export const getSessionPath = (sessionId: string): string[] => {
  const containers = useWorkspaceStore.getState().containers;
  const path: string[] = [];
  let current = containers.find(c => c.id === sessionId);
  
  while (current) {
    path.unshift(current.id);
    current = current.parentSessionId 
      ? containers.find(c => c.id === current!.parentSessionId)
      : undefined;
    
    if (path.length > 10) break; // Safety
  }
  
  return path;
};

// Debug: Expose store to window for Playwright
if (typeof window !== 'undefined') {
  (window as any).__ZUSTAND_STORE__ = useWorkspaceStore;
}
