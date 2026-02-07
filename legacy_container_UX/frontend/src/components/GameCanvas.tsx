import {
  addEdge,
  Background,
  Connection,
  Edge,
  MiniMap,
  Node,
  ReactFlow,
  ReactFlowProvider,
  SelectionMode,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useCallback, useEffect, useState, useRef } from 'react';
import ContainerNode from '../components/nodes/ContainerNode';
import { DatasourceNode } from '../components/nodes/DatasourceNode';
import ObjectNode from '../components/nodes/ObjectNode';
import PreviewNode from '../components/nodes/PreviewNode';
import { UserStubNode } from '../components/nodes/UserStubNode';
import { useWorkspaceStore } from '../lib/workspace-store';
// import { resourceLinkToNode } from '../lib/api-v4';
import { ContextMenu } from './ContextMenu';
import { StagingQueuePanel } from './StagingQueuePanel';
import { SessionContextMenu } from './SessionContextMenu';
import { ContainerPickerModal } from './ContainerPickerModal';
import * as api from '../lib/api';
import { isDemoMode } from '../lib/env';

// Unified: All containers use ContainerNode
const nodeTypes = {
  session: ContainerNode,
  object: ObjectNode,
  agent: ContainerNode,
  tool: ContainerNode,
  datasource: DatasourceNode,
  source: ContainerNode,
  preview: PreviewNode,
  user: UserStubNode,
};

interface GameCanvasProps {
  className?: string;
  workspaceView?: boolean; // Filter to show only sessions + their children
  onNodeDoubleClick?: (event: React.MouseEvent, node: Node) => void;
}

