/**
 * Graph Store — XYFlow nodes/edges state
 *
 * Manages the workspace graph visualization state.
 * Nodes map 1:1 to Collider NodeContainer tree nodes.
 */

import { create } from "zustand";
import type { Node, Edge, OnNodesChange, OnEdgesChange } from "@xyflow/react";
import { applyNodeChanges, applyEdgeChanges } from "@xyflow/react";

type GraphMorphism =
  | {
    morphism_type: "ADD_NODE_CONTAINER";
    node_type: string;
    temp_urn: string;
    properties?: Record<string, unknown>;
  }
  | {
    morphism_type: "LINK_NODES";
    source_urn: string;
    target_urn: string;
    edge_type: string;
  }
  | {
    morphism_type: "UPDATE_NODE_KERNEL";
    urn: string;
    kernel_data: Record<string, unknown>;
  }
  | {
    morphism_type: "DELETE_EDGE";
    source_urn: string;
    target_urn: string;
    edge_type: string;
  };

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
  applyMorphisms: (morphisms: unknown[]) => void;
  setActiveState: (nodes: unknown[], edges: unknown[]) => void;
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
  applyMorphisms: (morphisms) =>
    set((state) => {
      const nextNodes = [...state.nodes];
      const nextEdges = [...state.edges];

      const typed = morphisms.filter(
        (morphism): morphism is GraphMorphism =>
          typeof morphism === "object" &&
          morphism !== null &&
          "morphism_type" in morphism,
      );

      for (const morphism of typed) {
        switch (morphism.morphism_type) {
          case "ADD_NODE_CONTAINER": {
            const id = morphism.temp_urn;
            if (nextNodes.some((node) => node.id === id)) {
              break;
            }
            const index = nextNodes.length;
            const props = morphism.properties ?? {};
            const label =
              typeof props.label === "string"
                ? props.label
                : typeof props.thought === "string"
                  ? props.thought
                  : id;

            nextNodes.push({
              id,
              type: "nodeCard",
              position: { x: 40 + (index % 6) * 260, y: 40 + Math.floor(index / 6) * 140 },
              data: {
                nodeId: id,
                path: id,
                label,
                domain: morphism.node_type,
                hasContainer: true,
                skillCount: 0,
                toolCount: 0,
                isSelected: false,
              },
            });
            break;
          }
          case "LINK_NODES": {
            const edgeId = `e-${morphism.source_urn}-${morphism.target_urn}-${morphism.edge_type}`;
            if (nextEdges.some((edge) => edge.id === edgeId)) {
              break;
            }
            nextEdges.push({
              id: edgeId,
              source: morphism.source_urn,
              target: morphism.target_urn,
              type: "smoothstep",
              animated: false,
              data: { edge_type: morphism.edge_type },
            });
            break;
          }
          case "UPDATE_NODE_KERNEL": {
            const idx = nextNodes.findIndex((node) => node.id === morphism.urn);
            if (idx >= 0) {
              const existing = nextNodes[idx];
              nextNodes[idx] = {
                ...existing,
                data: {
                  ...existing.data,
                  ...(morphism.kernel_data as Partial<NodeData>),
                },
              };
            }
            break;
          }
          case "DELETE_EDGE": {
            for (let i = nextEdges.length - 1; i >= 0; i--) {
              const edge = nextEdges[i];
              if (edge.source === morphism.source_urn && edge.target === morphism.target_urn) {
                nextEdges.splice(i, 1);
              }
            }
            break;
          }
        }
      }

      return { nodes: nextNodes, edges: nextEdges };
    }),
  setActiveState: (nodes, edges) => set({ nodes: nodes as Node<NodeData>[], edges: edges as Edge[] }),
  reset: () => set({ nodes: [], edges: [], loading: false, error: null }),
}));
