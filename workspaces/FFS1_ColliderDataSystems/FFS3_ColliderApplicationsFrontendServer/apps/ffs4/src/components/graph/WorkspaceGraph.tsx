/**
 * WorkspaceGraph — ReactFlow canvas for workspace visualization
 *
 * Renders the node tree as an interactive graph.
 * Users select nodes via checkboxes to compose agent context.
 */

import { useCallback, useEffect, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useGraphStore } from "../../stores/graphStore";
import { useContextStore } from "../../stores/contextStore";
import { NodeCard } from "./NodeCard";

const nodeTypes: NodeTypes = {
  nodeCard: NodeCard,
};

interface WorkspaceGraphProps {
  appId: string | null;
}

export function WorkspaceGraph({ appId }: WorkspaceGraphProps) {
  const { nodes, edges, onNodesChange, onEdgesChange, loading, error } =
    useGraphStore();
  const selectedNodeIds = useContextStore((s) => s.selectedNodeIds);

  // We rely on the WebSocket in App.tsx to keep 'nodes' and 'edges' populated via setActiveState

  // Update node selection state when selectedNodeIds change
  const nodesWithSelection = useMemo(() => {
    const selectedSet = new Set(selectedNodeIds);
    return nodes.map((n) => ({
      ...n,
      data: { ...n.data, isSelected: selectedSet.has(n.id) },
    }));
  }, [nodes, selectedNodeIds]);

  if (!appId) {
    return (
      <div style={{ padding: 24, color: "#6b7280", textAlign: "center" }}>
        Select an application to view the workspace graph.
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ padding: 24, color: "#6b7280", textAlign: "center" }}>
        Loading workspace graph...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24, color: "#ef4444", textAlign: "center" }}>
        Error: {error}
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height: "100%" }}>
      <ReactFlow
        nodes={nodesWithSelection}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
      >
        <Background gap={16} size={1} color="#f0f0f0" />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const data = node.data as { isSelected?: boolean };
            return data?.isSelected ? "#3b82f6" : "#e5e7eb";
          }}
          style={{ background: "#fafafa" }}
        />
      </ReactFlow>
    </div>
  );
}
