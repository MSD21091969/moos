import { create } from "zustand";
import type { Application, AppNodeTree, ContextRole, DiscoveredTool } from "~/types";

interface SessionPreview {
  node_count: number;
  skill_count: number;
  tool_count: number;
  role: string;
  vector_matches: number;
}

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
  nanoClawWsUrl: string | null;  // NanoClawBridge WebSocket URL for direct chat
  composerOpen: boolean;
  inheritAncestors: boolean;

  // Root agent session state
  rootSessionId: string | null;
  rootSessionPreview: SessionPreview | null;

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
  setNanoClawWsUrl: (url: string | null) => void;
  setComposerOpen: (open: boolean) => void;
  setInheritAncestors: (inherit: boolean) => void;

  // Root agent actions
  setRootSessionId: (id: string | null) => void;
  setRootSessionPreview: (preview: SessionPreview | null) => void;
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
  nanoClawWsUrl: null,
  composerOpen: true,
  inheritAncestors: false,

  // Root agent defaults
  rootSessionId: null,
  rootSessionPreview: null,

  // Existing actions
  setApplications: (applications) => set({ applications }),
  selectApp: (selectedAppId) =>
    set({
      selectedAppId,
      selectedNodePath: null,
      tree: [],
      selectedNodeIds: [],
      sessionId: null,
      nanoClawWsUrl: null,
      rootSessionId: null,
      rootSessionPreview: null,
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
  setNanoClawWsUrl: (nanoClawWsUrl) => set({ nanoClawWsUrl }),
  setComposerOpen: (composerOpen) => set({ composerOpen }),
  setInheritAncestors: (inheritAncestors) => set({ inheritAncestors }),

  // Root agent actions
  setRootSessionId: (rootSessionId) => set({ rootSessionId }),
  setRootSessionPreview: (rootSessionPreview) => set({ rootSessionPreview }),
}));
