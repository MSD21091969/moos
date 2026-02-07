import { useReactFlow } from '@xyflow/react';
import { useCallback, useEffect, useState, useMemo, useRef } from 'react';
import { CustomNode, CustomNodeData } from '../lib/types';
import { visualFeedback } from '../lib/visual-feedback';
import { useWorkspaceStore } from '../lib/workspace-store';
import { 
  DEMO_AGENT_DEFINITIONS, 
  DEMO_TOOL_DEFINITIONS, 
  DEMO_SOURCE_DEFINITIONS 
} from '../lib/demo-data';
import type { DefinitionResponse } from '../lib/api';
import {
  ContextMenu as ContextMenuRoot,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuTrigger,
} from './ui/ContextMenu';
import {
  Plus,
  Layers,
  SortAsc,
  Cpu,
  Grid,
  Circle,
  Square,
  Wrench,
  Bot,
  FileText,
  LayoutGrid,
  Copy,
  Trash2,
  LogIn,
  Edit,
  Database,
  FilePlus,
  FolderPlus,
  Users,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ContainerQuickEditForm, ContainerType } from './ContainerQuickEditForm';
import { toast } from '../lib/toast-store';
import { ContainerPickerModal } from './ContainerPickerModal';
// import * as api from '../lib/api'; // Unused until API integration

interface ContextMenuProps {
  contextMenu: {
    x: number;
    y: number;
    type: 'node' | 'pane' | 'edge';
    node?: any;
    edge?: any;
  } | null;
  onClose: () => void;
  mode?: 'session' | 'workspace';
}

// Mode detection helper - use centralized env helper
import { isDemoMode } from '../lib/env';

