/**
 * useGraphData — Fetch node tree + convert to XYFlow nodes/edges
 *
 * Transforms Collider's tree structure into XYFlow's flat node/edge arrays
 * with automatic hierarchical layout.
 */

import { useCallback } from "react";
import type { Node, Edge } from "@xyflow/react";
import { getNodeTree, type TreeNode } from "../lib/api";
import { useGraphStore, type NodeData } from "../stores/graphStore";
import { useContextStore } from "../stores/contextStore";

const NODE_WIDTH = 220;
const NODE_HEIGHT = 80;
const H_GAP = 40;
const V_GAP = 60;

/**
 * Recursively flatten a tree into XYFlow nodes + edges.
 * Uses a simple top-down layout algorithm.
 */
function treeToFlow(
  tree: TreeNode[],
  parentId: string | null,
  depth: number,
  siblingIndex: number,
  selectedIds: Set<string>,
): { nodes: Node<NodeData>[]; edges: Edge[] } {
  const nodes: Node<NodeData>[] = [];
  const edges: Edge[] = [];

  for (let i = 0; i < tree.length; i++) {
    const treeNode = tree[i];
    const x = (siblingIndex + i) * (NODE_WIDTH + H_GAP);
    const y = depth * (NODE_HEIGHT + V_GAP);

    const flowNode: Node<NodeData> = {
      id: treeNode.id,
      type: "nodeCard",
      position: { x, y },
      data: {
        nodeId: treeNode.id,
        path: treeNode.path,
        label: treeNode.path.split("/").pop() ?? treeNode.path,
        domain: treeNode.container?.config?.domain,
        hasContainer: !!treeNode.container,
        skillCount: treeNode.container?.skills?.length ?? 0,
        toolCount: treeNode.container?.tools?.length ?? 0,
        isSelected: selectedIds.has(treeNode.id),
      },
    };

    nodes.push(flowNode);

    if (parentId) {
      edges.push({
        id: `e-${parentId}-${treeNode.id}`,
        source: parentId,
        target: treeNode.id,
        type: "smoothstep",
        animated: false,
      });
    }

    if (treeNode.children?.length) {
      const childResult = treeToFlow(
        treeNode.children,
        treeNode.id,
        depth + 1,
        siblingIndex + i,
        selectedIds,
      );
      nodes.push(...childResult.nodes);
      edges.push(...childResult.edges);
    }
  }

  return { nodes, edges };
}

export function useGraphData() {
  const { setNodes, setEdges, setLoading, setError } = useGraphStore();
  const selectedNodeIds = useContextStore((s) => s.selectedNodeIds);

  const loadTree = useCallback(
    async (appId: string) => {
      setLoading(true);
      setError(null);

      try {
        const tree = await getNodeTree(appId);
        const selectedSet = new Set(selectedNodeIds);
        const { nodes, edges } = treeToFlow(tree, null, 0, 0, selectedSet);
        setNodes(nodes);
        setEdges(edges);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        setError(msg);
      } finally {
        setLoading(false);
      }
    },
    [setNodes, setEdges, setLoading, setError, selectedNodeIds],
  );

  return { loadTree };
}