// Inner component that uses useReactFlow (must be inside ReactFlowProvider)
function GameCanvasInner({ className = '', workspaceView = false, onNodeDoubleClick }: GameCanvasProps) {
  const { setViewport: flowSetViewport, fitView } = useReactFlow();
  const {
    nodes: storeNodes,
    edges: storeEdges,
    viewport,
    setViewport,
    sessionViewports,
    setSessionViewport,
    // addStagedOperation, // TODO: Wire up batch operations UI
    setSelectedNodes,
    updateNodePosition,
    activeContainerId,
    // availableTools, // TODO: Wire up tool picker
    // availableAgents, // TODO: Wire up agent picker
    addResourceLink,
    loadAvailableTools,
    loadAvailableAgents,
    // containerRegistry, // TODO: Use for orphan lookups
    // userSessionId, // TODO: Use for workspace context
  } = useWorkspaceStore();

  // Resources available to be added (fetched from API)
  const [availableResources, setAvailableResources] = useState<any[]>([]);

  // Load tools/agents on mount (only in non-demo mode - demo uses static data)
  useEffect(() => {
    if (!isDemoMode()) {
      loadAvailableTools('all');
      loadAvailableAgents(null, '');
    }
  }, []);

  // Track Shift key for selection mode
  const [isShiftPressed, setIsShiftPressed] = useState(false);
  const [pickerState, setPickerState] = useState<{ type: 'agent' | 'tool', sessionId: string } | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Shift') setIsShiftPressed(true);
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === 'Shift') setIsShiftPressed(false);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);
  
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>(storeNodes as Node[]);
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    type: 'pane' | 'node' | 'edge';
    node?: Node;
    edge?: Edge;
  } | null>(null);
  const [sessionMenu, setSessionMenu] = useState<{ sessionId: string; x: number; y: number } | null>(null);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(storeEdges as Edge[]);
  
  // Track container transitions to prevent viewport flicker
  const [isTransitioning, setIsTransitioning] = useState(false);
  const prevContainerId = useRef<string | null>(null);

  // Sync local ReactFlow state with Zustand store
  useEffect(() => {
    // V4: If we have ResourceLinks, derive nodes from them
    // const v4Resources = activeContainerId ? containerResources : workspaceResources;
    
    // if (v4Resources && v4Resources.length > 0) {
    //   // V4 mode: Convert ResourceLinks to ReactFlow nodes
    //   const v4Nodes = v4Resources.map(link => resourceLinkToNode(link) as unknown as Node);
    //   console.log('🎨 GameCanvas: Setting V4 nodes:', v4Nodes);
    //   setNodes(v4Nodes);
    //   return;
    // }
    
    // Legacy/Demo mode: Use storeNodes directly with filtering
    let nodesToRender;
    
    // If inside a container (activeContainerId is set), show items belonging to that container
    if (activeContainerId) {
      // V5 Backend Mode: storeNodes is already scoped to the active container
      // Demo Mode: storeNodes is a flat list of all nodes, so we must filter
      const isDemo = isDemoMode();

      if (!isDemo) {
        nodesToRender = storeNodes;
      } else {
        // Show items that belong to this session (tools, agents, objects, child sessions)
        nodesToRender = storeNodes.filter((node: any) => {
          // Show items whose sessionId matches the active container
          if (node.data?.sessionId === activeContainerId) return true;
          // Also show child sessions whose parentSessionId matches
          if (node.type === 'session' && node.data?.parentSessionId === activeContainerId) return true;
          return false;
        });
      }
      console.log(`🔍 Inside ${activeContainerId}: showing ${nodesToRender.length} items`);
    } else if (!workspaceView) {
      // Non-workspace view (e.g., session-specific page) - show all
      nodesToRender = storeNodes;
    } else {
      // Workspace root view (L0): show parent-less sessions ONLY per UOM rules
      // UserSession can only contain SESSION + USER (ACL). No orphan agents/tools at L0.
      const sessions = storeNodes.filter((node: any) => node.type === 'session' && !node.data?.parentSessionId);
      
      // Calculate depth and object count for each session
      const sessionsWithMetadata = sessions.map((session: any) => {
        const sessionId = session.id;
        
        // Calculate max depth
        const calculateDepth = (sid: string, currentDepth: number = 0): number => {
          const children = storeNodes.filter((n: any) => 
            n.type === 'session' && n.data?.parentSessionId === sid
          );
          if (children.length === 0) return currentDepth;
          return Math.max(...children.map((child: any) => 
            calculateDepth(child.id, currentDepth + 1)
          ));
        };
        
        const depth = calculateDepth(sessionId, 0);
        
        // Count all objects in this session tree
        const countObjects = (sid: string): number => {
          // Count direct objects
          const directObjects = storeNodes.filter((n: any) => 
            n.type !== 'session' && n.data?.sessionId === sid
          ).length;
          
          // Count objects in child sessions recursively
          const childSessions = storeNodes.filter((n: any) => 
            n.type === 'session' && n.data?.parentSessionId === sid
          );
          
          const childObjectCount = childSessions.reduce((sum: number, child: any) => 
            sum + countObjects(child.id), 0
          );
          
          return directObjects + childObjectCount;
        };
        
        const objectCount = countObjects(sessionId);
        
        return {
          ...session,
          data: {
            ...session.data,
            depth,
            objectCount,
          }
        };
      });

      // At L0, only show sessions (UserSession contains SESSION + USER per UOM)
      nodesToRender = sessionsWithMetadata;
    }
    
    setNodes(nodesToRender as Node[]);
  }, [storeNodes, setNodes, workspaceView, activeContainerId]);

  useEffect(() => {
    setEdges(storeEdges as Edge[]);
  }, [storeEdges, setEdges]);

  // DO NOT sync back to store - causes loss of tool/agent nodes when workspace filters to sessions-only
  // The store is the source of truth, ReactFlow just displays filtered view

  // Clean up ReactFlow selection state when selection mode ends
  useEffect(() => {
    if (!isShiftPressed) {
      // Clear ReactFlow's selection overlay by setting selected=false on nodes
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          selected: false, // Clear all ReactFlow selection overlays
        }))
      );
      // Clear Zustand selection state
      setSelectedNodes([]);
    }
  }, [isShiftPressed, setNodes, setSelectedNodes]);

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => addEdge(connection, eds));
    },
    [setEdges]
  );

  const handleViewportChange = useCallback(
    (newViewport: any) => {
      if (activeContainerId) {
        setSessionViewport(activeContainerId, newViewport);
      } else {
        setViewport(newViewport);
      }
    },
    [activeContainerId, setViewport, setSessionViewport]
  );

  // Handle container transitions - hide canvas briefly during switch to prevent viewport flicker
  useEffect(() => {
    if (prevContainerId.current !== activeContainerId) {
      setIsTransitioning(true);
      prevContainerId.current = activeContainerId;
      
      // Small delay to allow nodes to update before restoring viewport
      const timer = setTimeout(() => {
        if (activeContainerId) {
          const saved = sessionViewports[activeContainerId];
          if (saved) {
            flowSetViewport(saved);
          } else {
            // No saved viewport for this session -> Fit View
            // We use fitView() instead of hardcoded 0,0,1 to ensure nodes are visible
            // We need to access the instance via useReactFlow() which we have as flowSetViewport's parent
            // But flowSetViewport is just a setter. We need the instance.
            // Actually, we can just set a flag or use a default that triggers fitView?
            // Better: use fitView() from useReactFlow
          }
        } else {
          // Workspace root
          // If viewport is default (0,0,1), try to fit view
          if (viewport.x === 0 && viewport.y === 0 && viewport.zoom === 1) {
             // We'll handle this in onInit or a separate effect that checks for nodes
          } else {
            flowSetViewport(viewport);
          }
        }
        setIsTransitioning(false);
      }, 50); // Brief delay for smooth transition
      
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeContainerId]);

  // Initial Fit View Logic
  useEffect(() => {
    // If we have nodes but viewport is default, fit view
    if (nodes.length > 0 && viewport.x === 0 && viewport.y === 0 && viewport.zoom === 1 && !activeContainerId) {
      console.log('🎨 Initial Fit View (Root)');
      fitView({ padding: 0.2 });
    }
  }, [nodes.length, activeContainerId, fitView, viewport.x, viewport.y, viewport.zoom]);

  // Session Fit View Logic
  useEffect(() => {
    if (activeContainerId && nodes.length > 0) {
                const saved = sessionViewports[activeContainerId];
      if (!saved) {
        console.log('🎨 Initial Fit View (Session)');
        fitView({ padding: 0.2 });
      }
    }
  }, [activeContainerId, nodes.length, fitView, sessionViewports]);

  const onPaneClick = useCallback(() => {
    // Close context menus when clicking canvas
    setContextMenu(null);
    setSessionMenu(null);
    // Clear selection when clicking on empty canvas
    if (!isShiftPressed) {
      setSelectedNodes([]);
    }
  }, [isShiftPressed, setSelectedNodes]);

  const onPaneContextMenu = useCallback((event: React.MouseEvent | MouseEvent) => {
    event.preventDefault();
    const clientX = 'clientX' in event ? event.clientX : 0;
    const clientY = 'clientY' in event ? event.clientY : 0;
    setContextMenu({
      x: clientX,
      y: clientY - 20, // Bump up slightly
      type: 'pane',
    });
  }, []);

  const onNodeContextMenu = useCallback((event: React.MouseEvent, node: Node) => {
    event.preventDefault();
    event.stopPropagation();

    // User nodes now get context menu with disabled "User (System-Defined)" item
    // Previously: if (node.type === 'user') return; // suppressed menu entirely

    if (node.type === 'session') {
      // Align "Edit" (2nd item) with cursor
      // "Open" item is ~32px height. Shift up by ~58px (50 + half 'E' height) to align Edit center with cursor
      setSessionMenu({ sessionId: node.id, x: event.clientX, y: event.clientY - 58 });
      return;
    }
    setContextMenu({
      x: event.clientX,
      y: event.clientY,
      type: 'node',
      node,
    });
  }, []);

  const onEdgeContextMenu = useCallback((event: React.MouseEvent, edge: Edge) => {
    event.preventDefault();
    setContextMenu({
      x: event.clientX,
      y: event.clientY,
      type: 'edge',
      edge,
    });
  }, []);

  const onNodeDragStart = useCallback(() => {
    // Close context menus when starting to drag a node
    setContextMenu(null);
    setSessionMenu(null);
  }, []);

  const onNodeDragStop = useCallback(
    (_: React.MouseEvent, node: Node) => {
      // Check if dragging a node that's part of a selection
      const selectedNodes = nodes.filter(n => n.selected);
      
      if (selectedNodes.length > 1 && selectedNodes.some(n => n.id === node.id)) {
        // Group drag - update all selected node positions
        console.log(`📍 Group drag: ${selectedNodes.length} nodes moved`);
        selectedNodes.forEach(n => {
          updateNodePosition(n.id, n.position);
        });
      } else {
        // Single node drag
        console.log(`📍 Node moved: ${node.data?.label || node.id} to (${Math.round(node.position.x)}, ${Math.round(node.position.y)})`);
        updateNodePosition(node.id, node.position);
      }
    },
    [nodes, updateNodePosition]
  );

  // ReactFlow's native selection end handler
  const onSelectionEnd = useCallback(() => {
    // Get selected session nodes from ReactFlow
    const selectedSessions = nodes.filter((n) => n.selected && n.type === 'session');

    if (selectedSessions.length > 0) {
      // Store selected session IDs in Zustand
      const sessionIds = selectedSessions.map((n) => n.id);
      setSelectedNodes(sessionIds);
      console.log(`✅ Marquee selected ${selectedSessions.length} sessions:`, sessionIds);
    }
  }, [nodes, setSelectedNodes]);

  // Handle selection changes (Ctrl+click, marquee, etc.)
  const onSelectionChange = useCallback(({ nodes: selectedNodes }: { nodes: Node[] }) => {
    const sessionIds = selectedNodes
      .filter(n => n.type === 'session')
      .map(n => n.id);
    setSelectedNodes(sessionIds);
  }, [setSelectedNodes]);

  return (
    <div className={`relative w-full h-full ${className}`} data-testid="react-flow">
      {/* Staging Queue Panel */}
      <StagingQueuePanel />
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onViewportChange={handleViewportChange}
        onPaneClick={onPaneClick}
        onPaneContextMenu={onPaneContextMenu}
        onNodeContextMenu={onNodeContextMenu}
        onEdgeContextMenu={onEdgeContextMenu}
        onNodeDragStart={onNodeDragStart}
        onNodeDragStop={onNodeDragStop}
        onSelectionEnd={onSelectionEnd}
        onSelectionChange={onSelectionChange}
        onNodeDoubleClick={onNodeDoubleClick}
        nodeTypes={nodeTypes}
        defaultViewport={viewport}
        snapToGrid
        snapGrid={[15, 15]}
        minZoom={0.125}
        maxZoom={2}
        className="bg-slate-950"
        style={{ opacity: isTransitioning ? 0 : 1, transition: 'opacity 0.05s ease-out' }}
        nodesDraggable={true}
        nodesConnectable={!isShiftPressed}
        elementsSelectable={true}
        selectionOnDrag={isShiftPressed}
        panOnDrag={!isShiftPressed}
        selectionMode={SelectionMode.Partial}
        multiSelectionKeyCode="Control"
        selectionKeyCode={null}
        deleteKeyCode={null}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={15} size={1} color="#334155" />
        <MiniMap
          className="bg-[rgba(15,23,42,0.50)] border border-slate-700"
          nodeColor={(node) => {
            const data = node.data as any;
            return data?.data?.themeColor || '#3b82f6';
          }}
        />

        <ContextMenu
          contextMenu={contextMenu}
          onClose={() => setContextMenu(null)}
          mode={activeContainerId ? 'session' : 'workspace'}
        />

        {sessionMenu && (
          <SessionContextMenu
            sessionId={sessionMenu.sessionId}
            position={{ x: sessionMenu.x, y: sessionMenu.y }}
            onClose={() => setSessionMenu(null)}
            onOpenPicker={async (type) => {
              console.log(`🎨 GameCanvas: onOpenPicker called for ${type}`);
              setPickerState({ type, sessionId: sessionMenu.sessionId });
              setSessionMenu(null);
              
              try {
                // Fetch all containers of this type
                const containers = await api.listContainers(type);
                
                // Map to format expected by picker
                const mapped = containers.map((c: api.Container) => ({
                   resource_id: c.instance_id,
                   resource_type: type,
                   title: (c as unknown as { title?: string }).title || c.instance_id,
                   description: (c as unknown as { description?: string }).description,
                   // Add other fields if needed
                   link_id: '', // Not linked yet
                   enabled: true,
                   preset_params: {},
                   input_mappings: {},
                   metadata: {}
                }));
                setAvailableResources(mapped);
              } catch (e) {
                console.error('Failed to fetch available resources:', e);
                setAvailableResources([]);
              }
            }}
          />
        )}

        {pickerState && (
          <ContainerPickerModal
            isOpen={true}
            containerType={pickerState.type}
            resources={availableResources as any[]}
            onSelect={async (r) => {
              try {
                const resource = r as any;
                await addResourceLink(pickerState.sessionId, {
                  resource_id: resource.resource_id,
                  resource_type: pickerState.type,
                  metadata: { title: resource.title || 'Resource' },
                  description: resource.description || '',
                  enabled: true,
                  preset_params: {},
                  input_mappings: {}
                });
              } catch (e) {
                console.error(e);
              }
              setPickerState(null);
            }}
            onClose={() => {
              console.log('🎨 GameCanvas: Closing picker');
              setPickerState(null);
            }}
          />
        )}
      </ReactFlow>
    </div>
  );
}

// Outer component with ReactFlowProvider
export default function GameCanvas(props: GameCanvasProps) {
  return (
    <ReactFlowProvider>
      <GameCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