export function ContextMenu({ contextMenu, onClose, mode = 'session' }: ContextMenuProps) {
  const { screenToFlowPosition, fitView } = useReactFlow();
  const navigate = useNavigate();

  const { 
    addNode, 
    deleteNodes, 
    applyLayout, 
    nodes,
    createChildSession,
    addToolToSessionV4,
    addAgentToSessionV4,
    addSourceToSessionV4,
    activeContainerId,
    userSessionId,
    activeContainerType,
    breadcrumbs,
    availableAgents,
    availableTools,
    loadAvailableAgents,
    loadAvailableTools,
    containerRegistry,
    loadContainer: _loadContainer,
    loadWorkspaceResources: _loadWorkspaceResources,
    loadOrphans,
  } = useWorkspaceStore();

  // Computed V4 compatibility values
  const activeSessionId = activeContainerId;

  // Load definitions on mount (for "Create New" submenus)
  const [definitionsLoaded, setDefinitionsLoaded] = useState(false);
  const loadAttempted = useRef(false);
  
  useEffect(() => {
    if (!loadAttempted.current && !definitionsLoaded && !isDemoMode()) {
      loadAttempted.current = true;
      // In backend mode, load definitions from API
      Promise.all([
        loadAvailableAgents(null, ''),
        loadAvailableTools('all'),
        // loadSourceDefinitions(), // Not implemented yet
      ]).then(() => setDefinitionsLoaded(true))
        .catch(err => console.error('Failed to load definitions:', err));
    }
  }, [definitionsLoaded, loadAvailableAgents, loadAvailableTools]);

  // Normalize definitions to common shape
  type NormalizedDef = { id: string; title: string; description?: string };
  const normalizeAgentDef = (def: any): NormalizedDef => ({
    id: def.definition_id || def.agent_id || def.id,
    title: def.title || def.name || 'Unnamed',
    description: def.description,
  });
  const normalizeToolDef = (def: any): NormalizedDef => ({
    id: def.definition_id || def.name || def.id,
    title: def.title || def.name || 'Unnamed',
    description: def.description,
  });

  // Get effective definitions (demo or from API)
  const effectiveAgentDefs = isDemoMode() ? DEMO_AGENT_DEFINITIONS : availableAgents;
  const effectiveToolDefs = isDemoMode() ? DEMO_TOOL_DEFINITIONS : availableTools;
  const effectiveSourceDefs = isDemoMode() ? DEMO_SOURCE_DEFINITIONS : []; // sourceDefinitions not in store yet

  // Tier + depth helpers
  const userTier = useMemo(() => {
    const raw = (localStorage.getItem('user_tier') || localStorage.getItem('tier') || import.meta.env.VITE_USER_TIER || import.meta.env.VITE_TIER || 'ENTERPRISE').toString().toUpperCase();
    if (raw.includes('FREE')) return 'FREE';
    if (raw.includes('PRO')) return 'PRO';
    if (raw.includes('ENTER')) return 'ENTERPRISE';
    return raw;
  }, []);

  const maxDepthForTier = useMemo(() => (userTier === 'FREE' ? 2 : 4), [userTier]);
  const navDepth = useMemo(() => Math.max(0, (breadcrumbs?.length || 1) - 1), [breadcrumbs]);
  const depthLimitReached = navDepth >= maxDepthForTier;

  // Compute orphans (Library) from containerRegistry - containers with parent_id=null
  const orphanContainers = useMemo(() => {
    return Object.values(containerRegistry)
      .filter(entry => entry.container?.parent_id === null)
      .map(entry => entry.container)
      .filter(Boolean);
  }, [containerRegistry]);

  // Filter orphans by type for menu display
  const getOrphansByType = useCallback((type: 'agent' | 'tool' | 'source') => {
    return orphanContainers.filter(c => 
      c?.instance_id?.startsWith(type) || 
      (c as any)?.definition_id?.includes(type)
    );
  }, [orphanContainers]);

  const canAdd = useCallback((options?: { isTerminal?: boolean }) => {
    const isTerminal = options?.isTerminal ?? false;

    if (activeContainerType === 'source') {
      toast.warning('Source containers are terminal. Only Users may be added here.');
      return false;
    }

    if (!isTerminal && depthLimitReached) {
      toast.warning(`Depth limit reached for ${userTier}. Terminals only at L${maxDepthForTier}.`);
      return false;
    }

    return true;
  }, [activeContainerType, depthLimitReached, userTier, maxDepthForTier]);

  const isSourceContainer = activeContainerType === 'source';
  const disableNonTerminalAdds = isSourceContainer || depthLimitReached;
  const disableSourceAdd = isSourceContainer;
  const disableDocumentAdd = isSourceContainer;

  const [pickerType, setPickerType] = useState<'agent' | 'tool' | 'source' | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);

  const handleCreateSession = useCallback(async () => {
    if (!contextMenu) return;

    if (!canAdd({ isTerminal: false })) return;

    const flowPosition = screenToFlowPosition({
      x: contextMenu.x,
      y: contextMenu.y,
    });

    try {
      // Use agent interface for consistent behavior
      const parentId = activeSessionId || userSessionId;
      if (parentId) {
        await createChildSession(
            parentId,
            'New Session',
            flowPosition,
            ''
        );
      }
      
      onClose();
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  }, [contextMenu, screenToFlowPosition, onClose, activeSessionId, userSessionId, createChildSession, canAdd]);

  // Helper to get current session ID from URL or store
  const getCurrentSessionId = useCallback((): string | undefined => {
    // Try URL patterns: /workspace/{id} or /session/{id}
    const workspaceMatch = window.location.pathname.match(/\/workspace\/([^/]+)/);
    if (workspaceMatch) return workspaceMatch[1];
    
    const sessionMatch = window.location.pathname.match(/\/session\/([^/]+)/);
    if (sessionMatch) return sessionMatch[1];
    
    // Fall back to store's activeSessionId, then userSessionId (root)
    return activeSessionId || userSessionId || undefined;
  }, [activeSessionId, userSessionId]);

  // Generic handler for creating a new tool from a definition
  const handleCreateToolFromDefinition = useCallback(async (definition: DefinitionResponse) => {
    if (!contextMenu) return;

    const flowPosition = screenToFlowPosition({
      x: contextMenu.x,
      y: contextMenu.y,
    });

    const sessionId = getCurrentSessionId();

    if (!sessionId) {
      console.warn('No session ID found - cannot add tool outside session context');
      onClose();
      return;
    }

    if (!canAdd({ isTerminal: false })) {
      onClose();
      return;
    }

    try {
      await addToolToSessionV4(
        sessionId,
        definition.definition_id,
        {
          description: definition.title,
          metadata: { x: flowPosition.x, y: flowPosition.y }
        }
      );

      setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 50);
      onClose();
    } catch (error) {
      console.error('Failed to add tool:', error);
    }
  }, [contextMenu, onClose, screenToFlowPosition, fitView, addToolToSessionV4, getCurrentSessionId, canAdd]);

  // Generic handler for creating a new source from a definition
  const handleCreateSourceFromDefinition = useCallback(async (definition: DefinitionResponse) => {
    if (!contextMenu) return;

    const flowPosition = screenToFlowPosition({
      x: contextMenu.x,
      y: contextMenu.y,
    });

    const sessionId = getCurrentSessionId();

    if (!sessionId) {
      console.warn('No session ID found - cannot add source outside session context');
      onClose();
      return;
    }

    if (!canAdd({ isTerminal: true })) {
      onClose();
      return;
    }

    try {
      await addSourceToSessionV4(
        sessionId,
        definition.definition_id,
        {
          description: definition.title,
          metadata: { x: flowPosition.x, y: flowPosition.y }
        }
      );

      setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 50);
      onClose();
    } catch (error) {
      console.error('Failed to add source:', error);
    }
  }, [contextMenu, onClose, screenToFlowPosition, fitView, addSourceToSessionV4, getCurrentSessionId, canAdd]);

  // Generic handler for creating a new agent from a definition
  const handleCreateAgentFromDefinition = useCallback(async (definition: DefinitionResponse) => {
    if (!contextMenu) return;

    const flowPosition = screenToFlowPosition({
      x: contextMenu.x,
      y: contextMenu.y,
    });

    const sessionId = getCurrentSessionId();

    if (!sessionId) {
      console.warn('No session ID found - cannot add agent outside session context');
      onClose();
      return;
    }

    try {
      await addAgentToSessionV4(
        sessionId,
        definition.definition_id,
        {
          description: definition.title,
          metadata: { x: flowPosition.x, y: flowPosition.y }
        }
      );

      setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 50);
      onClose();
    } catch (error) {
      console.error('Failed to add agent:', error);
    }
  }, [contextMenu, onClose, screenToFlowPosition, fitView, addAgentToSessionV4, getCurrentSessionId]);

  // Placeholder for adding existing container (TODO: implement container picker)
  const handleAddExistingContainer = useCallback(async (containerType: 'agent' | 'tool' | 'source') => {
    // Load orphans into registry before opening picker
    await loadOrphans(containerType);
    setPickerType(containerType);
    setPickerOpen(true);
  }, [loadOrphans]);

  const handleSelectExisting = useCallback(
    async (resource: any) => {
      if (!contextMenu) return;

      const flowPosition = screenToFlowPosition({ x: contextMenu.x, y: contextMenu.y });
      const parentId = getCurrentSessionId();

      if (!parentId) {
        toast.warning('Open a container to add an existing item.');
        setPickerOpen(false);
        return;
      }

      // Determine type from instance_id prefix
      const instanceId = resource.instance_id || resource.id;
      const resourceType = instanceId?.split('_')[0] || 'agent';
      const isTerminal = resourceType === 'source';
      
      if (!canAdd({ isTerminal })) {
        setPickerOpen(false);
        return;
      }

      const mode = import.meta.env.VITE_MODE;

      try {
        if (mode === 'demo') {
          const newId = `${resourceType}-${instanceId}-${Date.now()}`;
          addNode({
            id: newId,
            type: resourceType as any,
            position: flowPosition,
            data: {
              id: newId,
              type: resourceType,
              label: resource.title || resource.definition_id || instanceId,
              sessionId: parentId,
              definition_id: resource.definition_id,
            },
          } as CustomNode);

          visualFeedback.highlightNodes([newId], '#3b82f6', 1200, 'Adopted');
          toast.info('Adopted container from Library (demo).');
        } else {
          // V5 API: Adopt orphan via addResourceLink with instance_id
          const { addResourceLink } = useWorkspaceStore.getState();
          await addResourceLink(parentId, {
            resource_type: resourceType,
            resource_id: resource.definition_id || instanceId,
            instance_id: instanceId,  // KEY: This triggers adoption
            description: resource.title || resource.description,
            metadata: {
              x: flowPosition.x,
              y: flowPosition.y,
            },
          });

          toast.success('Adopted container from Library');
        }
      } catch (error: any) {
        console.error('Failed to adopt container:', error);
        // Handle "not orphan" error gracefully
        if (error.message?.includes('already has parent')) {
          toast.error('Container is not available (still linked elsewhere)');
        } else {
          toast.error('Failed to adopt container');
        }
      } finally {
        setPickerOpen(false);
        onClose();
      }
    },
    [addNode, canAdd, contextMenu, getCurrentSessionId, onClose, screenToFlowPosition]
  );

  const handleAddDocument = useCallback(() => {
    if (!contextMenu) return;

    const flowPosition = screenToFlowPosition({
      x: contextMenu.x,
      y: contextMenu.y,
    });

    const newNode = {
      id: `doc-${Date.now()}`,
      type: 'object',
      position: flowPosition,
      data: {
        id: `doc-${Date.now()}`,
        type: 'document' as const,
        label: 'New Document',
        sessionId: undefined,
      },
    };

    addNode(newNode);
    visualFeedback.highlightNodes([newNode.id], '#f59e0b', 2000, 'Created');

    setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 50);

    onClose();
  }, [contextMenu, addNode, onClose, screenToFlowPosition, fitView, canAdd]);

  const handleDuplicateNode = useCallback(() => {
    if (!contextMenu?.node) return;

    const originalNode = contextMenu.node;
    const newNode: CustomNode = {
      ...originalNode,
      id: `${originalNode.type}-${Date.now()}`,
      type: originalNode.type!,
      position: {
        x: originalNode.position.x + 50,
        y: originalNode.position.y + 50,
      },
      data: originalNode.data as CustomNodeData & Record<string, unknown>,
    };

    addNode(newNode);
    visualFeedback.highlightNodes([newNode.id], '#3b82f6', 2000, 'Duplicated');
    onClose();
  }, [contextMenu, addNode, onClose]);

  const handleDeleteNode = useCallback(() => {
    if (!contextMenu?.node) return;

    deleteNodes([contextMenu.node.id]);
    visualFeedback.highlightNodes([contextMenu.node.id], '#ef4444', 1000, 'Deleted');
    onClose();
  }, [contextMenu, deleteNodes, onClose]);

  const handleCircularLayout = useCallback(() => {
    // Simplified - just apply grid layout to all visible nodes
    applyLayout('grid');
    onClose();
  }, [applyLayout, onClose]);

  // Handler to open/dive into a container (session, agent, tool, source)
  const handleOpenContainer = useCallback(() => {
    if (!contextMenu?.node) return;
    const nodeId = contextMenu.node.id;
    // All containers navigate the same way
    navigate(`/workspace/${nodeId}`);
    onClose();
  }, [contextMenu, navigate, onClose]);

  // Check if node is a container (can be opened/dived into)
  // Containers: session, agent, tool (NOT source - it's terminal)
  const isContainerNode = contextMenu?.node?.type === 'session' || 
                          contextMenu?.node?.type === 'agent' || 
                          contextMenu?.node?.type === 'tool';

  // Terminal nodes: source and user cannot be navigated into
  // Source: terminal data endpoint, User: system-defined ACL reference
  const isTerminalNode = contextMenu?.node?.type === 'source' || 
                         contextMenu?.node?.type === 'user';

  if (!contextMenu) return null;

  const isNode = contextMenu.type === 'node';
  const isPane = contextMenu.type === 'pane';

  return (
    <ContextMenuRoot>
      <ContextMenuTrigger
        className="fixed w-0 h-0"
        style={{ left: contextMenu.x, top: contextMenu.y }}
        ref={(node) => {
          if (node) {
            node.dispatchEvent(new MouseEvent('contextmenu', {
              bubbles: true,
              cancelable: true,
              view: window,
              clientX: contextMenu.x,
              clientY: contextMenu.y
            }));
          }
        }}
      />

      <ContextMenuContent className="w-64" onCloseAutoFocus={(e) => {
        e.preventDefault();
        onClose();
      }}>
        {/* Pane Context Menu */}
        {isPane && (
          <>
            <ContextMenuItem onClick={handleCreateSession} data-testid="create-session-btn" disabled={disableNonTerminalAdds}>
              <Plus className="mr-2 h-4 w-4" />
              <span>Create Session</span>
            </ContextMenuItem>

            <ContextMenuSeparator />

            <ContextMenuSub>
              <ContextMenuSubTrigger>
                <Layers className="mr-2 h-4 w-4" />
                <span>Grouping</span>
              </ContextMenuSubTrigger>
              <ContextMenuSubContent className="w-48">
                <ContextMenuItem onClick={() => console.log('Group by Color')}>
                  <span>Color</span>
                </ContextMenuItem>
                <ContextMenuItem onClick={() => console.log('Group by A-Z')}>
                  <SortAsc className="mr-2 h-4 w-4" />
                  <span>A-Z</span>
                </ContextMenuItem>
                <ContextMenuItem onClick={() => console.log('Group by Algorithm')}>
                  <Cpu className="mr-2 h-4 w-4" />
                  <span>Collider Algorithm</span>
                </ContextMenuItem>
                <ContextMenuItem onClick={() => console.log('Group Custom')}>
                  <Grid className="mr-2 h-4 w-4" />
                  <span>Custom</span>
                </ContextMenuItem>
                <ContextMenuSeparator />
                <ContextMenuItem onClick={() => console.log('Circle layout')}>
                  <Circle className="mr-2 h-4 w-4" />
                  <span>Circle</span>
                </ContextMenuItem>
                <ContextMenuItem onClick={() => console.log('Square layout')}>
                  <Square className="mr-2 h-4 w-4" />
                  <span>Square</span>
                </ContextMenuItem>
              </ContextMenuSubContent>
            </ContextMenuSub>

            {(mode === 'session' || mode === 'workspace') && (
              <>
                <ContextMenuSeparator />
                {isSourceContainer ? (
                  <>
                    <ContextMenuItem disabled>
                      <Database className="mr-2 h-4 w-4" />
                      <span>Source is terminal (only Users allowed)</span>
                    </ContextMenuItem>
                    <ContextMenuItem disabled>
                      <Users className="mr-2 h-4 w-4" />
                      <span>Add User (coming soon)</span>
                    </ContextMenuItem>
                  </>                ) : !activeContainerId ? (
                  <>
                    {/* L0 (Workspace Root): Only SESSION creation allowed per UOM */}
                    <ContextMenuItem disabled>
                      <Bot className="mr-2 h-4 w-4" />
                      <span>Agents can only be added inside sessions</span>
                    </ContextMenuItem>
                    <ContextMenuItem disabled>
                      <Wrench className="mr-2 h-4 w-4" />
                      <span>Tools can only be added inside sessions</span>
                    </ContextMenuItem>
                    <ContextMenuItem disabled>
                      <Database className="mr-2 h-4 w-4" />
                      <span>Sources can only be added inside containers</span>
                    </ContextMenuItem>
                  </>                ) : activeContainerId === null ? (
                  <>
                    {/* L0 (Workspace Root): Only SESSION creation allowed */}
                    <ContextMenuItem disabled>
                      <Bot className="mr-2 h-4 w-4" />
                      <span>Agents can only be added inside sessions</span>
                    </ContextMenuItem>
                    <ContextMenuItem disabled>
                      <Wrench className="mr-2 h-4 w-4" />
                      <span>Tools can only be added inside sessions</span>
                    </ContextMenuItem>
                    <ContextMenuItem disabled>
                      <Database className="mr-2 h-4 w-4" />
                      <span>Sources can only be added inside containers</span>
                    </ContextMenuItem>
                  </>
                ) : (
                  <>
                    {/* Agent Submenu - Create New or Add Existing */}
                    <ContextMenuSub>
                      <ContextMenuSubTrigger data-testid="context-add-agent" disabled={disableNonTerminalAdds}>
                        <Bot className="mr-2 h-4 w-4" />
                        <span>Add Agent</span>
                      </ContextMenuSubTrigger>
                      <ContextMenuSubContent className="w-56">
                        {/* Create New from Definition */}
                        <ContextMenuSub>
                          <ContextMenuSubTrigger>
                            <FilePlus className="mr-2 h-4 w-4" />
                            <span>Create New...</span>
                          </ContextMenuSubTrigger>
                          <ContextMenuSubContent className="w-56">
                            {effectiveAgentDefs.map((def) => {
                              const normalized = normalizeAgentDef(def);
                              return (
                              <ContextMenuItem 
                                key={normalized.id}
                                onClick={() => handleCreateAgentFromDefinition(def as any)}
                              >
                                <div className="flex flex-col">
                                  <span>{normalized.title}</span>
                                  {normalized.description && (
                                    <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                                      {normalized.description}
                                    </span>
                                  )}
                                </div>
                              </ContextMenuItem>
                            );
                            })}
                            {effectiveAgentDefs.length === 0 && (
                              <ContextMenuItem disabled>
                                <span className="text-muted-foreground">No agent definitions</span>
                              </ContextMenuItem>
                            )}
                          </ContextMenuSubContent>
                        </ContextMenuSub>
                        
                        {/* Add Existing Owned/Shared */}
                        <ContextMenuItem onClick={() => handleAddExistingContainer('agent')} disabled={disableNonTerminalAdds}>
                          <FolderPlus className="mr-2 h-4 w-4" />
                          <span>Add Existing...</span>
                        </ContextMenuItem>
                      </ContextMenuSubContent>
                    </ContextMenuSub>

                    {/* Tool Submenu - Create New or Add Existing */}
                    <ContextMenuSub>
                      <ContextMenuSubTrigger data-testid="context-add-tool" disabled={disableNonTerminalAdds}>
                        <Wrench className="mr-2 h-4 w-4" />
                        <span>Add Tool</span>
                      </ContextMenuSubTrigger>
                      <ContextMenuSubContent className="w-56">
                        {/* Create New from Definition */}
                        <ContextMenuSub>
                          <ContextMenuSubTrigger>
                            <FilePlus className="mr-2 h-4 w-4" />
                            <span>Create New...</span>
                          </ContextMenuSubTrigger>
                          <ContextMenuSubContent className="w-56">
                            {effectiveToolDefs.map((def) => {
                              const normalized = normalizeToolDef(def);
                              return (
                              <ContextMenuItem 
                                key={normalized.id}
                                onClick={() => handleCreateToolFromDefinition(def as any)}
                              >
                                <div className="flex flex-col">
                                  <span>{normalized.title}</span>
                                  {normalized.description && (
                                    <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                                      {normalized.description}
                                    </span>
                                  )}
                                </div>
                              </ContextMenuItem>
                            );
                            })}
                            {effectiveToolDefs.length === 0 && (
                              <ContextMenuItem disabled>
                                <span className="text-muted-foreground">No tool definitions</span>
                              </ContextMenuItem>
                            )}
                          </ContextMenuSubContent>
                        </ContextMenuSub>
                        
                        {/* Add Existing Owned/Shared */}
                        <ContextMenuItem onClick={() => handleAddExistingContainer('tool')} disabled={disableNonTerminalAdds}>
                          <FolderPlus className="mr-2 h-4 w-4" />
                          <span>Add Existing...</span>
                        </ContextMenuItem>
                      </ContextMenuSubContent>
                    </ContextMenuSub>

                    {/* Source Submenu - Create New or Add Existing */}
                    <ContextMenuSub>
                      <ContextMenuSubTrigger data-testid="context-add-source" disabled={disableSourceAdd}>
                        <Database className="mr-2 h-4 w-4" />
                        <span>Add Source</span>
                      </ContextMenuSubTrigger>
                      <ContextMenuSubContent className="w-56">
                        {/* Create New from Definition */}
                        <ContextMenuSub>
                          <ContextMenuSubTrigger>
                            <FilePlus className="mr-2 h-4 w-4" />
                            <span>Create New...</span>
                          </ContextMenuSubTrigger>
                          <ContextMenuSubContent className="w-56">
                            {effectiveSourceDefs.map((def) => (
                              <ContextMenuItem 
                                key={def.definition_id}
                                onClick={() => handleCreateSourceFromDefinition(def)}
                              >
                                <div className="flex flex-col">
                                  <span>{def.title}</span>
                                  {def.description && (
                                    <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                                      {def.description}
                                    </span>
                                  )}
                                </div>
                              </ContextMenuItem>
                            ))}
                            {effectiveSourceDefs.length === 0 && (
                              <ContextMenuItem disabled>
                                <span className="text-muted-foreground">No source definitions</span>
                              </ContextMenuItem>
                            )}
                          </ContextMenuSubContent>
                        </ContextMenuSub>
                        
                        {/* Add Existing Owned/Shared */}
                        <ContextMenuItem onClick={() => handleAddExistingContainer('source')} disabled={disableSourceAdd}>
                          <FolderPlus className="mr-2 h-4 w-4" />
                          <span>Add Existing...</span>
                        </ContextMenuItem>
                      </ContextMenuSubContent>
                    </ContextMenuSub>

                    <ContextMenuSeparator />

                    <ContextMenuItem onClick={handleAddDocument} data-ai-action="context-add-document" disabled={disableDocumentAdd}>
                      <FileText className="mr-2 h-4 w-4" />
                      <span>Add Document</span>
                    </ContextMenuItem>
                  </>
                )}
              </>
            )}

            {nodes.length > 0 && (
              <>
                <ContextMenuSeparator />
                <ContextMenuItem onClick={handleCircularLayout} data-ai-action="context-circular-layout">
                  <LayoutGrid className="mr-2 h-4 w-4" />
                  <span>Circular Layout</span>
                </ContextMenuItem>
              </>
            )}
          </>
        )}

        {/* Node Context Menu */}
        {isNode && contextMenu.node && (
          <>
            {/* Container menu (session, agent, tool) - can be opened/navigated */}
            {isContainerNode && (
              <>
                <ContextMenuItem onClick={handleOpenContainer} data-ai-action="context-open-container">
                  <LogIn className="mr-2 h-4 w-4" />
                  <span>Open</span>
                </ContextMenuItem>

                <ContextMenuSub>
                  <ContextMenuSubTrigger>
                    <Edit className="mr-2 h-4 w-4" />
                    <span>Edit</span>
                  </ContextMenuSubTrigger>
                  <ContextMenuSubContent className="p-2 min-w-[280px]">
                    <ContainerQuickEditForm
                      nodeId={contextMenu.node.id}
                      containerType={contextMenu.node.type as ContainerType}
                      onClose={onClose}
                    />
                  </ContextMenuSubContent>
                </ContextMenuSub>

                <ContextMenuSeparator />
              </>
            )}

            {/* Terminal node menu (source, user) - cannot be navigated into */}
            {isTerminalNode && (
              <>
                {/* Source nodes: Edit allowed (modify config), Delete allowed */}
                {contextMenu.node.type === 'source' && (
                  <ContextMenuSub>
                    <ContextMenuSubTrigger>
                      <Edit className="mr-2 h-4 w-4" />
                      <span>Edit Source</span>
                    </ContextMenuSubTrigger>
                    <ContextMenuSubContent className="p-2 min-w-[280px]">
                      <ContainerQuickEditForm
                        nodeId={contextMenu.node.id}
                        containerType="source"
                        onClose={onClose}
                      />
                    </ContextMenuSubContent>
                  </ContextMenuSub>
                )}
                {/* User nodes: View only (system-defined), no edit - ACL changes via parent resource_link */}
                {contextMenu.node.type === 'user' && (
                  <ContextMenuItem disabled data-ai-action="context-view-user">
                    <Edit className="mr-2 h-4 w-4 opacity-50" />
                    <span className="opacity-50">User (System-Defined)</span>
                  </ContextMenuItem>
                )}
                <ContextMenuSeparator />
              </>
            )}

            {/* Duplicate - available for non-terminal nodes only */}
            {!isTerminalNode && (
              <>
                <ContextMenuItem onClick={handleDuplicateNode} data-ai-action="context-duplicate-node">
                  <Copy className="mr-2 h-4 w-4" />
                  <span>Duplicate</span>
                </ContextMenuItem>
                <ContextMenuSeparator />
              </>
            )}

            {/* Delete - available for containers and source, NOT for user nodes */}
            {contextMenu.node.type !== 'user' && (
              <ContextMenuItem 
                onClick={handleDeleteNode} 
                data-ai-action="context-delete-node"
                className="text-red-400 focus:text-red-400 focus:bg-red-900/20"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                <span>Delete</span>
              </ContextMenuItem>
            )}
          </>
        )}
      </ContextMenuContent>

      <ContainerPickerModal
        isOpen={pickerOpen}
        containerType={pickerType || 'agent'}
        resources={pickerType ? getOrphansByType(pickerType) as any : []}
        onSelect={handleSelectExisting}
        onClose={() => setPickerOpen(false)}
      />
    </ContextMenuRoot>
  );
}
