import { create } from "zustand";
import type { Application, AppNodeTree } from "~/types";

interface AppState {
  applications: Application[];
  selectedAppId: string | null;
  selectedNodePath: string | null;
  tree: AppNodeTree[];
  loading: boolean;
  error: string | null;
  setApplications: (apps: Application[]) => void;
  selectApp: (appId: string | null) => void;
  selectNode: (path: string | null) => void;
  setTree: (tree: AppNodeTree[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  applications: [],
  selectedAppId: null,
  selectedNodePath: null,
  tree: [],
  loading: false,
  error: null,
  setApplications: (applications) => set({ applications }),
  selectApp: (selectedAppId) =>
    set({ selectedAppId, selectedNodePath: null, tree: [] }),
  selectNode: (selectedNodePath) => set({ selectedNodePath }),
  setTree: (tree) => set({ tree }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));
