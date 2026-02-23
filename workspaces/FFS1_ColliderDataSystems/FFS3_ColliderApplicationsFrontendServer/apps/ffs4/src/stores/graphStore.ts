/**
 * Graph Store — XYFlow nodes/edges state
 *
 * Manages the workspace graph visualization state.
 * Nodes map 1:1 to Collider NodeContainer tree nodes.
 */

import { create } from "zustand";
import type { Node, Edge, OnNodesChange, OnEdgesChange } from "@xyflow/react";
import { applyNodeChanges, applyEdgeChanges } from "@xyflow/react";

export interface NodeData extends Record<string, unknown> {
  nodeId: string;
  path: string;
  label: string;
  domain?: string;
  emoji?: string;
  hasContainer: boolean;
  skillCount: number;
  toolCount: number;
  isSelected: boolean;
}

interface GraphState {
  nodes: Node<NodeData>[];
  edges: Edge[];
  loading: boolean;
  error: string | null;

  setNodes: (nodes: Node<NodeData>[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: OnNodesChange<Node<NodeData>>;
  onEdgesChange: OnEdgesChange;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useGraphStore = create<GraphState>((set, get) => ({
  nodes: [],
  edges: [],
  loading: false,
  error: null,

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  onNodesChange: (changes) => {
    set({ nodes: applyNodeChanges(changes, get().nodes) });
  },

  onEdgesChange: (changes) => {
    set({ edges: applyEdgeChanges(changes, get().edges) });
  },

  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  reset: () => set({ nodes: [], edges: [], loading: false, error: null }),
}));
