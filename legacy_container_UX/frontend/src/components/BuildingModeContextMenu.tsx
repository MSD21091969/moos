import { useCallback } from 'react';
import { useReactFlow } from '@xyflow/react';
import { Bot, Database, Plus, User, Wrench } from 'lucide-react';
import { generateAgentId, generateToolId, generateSourceId, generateId } from '../lib/id-generator';
import { useWorkspaceStore } from '../lib/workspace-store';
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
} from './ui/ContextMenu';

interface BuildingModeContextMenuProps {
  x: number;
  y: number;
  sessionId: string;
  onClose: () => void;
}

export function BuildingModeContextMenu({
  x,
  y,
  sessionId,
  onClose,
}: BuildingModeContextMenuProps) {
  const { addNode, createChildSession } = useWorkspaceStore();
  const { screenToFlowPosition } = useReactFlow();
  const containers = useWorkspaceStore(state => state.containers);

  // Calculate depth to enforce max nesting level
  const getDepth = (id: string): number => {
    let depth = 0;
    let current = containers.find(c => c.id === id);
    while (current?.parentSessionId) {
      depth++;
      current = containers.find(c => c.id === current!.parentSessionId);
    }
    return depth;
  };

  const currentDepth = getDepth(sessionId);
  const canCreateChild = currentDepth < 2; // Max depth: L0 (workspace), L1 (session), L2 (child session)

  // Helper to get flow position from screen coordinates
  const getFlowPosition = useCallback(() => {
    // Use screenToFlowPosition to convert client coordinates (x, y) to flow coordinates
    // This handles zoom, pan, and viewport offsets automatically
    return screenToFlowPosition({ x, y });
  }, [x, y, screenToFlowPosition]);

  const handleAddAgent = useCallback(() => {
    const pos = getFlowPosition();
    const agentId = generateAgentId();
    const newNode = {
      id: agentId,
      type: 'agent' as const,
      position: pos,
      data: {
        id: agentId,
        name: 'New Agent',
        role: 'Assistant',
        sessionId,
        status: 'idle' as const,
        capabilities: [],
      },
    };
    addNode(newNode);
    onClose();
  }, [getFlowPosition, sessionId, addNode, onClose]);

  const handleAddTool = useCallback(() => {
    const pos = getFlowPosition();
    const toolId = generateToolId();
    const newNode = {
      id: toolId,
      type: 'tool' as const,
      position: pos,
      data: {
        id: toolId,
        name: 'New Tool',
        category: 'Utility',
        sessionId,
        inputs: [],
        outputs: [],
      },
    };
    addNode(newNode);
    onClose();
  }, [getFlowPosition, sessionId, addNode, onClose]);

  const handleAddSource = useCallback(() => {
    const pos = getFlowPosition();
    const sourceId = generateSourceId();
    const newNode = {
      id: sourceId,
      type: 'object' as const,
      position: pos,
      data: {
        id: sourceId,
        type: 'api' as const,
        label: 'New Source',
        sessionId,
        fileType: 'API',
        size: 0,
      } as any,
    };
    addNode(newNode as any);
    onClose();
  }, [getFlowPosition, sessionId, addNode, onClose]);

  const handleAddACLMember = useCallback(() => {
    const pos = getFlowPosition();
    const aclId = generateId('acl');
    const newNode = {
      id: aclId,
      type: 'object' as const,
      position: pos,
      data: {
        id: aclId,
        type: 'user' as const,
        label: 'ACL Member',
        sessionId,
        fileType: 'USER',
        size: 0,
      } as any,
    };
    addNode(newNode as any);
    onClose();
  }, [getFlowPosition, sessionId, addNode, onClose]);

  const handleAddChildSession = useCallback(async () => {
    try {
      const pos = getFlowPosition();
      const parentContainer = containers.find(c => c.id === sessionId);
      const parentTitle = parentContainer?.title || 'Unknown Session';
      const title = 'New Session';
      const description = `Child of ${parentTitle} (ID: ${sessionId})`;
      await createChildSession(sessionId, title, pos, description);
      onClose();
    } catch (error) {
      console.error('Failed to create child session:', error);
    }
  }, [sessionId, containers, createChildSession, onClose, getFlowPosition]);

  return (
    <ContextMenu>
      <ContextMenuTrigger
        className="fixed w-0 h-0"
        style={{ left: x, top: y }}
        // Automatically open when mounted
        ref={(node) => {
          if (node) {
            node.dispatchEvent(new MouseEvent('contextmenu', {
              bubbles: true,
              cancelable: true,
              view: window,
              clientX: x,
              clientY: y
            }));
          }
        }}
      />
      
      <ContextMenuContent className="w-56" onCloseAutoFocus={(e) => {
        e.preventDefault();
        onClose();
      }}>
        <ContextMenuItem onClick={handleAddChildSession} disabled={!canCreateChild}>
          <Plus className="mr-2 h-4 w-4" />
          <span>Create Session</span>
        </ContextMenuItem>

        <ContextMenuSeparator />

        <ContextMenuItem onClick={handleAddAgent}>
          <Bot className="mr-2 h-4 w-4" />
          <span>Agent</span>
        </ContextMenuItem>

        <ContextMenuItem onClick={handleAddTool}>
          <Wrench className="mr-2 h-4 w-4" />
          <span>Tool</span>
        </ContextMenuItem>

        <ContextMenuItem onClick={handleAddSource}>
          <Database className="mr-2 h-4 w-4" />
          <span>Source</span>
        </ContextMenuItem>

        <ContextMenuItem onClick={handleAddACLMember}>
          <User className="mr-2 h-4 w-4" />
          <span>ACL Member</span>
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
}
