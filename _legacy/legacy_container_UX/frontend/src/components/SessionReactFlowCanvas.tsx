import { useMemo, useState, useCallback, useEffect } from 'react'
import type { MouseEvent as ReactMouseEvent } from 'react'
import { useParams } from 'react-router-dom'
import {
  ReactFlow,
  Background,
  MiniMap,
  Controls,
  NodeTypes,
  useNodesState,
  useEdgesState,
  Node,
  ReactFlowProvider,
  Viewport,
} from '@xyflow/react'
import { useWorkspaceStore } from '../lib/workspace-store'
import ObjectNode from './nodes/ObjectNode'
import AgentNode from './nodes/AgentNode'
import ToolNode from './nodes/ToolNode'
import ChildSessionNode from './nodes/ChildSessionNode'
import { BuildingModeContextMenu } from './BuildingModeContextMenu'
import { SessionContextMenu } from './SessionContextMenu'

interface SessionSpaceCanvasProps {
  className?: string
  onNodeDoubleClick?: (event: React.MouseEvent, node: any) => void
}

const nodeTypes: NodeTypes = {
  session: ChildSessionNode,
  object: ObjectNode,
  agent: AgentNode,
  tool: ToolNode,
}

function SessionSpaceCanvasInner({ className = '', onNodeDoubleClick }: SessionSpaceCanvasProps) {
  const { sessionId } = useParams<{ sessionId: string }>()
  const allNodes = useWorkspaceStore(state => state.nodes)
  const allEdges = useWorkspaceStore(state => state.edges)
  const updateNodeData = useWorkspaceStore(state => state.updateNodeData)
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null)
  const [sessionMenu, setSessionMenu] = useState<{ sessionId: string; x: number; y: number } | null>(null)
  
  // Restore viewport on mount (moved to onInit below)
  
  const filteredNodes = useMemo(() => {
    return allNodes.filter(n => {
      const data = n.data as any;
      
      if (n.type === 'session' && data?.parentSessionId === sessionId) {
        return true;
      }
      
      if (n.type === 'session') return false;
      
      return data?.sessionId === sessionId;
    });
  }, [allNodes, sessionId])
  
  const filteredEdges = useMemo(() => {
    const nodeIds = new Set(filteredNodes.map(n => n.id))
    return allEdges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target))
  }, [allEdges, filteredNodes])

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>(filteredNodes as Node[])
  const [edges, setEdges, onEdgesChange] = useEdgesState(filteredEdges)

  useEffect(() => {
    setNodes(filteredNodes as Node[])
  }, [filteredNodes, setNodes])

  useEffect(() => {
    setEdges(filteredEdges)
  }, [filteredEdges, setEdges])

  const handleNodeDragStop = useCallback(
    (_: React.MouseEvent, node: Node) => {
      console.log(`📍 SessionView: ${node.id} → (${Math.round(node.position.x)}, ${Math.round(node.position.y)})`);
      updateNodeData(node.id, { position: node.position });
    },
    [updateNodeData]
  )

  type PaneContextEvent = MouseEvent | ReactMouseEvent<Element, MouseEvent>

  const handlePaneContextMenu = useCallback((event: PaneContextEvent) => {
    event.preventDefault()
    setContextMenu({ x: event.clientX, y: event.clientY })
  }, [])

  const handlePaneClick = useCallback(() => {
    setContextMenu(null)
    setSessionMenu(null)
  }, [])

  const handleNodeContextMenu = useCallback((event: React.MouseEvent, node: any) => {
    event.preventDefault()
    event.stopPropagation()
    
    if (node.type === 'session' || node.type === 'agent' || node.type === 'tool') {
      setSessionMenu({ sessionId: node.id, x: event.clientX, y: event.clientY - 58 })
    } else {
      // For other nodes, we could show a generic menu or nothing
      // Currently just preventing default browser menu
    }
  }, [])

  const handleViewportChange = useCallback(
    (viewport: Viewport) => {
      if (sessionId) {
        useWorkspaceStore.getState().setSessionViewport(sessionId, viewport)
      }
    },
    [sessionId]
  )

  const handleInit = useCallback(
    (reactFlowInstance: any) => {
      console.log(`🎨 Canvas Init: ${sessionId}`);
      if (sessionId) {
        const savedViewport = useWorkspaceStore.getState().sessionViewports[sessionId]
        console.log(`  - Saved Viewport:`, savedViewport);
        if (savedViewport) {
          reactFlowInstance.setViewport(savedViewport, { duration: 0 })
        } else {
          // Explicitly reset if no saved viewport (though remount should do this)
          console.log(`  - No saved viewport, fitting view`);
          // Wait a tick for nodes to render
          setTimeout(() => {
            reactFlowInstance.fitView({ padding: 0.2, duration: 200 });
          }, 50);
        }
      }
    },
    [sessionId]
  )
  
  useEffect(() => {
    console.log(`🔄 Canvas Mount: ${sessionId}`);
    return () => console.log(`❌ Canvas Unmount: ${sessionId}`);
  }, [sessionId]);
  
  return (
    <div className={`relative w-full h-full ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={handleNodeDragStop}
        onInit={handleInit}
        fitView
        minZoom={0.5}
        maxZoom={1.5}
        snapToGrid
        snapGrid={[15, 15]}
        nodesDraggable={true}
        nodesConnectable={true}
        elementsSelectable={true}
        panOnDrag={true}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{
          animated: true,
          style: { stroke: '#3b82f6', strokeWidth: 2 },
        }}
        onPaneContextMenu={handlePaneContextMenu}
        onPaneClick={handlePaneClick}
        onNodeDoubleClick={onNodeDoubleClick}
        onNodeContextMenu={handleNodeContextMenu}
        onViewportChange={handleViewportChange}
      >
        <Background gap={15} color="#1e293b" />
        <Controls
          showInteractive={false}
          position="bottom-right"
          className="bg-[rgba(15,23,42,0.90)] border border-slate-700"
        />
        <MiniMap
          nodeColor={(node) => {
            if (node.type === 'agent') return '#10b981'
            if (node.type === 'tool') return '#f59e0b'
            return '#3b82f6'
          }}
          className="bg-[rgba(15,23,42,0.90)] border border-slate-700"
        />

        {/* Building Mode Context Menu */}
        {contextMenu && sessionId && (
          <BuildingModeContextMenu
            x={contextMenu.x}
            y={contextMenu.y}
            sessionId={sessionId}
            onClose={() => setContextMenu(null)}
          />
        )}

        {/* Session Context Menu (for child sessions) */}
        {sessionMenu && (
          <SessionContextMenu
            sessionId={sessionMenu.sessionId}
            position={{ x: sessionMenu.x, y: sessionMenu.y }}
            onClose={() => setSessionMenu(null)}
            onOpenPicker={(type) => console.warn('Picker not implemented in SessionReactFlowCanvas', type)}
          />
        )}
      </ReactFlow>
    </div>
  )
}

export default function SessionSpaceCanvas(props: SessionSpaceCanvasProps) {
  return (
    <ReactFlowProvider>
      <SessionSpaceCanvasInner {...props} />
    </ReactFlowProvider>
  )
}
