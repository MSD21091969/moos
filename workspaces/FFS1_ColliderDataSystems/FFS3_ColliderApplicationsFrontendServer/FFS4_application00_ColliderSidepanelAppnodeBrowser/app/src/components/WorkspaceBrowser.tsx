import { ReactFlow, MiniMap, Controls, Background, Node, Edge } from '@xyflow/react';

interface WorkspaceBrowserProps {
  nodes: Node[];
  edges: Edge[];
  onNodeClick?: (event: React.MouseEvent, node: Node) => void;
}

export function WorkspaceBrowser({ nodes, edges, onNodeClick }: WorkspaceBrowserProps) {
  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={onNodeClick}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
