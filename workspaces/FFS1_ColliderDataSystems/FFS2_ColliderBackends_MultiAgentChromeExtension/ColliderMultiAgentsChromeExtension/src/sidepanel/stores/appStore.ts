import { create } from "zustand";
import type { Application, AppNodeTree, ContextRole, DiscoveredTool } from "~/types";

interface AppState {
  // Existing tree/app state
  applications: Application[];
  selectedAppId: string | null;
  selectedNodePath: string | null;
  tree: AppNodeTree[];
  loading: boolean;
  error: string | null;

  // Context composer state (WorkspaceBrowser)
  selectedNodeIds: string[];
  contextRole: ContextRole;
  vectorQuery: string;
  discoveredTools: DiscoveredTool[];
  sessionId: string | null;
  composerOpen: boolean;

  // Existing actions
  setApplications: (apps: Application[]) => void;
  selectApp: (appId: string | null) => void;
  selectNode: (path: string | null) => void;
  setTree: (tree: AppNodeTree[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Composer actions
  toggleNodeSelection: (nodeId: string) => void;
  setContextRole: (role: ContextRole) => void;
  setVectorQuery: (q: string) => void;
  setDiscoveredTools: (tools: DiscoveredTool[]) => void;
  setSessionId: (id: string | null) => void;
  setComposerOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Existing defaults
  applications: [],
  selectedAppId: null,
  selectedNodePath: null,
  tree: [],
  loading: false,
  error: null,

  // Composer defaults
  selectedNodeIds: [],
  contextRole: "app_user",
  vectorQuery: "",
  discoveredTools: [],
  sessionId: null,
  composerOpen: true,

  // Existing actions
  setApplications: (applications) => set({ applications }),
  selectApp: (selectedAppId) =>
    set({
      selectedAppId,
      selectedNodePath: null,
      tree: [],
      selectedNodeIds: [],
      sessionId: null,
    }),
  selectNode: (selectedNodePath) => set({ selectedNodePath }),
  setTree: (tree) => set({ tree }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),

  // Composer actions
  toggleNodeSelection: (nodeId) => {
    const { selectedNodeIds } = get();
    set({
      selectedNodeIds: selectedNodeIds.includes(nodeId)
        ? selectedNodeIds.filter((id) => id !== nodeId)
        : [...selectedNodeIds, nodeId],
    });
  },
  setContextRole: (contextRole) => set({ contextRole, sessionId: null }),
  setVectorQuery: (vectorQuery) => set({ vectorQuery }),
  setDiscoveredTools: (discoveredTools) => set({ discoveredTools }),
  setSessionId: (sessionId) => set({ sessionId }),
  setComposerOpen: (composerOpen) => set({ composerOpen }),
}));
