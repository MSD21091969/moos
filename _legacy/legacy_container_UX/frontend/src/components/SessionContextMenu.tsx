/**
 * Session Context Menu
 *
 * Right-click context menu for session nodes on canvas
 * Actions: Enter, Edit, Duplicate, Share, Delete
 *
 * Usage:
 *   <SessionContextMenu
 *     sessionId="sess_123"
 *     position={{x: 100, y: 100}}
 *     onClose={() => ...}
 *   />
 */

import { Copy, Edit, LogIn, Trash2, Plus, Bot, Wrench } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import * as api from '../lib/api';
import { useWorkspaceStore } from '../lib/workspace-store';
import { SessionQuickEditForm } from './SessionQuickEditForm';
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuTrigger,
} from './ui/ContextMenu';
// import { useEffect, useState } from 'react';

interface SessionContextMenuProps {
  sessionId: string;
  position: { x: number; y: number };
  onClose: () => void;
  onOpenPicker: (type: 'agent' | 'tool') => void;
}

export function SessionContextMenu({ sessionId, position, onClose, onOpenPicker }: SessionContextMenuProps) {
  const navigate = useNavigate();
  const { 
    nodes, 
    containers, 
    selectedNodeIds, 
    deleteContainer: storeDeleteSession,
    // createContainer
  } = useWorkspaceStore();
  
  const sessionNode = nodes.find((n) => n.id === sessionId);
  const currentSession = containers.find((s) => s.id === sessionId);

  // Load tools/agents on mount for submenus
  /*
  useEffect(() => {
    if (availableTools.length === 0) loadAvailableTools('all');
    if (availableAgents.length === 0) loadAvailableAgents(null, '');
  }, []);
  */

  // Check if this is part of a bulk selection
  // Filter selected IDs to only include sessions
  const selectedSessionIds = selectedNodeIds.filter((id) => {
    const node = nodes.find((n) => n.id === id);
    return node?.type === 'session';
  });

  // If the right-clicked session is part of the selection, treat as bulk action
  // Otherwise, treat as single action on the clicked node (ignoring other selection)
  const isClickedNodeSelected = selectedSessionIds.includes(sessionId);
  const isBulkSelection = isClickedNodeSelected && selectedSessionIds.length > 1;
  const bulkSessionIds = isBulkSelection ? selectedSessionIds : [sessionId];

  // If bulk selection, disable single-item actions
  const isSingleActionDisabled = isBulkSelection;

  const handleEnter = () => {
    if (isSingleActionDisabled) return;
    navigate(`/workspace/${sessionId}`);
    onClose();
  };

  /*
  const handleAddChildSession = async () => {
    if (isSingleActionDisabled) return;
    try {
      await createContainer('session', sessionId, { title: 'New Session', description: '' });
      onClose();
    } catch (error) {
      console.error('Failed to create child session:', error);
    }
  };
  */

  /*
  const handleAddTool = async (toolId: string) => {
    if (isSingleActionDisabled) return;
    try {
      // V5: Add resource link
      await addResourceLink(sessionId, {
        resource_id: toolId,
        resource_type: 'tool',
        metadata: { title: 'Tool' }, // Should fetch tool name
        description: ''
      });
      onClose();
    } catch (error) {
      console.error('Failed to add tool:', error);
    }
  };

  const handleAddAgent = async (agentId: string) => {
    if (isSingleActionDisabled) return;
    try {
      // V5: Add resource link
      await addResourceLink(sessionId, {
        resource_id: agentId,
        resource_type: 'agent',
        metadata: { title: 'Agent' }, // Should fetch agent name
        description: ''
      });
      onClose();
    } catch (error) {
      console.error('Failed to add agent:', error);
    }
  };
  */

  const handleDuplicate = async () => {
    if (isSingleActionDisabled) return;
    try {
      const nodeTitle = sessionNode?.data?.title;
      const originalTitle: string = 
        currentSession?.title || 
        (typeof nodeTitle === 'string' ? nodeTitle : 'Session');

      const store = useWorkspaceStore.getState();

      if (store.userSessionId || store.activeContainerId) {
        // V5: Create session as container with parent
        const parentId = store.activeContainerId || store.userSessionId || '';
        await api.createSession(parentId, {
          title: `${originalTitle} (Copy)`,
          description: currentSession?.description || '',
          tags: [],
          session_type: 'workspace',
          ttl_hours: 24,
        });

        // Reload parent to show new session
        if (store.activeContainerId) {
          await store.loadContainer(store.activeContainerId, 'session');
        } else if (store.userSessionId) {
          await store.loadContainer(store.userSessionId, 'usersession');
        }
      } else {
        // Legacy/Demo Fallback
        // Create duplicate session object in store
        const newId = `session-${Date.now()}`;
        const newSession: any = {
          id: newId,
          title: `${originalTitle} (Copy)`,
          description: currentSession?.description || '',
          status: 'active',
          type: 'session',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };

        // Use createContainer for V5 compatibility
        await store.createContainer('session', 'root', newSession);
      }

      onClose();
    } catch (error) {
      console.error('Failed to duplicate session:', error);
    }
  };

  /*
  const handleShare = async () => {
    if (isSingleActionDisabled) return;
    const emails = prompt('Enter email addresses (comma-separated):');
    if (!emails) return;

    const emailList = emails.split(',').map((e) => e.trim()).filter(Boolean);
    if (emailList.length === 0) return;

    try {
      // await shareSession(sessionId, emailList);
      console.warn('Share session not implemented in V4 yet');
      onClose();
    } catch (error) {
      console.error('Failed to share session:', error);
    }
  };
  */

  const handleDelete = async () => {
    const count = bulkSessionIds.length;
    const message =
      count > 1
        ? `Delete ${count} selected sessions?\n\nThis action cannot be undone.`
        : `Delete session "${
            sessionNode?.data?.title || 'Untitled'
          }"?\n\nThis action cannot be undone.`;

    const confirmed = confirm(message);
    if (!confirmed) return;

    try {
      for (const id of bulkSessionIds) {
        // Store action handles backend sync (V4 & Legacy)
        storeDeleteSession(id);
      }
      onClose();
    } catch (error) {
      console.error('Failed to delete session(s):', error);
    }
  };

  // We use a virtual trigger because ReactFlow handles the right-click event
  return (
    <ContextMenu>
      <ContextMenuTrigger
        className="fixed w-0 h-0"
        style={{ left: position.x, top: position.y }}
        // Automatically open when mounted
        ref={(node) => {
          if (node) {
            node.dispatchEvent(new MouseEvent('contextmenu', {
              bubbles: true,
              cancelable: true,
              view: window,
              clientX: position.x,
              clientY: position.y
            }));
          }
        }}
      />
      
      <ContextMenuContent className="w-64" onCloseAutoFocus={(e) => {
        e.preventDefault();
        onClose();
      }}>
        {/* Open = Dive Into Container */}
        <ContextMenuItem onClick={handleEnter} disabled={isSingleActionDisabled}>
          <LogIn className="mr-2 h-4 w-4" />
          <span>Open</span>
        </ContextMenuItem>

        {/* Edit = Quick Edit Properties */}
        <ContextMenuSub>
          <ContextMenuSubTrigger disabled={isSingleActionDisabled}>
            <Edit className="mr-2 h-4 w-4" />
            <span>Edit</span>
          </ContextMenuSubTrigger>
          <ContextMenuSubContent className="p-2">
            <SessionQuickEditForm sessionId={sessionId} onClose={onClose} />
          </ContextMenuSubContent>
        </ContextMenuSub>

        <ContextMenuSeparator />

        {/* Add Agent */}
        <ContextMenuSub>
          <ContextMenuSubTrigger disabled={isSingleActionDisabled} data-testid="context-add-agent">
            <Bot className="mr-2 h-4 w-4" />
            <span>Add Agent</span>
          </ContextMenuSubTrigger>
          <ContextMenuSubContent className="w-48">
            <ContextMenuItem onSelect={() => {
              console.log('🖱️ Clicked Add Existing Agent');
              onOpenPicker('agent');
            }}>
              <Plus className="mr-2 h-4 w-4" />
              <span>Add Existing...</span>
            </ContextMenuItem>
          </ContextMenuSubContent>
        </ContextMenuSub>

        {/* Add Tool */}
        <ContextMenuSub>
          <ContextMenuSubTrigger disabled={isSingleActionDisabled} data-testid="context-add-tool">
            <Wrench className="mr-2 h-4 w-4" />
            <span>Add Tool</span>
          </ContextMenuSubTrigger>
          <ContextMenuSubContent className="w-48">
            <ContextMenuItem onSelect={() => {
              console.log('🖱️ Clicked Add Existing Tool');
              onOpenPicker('tool');
            }}>
              <Plus className="mr-2 h-4 w-4" />
              <span>Add Existing...</span>
            </ContextMenuItem>
          </ContextMenuSubContent>
        </ContextMenuSub>

        <ContextMenuSeparator />

        {/* Duplicate */}
        <ContextMenuItem onClick={handleDuplicate} disabled={isSingleActionDisabled}>
          <Copy className="mr-2 h-4 w-4" />
          <span>Duplicate</span>
        </ContextMenuItem>

        <ContextMenuSeparator />

        {/* Delete */}
        <ContextMenuItem onClick={handleDelete} className="text-red-400 focus:text-red-400 focus:bg-red-900/20">
          <Trash2 className="mr-2 h-4 w-4" />
          <span>Delete {isBulkSelection ? `(${bulkSessionIds.length})` : ''}</span>
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
}
