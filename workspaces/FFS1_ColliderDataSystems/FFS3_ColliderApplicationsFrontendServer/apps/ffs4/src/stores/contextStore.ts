/**
 * Context Store — Selected nodes + composition state
 *
 * Manages which nodes the user has selected for context composition,
 * the active role, and the composed session state.
 */

import { create } from "zustand";

export type ContextRole =
  | "app_user"
  | "app_admin"
  | "collider_admin"
  | "superadmin";

interface ContextState {
  /** Currently selected app */
  appId: string | null;
  /** Node IDs selected for context composition (checkboxes in graph) */
  selectedNodeIds: string[];
  /** Active role for the session */
  role: ContextRole;
  /** Optional vector query for tool discovery */
  vectorQuery: string;
  /** Whether to inherit ancestor context */
  inheritAncestors: boolean;
  /** Composing state */
  composing: boolean;

  setAppId: (appId: string | null) => void;
  toggleNode: (nodeId: string) => void;
  setSelectedNodeIds: (ids: string[]) => void;
  setRole: (role: ContextRole) => void;
  setVectorQuery: (query: string) => void;
  setInheritAncestors: (v: boolean) => void;
  setComposing: (composing: boolean) => void;
  reset: () => void;
}

export const useContextStore = create<ContextState>((set) => ({
  appId: null,
  selectedNodeIds: [],
  role: "app_user",
  vectorQuery: "",
  inheritAncestors: true,
  composing: false,

  setAppId: (appId) => set({ appId }),

  toggleNode: (nodeId) =>
    set((state) => {
      const has = state.selectedNodeIds.includes(nodeId);
      return {
        selectedNodeIds: has
          ? state.selectedNodeIds.filter((id) => id !== nodeId)
          : [...state.selectedNodeIds, nodeId],
      };
    }),

  setSelectedNodeIds: (ids) => set({ selectedNodeIds: ids }),
  setRole: (role) => set({ role }),
  setVectorQuery: (query) => set({ vectorQuery: query }),
  setInheritAncestors: (v) => set({ inheritAncestors: v }),
  setComposing: (composing) => set({ composing }),
  reset: () =>
    set({
      appId: null,
      selectedNodeIds: [],
      role: "app_user",
      vectorQuery: "",
      inheritAncestors: true,
      composing: false,
    }),
}));
