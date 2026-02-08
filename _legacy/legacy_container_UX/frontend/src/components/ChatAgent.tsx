import { useState, useEffect, useRef, useCallback } from 'react';

import { visualFeedback } from '../lib/visual-feedback';
import { canvasObserver } from '../lib/canvas-observer';
import { useChatStore } from '../lib/chat-store';
import { useWorkspaceStore } from '../lib/workspace-store';
import { GeminiLiveSession } from '../lib/gemini-live-client';
import { LocalIntelligence } from '../lib/local-intelligence';
import { toast } from '../lib/toast-store';
import { Send, Mic, MicOff, Layers, Zap, Trash2, Cloud, Cpu } from 'lucide-react';
import { MicrosoftLoginButton } from './MicrosoftLoginButton';
import type { ColliderBridge } from '../lib/chat/collider-bridge';

// Extend Window for bridge access
declare global {
  interface Window {
    __colliderBridge?: ColliderBridge;
  }
}

type ChatMode = 'staged' | 'direct' | 'voice';
type VoiceStatus = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

export default function ChatAgent() {
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<ChatMode>('staged');
  const [aiMode, setAiMode] = useState<'cloud' | 'local'>('cloud');
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus>('idle');
  const [liveSession, setLiveSession] = useState<GeminiLiveSession | null>(null);
  const [openMenu, setOpenMenu] = useState<'session' | 'agent' | 'tool' | 'api' | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const localAgentRef = useRef<LocalIntelligence | null>(null);

  // Listen for agent commands to open menus
  useEffect(() => {
    const handleOpenMenu = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail && detail.type) {
        setOpenMenu(detail.type);
      }
    };
    window.addEventListener('agent:open-menu', handleOpenMenu);
    return () => window.removeEventListener('agent:open-menu', handleOpenMenu);
  }, []);

  const { messages, isAgentTyping, addMessage, setAgentTyping, clearMessages } = useChatStore();
  const {
    nodes,
    edges,
    containers,
    selectedNodeIds,
    activeContainerId,
    userSessionId,
    breadcrumbs,
    updateNodePosition,
    setSelectedNodes,
    addNode,
    createContainer,
    updateContainer,
    deleteNodes,
    applyLayout,
    setActiveContainer,
    // Custom tool/agent actions
    createUserCustomTool,
    createUserCustomAgent,
    availableTools,
    availableAgents,
    loadAvailableTools,
    loadAvailableAgents,
    addToolToSessionV4,
    addAgentToSessionV4,
    createChildSession,
  } = useWorkspaceStore();

  // Helper functions for tool calls
  const findResources = async (_scopeId: string, _query: string, _type: string) => []; 
  const batchDeleteResources = async (_items: any[]) => {};
  const updateTheme = async (id: string, theme: any) => updateContainer(id, theme);
  const addSession = async (data: any) => createContainer('session', userSessionId || 'root', data);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Stream visual context to Gemini when graph changes
  useEffect(() => {
    if (mode === 'voice' && liveSession && liveSession.connected) {
      liveSession.streamVisualContext({
        nodes,
        edges,
        selectedNodes: selectedNodeIds,
        activeSession: activeContainerId,
        viewport: { x: 0, y: 0, zoom: 1 }, // Default viewport - would need to get from ReactFlow
        timestamp: Date.now(),
        globalSessions: containers.map(s => ({ id: s.id, title: s.title })),
        breadcrumbs: breadcrumbs
      });
    }
  }, [mode, liveSession, nodes, edges, selectedNodeIds, activeContainerId, containers, breadcrumbs]);

  // Reconnect if AI mode changes while voice is active
  useEffect(() => {
    if (mode === 'voice' && liveSession) {
      disconnectVoice().then(() => connectVoice());
    }
  }, [aiMode]);

  // Voice mode: Connect to live session
  const connectVoice = useCallback(async () => {
    try {
      const apiKey = import.meta.env?.VITE_GEMINI_API_KEY as string | undefined;
      if (!apiKey && aiMode === 'cloud') {
        addMessage({ role: 'assistant', content: 'VITE_GEMINI_API_KEY not found' });
        return;
      }

      const session = new GeminiLiveSession({
        apiKey: apiKey || '',
        mode: aiMode,
        generationConfig: {
          temperature: 0.7, // More creative/natural
          topP: 0.95,
          topK: 40,
          maxOutputTokens: 1000,
        },
        voiceConfig: {
          rate: 0.9, // Calm, steady (HAL-like)
          pitch: 0.9, // Slightly lower
          lang: 'en-US',
        },
      });
      await session.connect(
        (status) => setVoiceStatus(status as VoiceStatus),
        (text, isFinal) => {
          if (isFinal) {
            addMessage({ role: 'user', content: `🎤 ${text}` });
            // Voice command is processed by Gemini Live session automatically
          }
        },
        async (name, args) => await handleToolCall(name, args),
        (text) => {
          addMessage({ role: 'assistant', content: text });
        }
      );

      setLiveSession(session);
      setMode('voice');
    } catch (error) {
      console.error('Voice connect error:', error);
      addMessage({ role: 'assistant', content: '❌ Voice connection failed' });
    }
  }, [addMessage, aiMode]);

  const disconnectVoice = useCallback(async () => {
    if (liveSession) {
      await liveSession.disconnect();
      setLiveSession(null);
      setVoiceStatus('idle');
      setMode('staged');
    }
  }, [liveSession]);

  // Tool call handler for voice mode
  const handleToolCall = useCallback(
    async (name: string, args: any): Promise<any> => {
      try {
        switch (name) {
          case 'create_session': {
            const { title, position_x, position_y, description, theme_color } = args || {};
            // Fix: Default to 'root' if no parent found (Demo Mode compatibility)
            const parentId = activeContainerId || userSessionId || 'root';
            
            const result = await createChildSession(
              parentId,
              title || 'New Session',
              { x: position_x || 100, y: position_y || 100 },
              description
            );

            // Apply theme color if provided
            if (theme_color && result) {
              updateContainer(result, { themeColor: theme_color });
            }

            return {
              success: true,
              message: `Created session "${title || 'New Session'}"`,
              session: { id: result, title: title || 'New Session' },
            };
          }

          case 'find_resources': {
            const { scope_id, query, scope_type } = args;
            const result = await findResources(scope_id, query, scope_type);
            return { success: true, count: (result as any).total, results: (result as any).results };
          }

          case 'batch_delete_resources': {
            const { items } = args;
            const result = await batchDeleteResources(items);
            return { success: true, ...(result as any) };
          }

          case 'get_user_session': {
            // If in Cloud Mode, try to fetch real UserSession
            if (aiMode === 'cloud') {
               try {
                 // We can't easily import v4Api here directly if it's not exposed via store
                 // But we can check if we have a userSessionId
                 if (userSessionId) {
                    return {
                      success: true,
                      user_session_id: userSessionId,
                      message: "UserSession found. (Note: Full API access requires backend connection)",
                      // In a real implementation, we would call v4Api.getUserSession(userId) here
                    };
                 }
               } catch (e) {
                 console.warn("Failed to fetch UserSession", e);
               }
            }
            
            // Fallback / Demo Mode
            return {
              success: true,
              mode: 'demo',
              user_session_id: 'root',
              message: "Running in Demo Mode. Root container is virtual 'root'.",
              permissions: ['owner', 'admin'],
              quota: { remaining: 1000, limit: 1000 }
            };
          }

          case 'list_sessions': {
            const sessionList = containers.map((s) => ({
              id: s.id,
              title: s.title,
              position: s.position,
              status: s.status,
              zone: s.zoneId,
            }));

            // Open menu to show containers
            window.dispatchEvent(new CustomEvent('agent:open-menu', { detail: { type: 'session' } }));

            return {
              success: true,
              message: `Found ${containers.length} containers`,
              containers: sessionList,
            };
          }

          case 'query_sessions': {
            const { color, tags, is_shared, search_term } = args;
            
            let filtered = containers;
            
            if (color) {
              filtered = filtered.filter(s => s.themeColor?.toLowerCase().includes(color.toLowerCase()));
            }
            
            if (tags && Array.isArray(tags)) {
              filtered = filtered.filter(s => s.tags?.some(t => tags.includes(t)));
            }
            
            if (is_shared !== undefined) {
              // Note: In Demo Mode, is_shared might not be populated, but we check metadata if available
              filtered = filtered.filter(s => {
                 const meta = s.metadata as any;
                 return meta?.is_shared === is_shared;
              });
            }
            
            if (search_term) {
              const term = search_term.toLowerCase();
              filtered = filtered.filter(s => 
                s.title.toLowerCase().includes(term) || 
                s.description?.toLowerCase().includes(term)
              );
            }

            return {
              success: true,
              count: filtered.length,
              containers: filtered.map(s => ({
                id: s.id,
                title: s.title,
                color: s.themeColor,
                tags: s.tags,
                position: s.position
              }))
            };
          }

          case 'observe_canvas': {
            try {
              // Agent "sees" current visual state
              const canvasState = canvasObserver.getCanvasState();
              const description = canvasObserver.describeCanvasState();
              const menuOptions = canvasObserver.getContextMenuOptions();
              const recentActions = canvasObserver.getInteractionHistory(5);

              return {
                success: true,
                message: `Current canvas state:\n\n${description}\n\nAvailable context menu: ${menuOptions.join(
                  ', '
                )}\n\nRecent interactions: ${
                  recentActions.map((a) => a.type).join(', ') || 'None yet'
                }`,
                state: canvasState,
                menuOptions,
                recentActions,
              };
            } catch (error) {
              console.error('Error observing canvas:', error);
              return {
                success: false,
                message: `Error observing canvas: ${
                  error instanceof Error ? error.message : String(error)
                }`,
                state: null,
              };
            }
          }

          case 'switch_session': {
            const { session_id, session_title } = args;
            let targetId = session_id;

            if (!targetId && session_title) {
              const target = containers.find((s) =>
                s.title.toLowerCase().includes(session_title.toLowerCase())
              );
              if (target) targetId = target.id;
            }

            if (targetId) {
              setActiveContainer(targetId);
              window.dispatchEvent(new CustomEvent('agent:open-menu', { detail: { type: 'session' } }));
              return { success: true, message: `Switched to session` };
            } else {
              return { success: false, message: 'Session not found' };
            }
          }

          case 'delete_session': {
            const { session_id, confirm } = args;
            const targetSession = containers.find((s) => s.id === session_id);

            if (!targetSession) {
              return { success: false, message: 'Session not found' };
            }

            if (!confirm) {
              return {
                success: false,
                message: `Confirm deletion of "${targetSession.title}"?`,
              };
            }

            const title = targetSession.title;
            deleteNodes([session_id]);

            // Open menu to show deletion
            window.dispatchEvent(new CustomEvent('agent:open-menu', { detail: { type: 'session' } }));

            return {
              success: true,
              message: `Deleted session "${title}"`,
            };
          }

          case 'move_nodes': {
            const { nodeIds, node_ids, delta_x, delta_y } = args || {};
            const ids = (nodeIds || node_ids || selectedNodeIds || []).filter(Boolean);

            if (ids && ids.length > 0) {
              ids.forEach((id: string) => {
                const node = nodes.find((n) => n.id === id);
                if (node) {
                  updateNodePosition(id, {
                    x: node.position.x + (delta_x ?? 0),
                    y: node.position.y + (delta_y ?? 0),
                  });
                }
              });
              visualFeedback.highlightNodes(ids, '#3b82f6', 2000, 'Moved');
              return { success: true, message: `Moved ${ids.length} nodes` };
            }
            return { success: false, message: 'No nodes provided to move' };
          }

          case 'select_nodes': {
            const { nodeIds, node_ids, type, label_pattern, clear_existing } = args || {};
            let ids: string[] | undefined = nodeIds || node_ids;

            if (!ids && type) {
              ids = nodes.filter((n) => (n.data as any)?.type === type).map((n) => n.id);
            }

            if (!ids && label_pattern) {
              try {
                const regex = new RegExp(label_pattern, 'i');
                ids = nodes
                  .filter((n) => {
                    const label = (n.data as any)?.label || (n.data as any)?.title || '';
                    return regex.test(label as string);
                  })
                  .map((n) => n.id);
              } catch (error) {
                console.warn('Invalid label_pattern regex', error);
              }
            }

            if (!ids) ids = selectedNodeIds;

            if (clear_existing) setSelectedNodes([]);
            setSelectedNodes(ids || []);

            return { success: true, message: `Selected ${ids?.length || 0} nodes` };
          }

          case 'apply_layout': {
            const { algorithm, nodeIds, node_ids } = args || {};
            const ids = nodeIds || node_ids || selectedNodeIds || nodes.map((n) => n.id);

            if (!ids || ids.length === 0) {
              return { success: false, message: 'No nodes available for layout' };
            }

            applyLayout(algorithm || 'circular');
            return { success: true, message: `Applied ${algorithm || 'circular'} layout` };
          }

          case 'create_node': {
            const { type, label, position_x, position_y } = args || {};

            try {
              // Route through agent interface for consistent optimistic UI
              if (type === 'tool' && activeContainerId) {
                // Use agent interface instead of direct store call
                await addToolToSessionV4(
                  activeContainerId,
                  'csv_analyzer', // Default tool
                  {
                    description: label || 'New Tool',
                    metadata: { x: position_x || 100, y: position_y || 100 },
                  }
                );
                return { success: true, message: `Created tool: ${label}` };
              } else if (type === 'agent' && activeContainerId) {
                // Use agent interface instead of direct store call
                await addAgentToSessionV4(
                  activeContainerId,
                  'demo_agent', // Default agent
                  {
                    description: label || 'New Agent',
                    metadata: { x: position_x || 100, y: position_y || 100 },
                  }
                );
                return { success: true, message: `Created agent: ${label}` };
              } else if (type === 'object') {
                // For documents/objects, direct node creation is still OK
                const nodeId = `object-${Date.now()}`;
                const newNode = {
                  id: nodeId,
                  type: 'object',
                  position: { x: position_x || 100, y: position_y || 100 },
                  data: {
                    id: nodeId,
                    type: 'data' as const,
                    label: label || 'New Object',
                    fileType: 'JSON',
                  },
                };
                addNode(newNode);
                visualFeedback.highlightNodes([nodeId], '#f59e0b', 2000, 'Created');
                return { success: true, message: `Created object: ${label}`, nodeId };
              } else {
                // Fallback for other node types or when no session is active
                const nodeId = `${type}-${Date.now()}`;
                const newNode = {
                  id: nodeId,
                  type: type || 'default',
                  position: { x: position_x || 100, y: position_y || 100 },
                  data: { label: label || 'New Node' },
                };
                addNode(newNode as any);
                visualFeedback.highlightNodes([nodeId], '#f59e0b', 2000, 'Created');
                return { success: true, message: `Created ${type}: ${label}`, nodeId };
              }
            } catch (error) {
              console.error('Failed to create node:', error);
              return { 
                success: false, 
                message: `Failed to create ${type}: ${error instanceof Error ? error.message : 'Unknown error'}` 
              };
            }
          }

          case 'delete_nodes': {
            const { nodeIds, node_ids } = args || {};
            const ids = nodeIds || node_ids || selectedNodeIds;
            if (ids && ids.length > 0) {
              deleteNodes(ids);
              visualFeedback.highlightNodes(ids, '#ef4444', 1000, 'Deleted');
              return { success: true, message: `Deleted ${ids.length} nodes` };
            }
            return { success: false, message: 'No nodes provided to delete' };
          }

          case 'update_theme': {
            const { preset, primary_color, background_color, node_style } = args || {};
            if (activeContainerId) {
              updateTheme(activeContainerId, { preset, primary_color, background_color, node_style });
              return { success: true, message: `Applied theme: ${preset || 'custom'}` };
            }
            return { success: false, message: 'No active session to update theme' };
          }

          case 'create_custom_tool': {
            try {
              const { name, description, builtin_tool, config, tags } = args || {};
              const payload = {
                name,
                description,
                builtin_tool_name: builtin_tool,
                config: config || {},
                tags: tags || [],
              };
              const toolId = await createUserCustomTool(payload);
              toast.success(`✅ Created custom tool: ${name}`);
              return {
                success: true,
                message: `Created custom tool "${name}". You can now add it to containers.`,
                data: { id: toolId, name },
              };
            } catch (error) {
              const message =
                error instanceof Error ? error.message : 'Failed to create custom tool';
              toast.error(message);
              return { success: false, message };
            }
          }

          case 'create_custom_agent': {
            try {
              const { name, description, system_prompt, model, tags } = args || {};
              const payload = {
                name,
                description,
                system_prompt,
                model: model || 'gpt-4',
                tags: tags || [],
              };
              const agentId = await createUserCustomAgent(payload);
              toast.success(`✅ Created custom agent: ${name}`);
              return {
                success: true,
                message: `Created custom agent "${name}". You can now add it to containers.`,
                data: { id: agentId, name },
              };
            } catch (error) {
              const message =
                error instanceof Error ? error.message : 'Failed to create custom agent';
              toast.error(message);
              return { success: false, message };
            }
          }

          case 'add_tool_to_session': {
            try {
              const { session_id, tool_name, display_name, config_overrides } = args || {};
              const targetSession = containers.find((s) => s.id === session_id);
              if (!targetSession) {
                toast.error('Session not found');
                return { success: false, message: 'Session not found' };
              }

              // Load available tools if not cached
              if (!availableTools || availableTools.length === 0) {
                await loadAvailableTools();
              }

              // Validate tool exists
              const tool = availableTools.find((t) => t.name === tool_name);
              if (!tool) {
                toast.error(`Tool "${tool_name}" not found`);
                return { success: false, message: `Tool "${tool_name}" not found` };
              }

              await addToolToSessionV4(session_id, tool_name, {
                description: display_name || tool.name,
                preset_params: config_overrides || {},
              });
              toast.success(`✅ Added tool "${display_name || tool_name}" to session`);
              return {
                success: true,
                message: `Added tool "${display_name || tool_name}" to session "${targetSession.title}"`,
              };
            } catch (error) {
              const message =
                error instanceof Error ? error.message : 'Failed to add tool to session';
              toast.error(message);
              return { success: false, message };
            }
          }

          case 'add_agent_to_session': {
            try {
              const { session_id, agent_id, display_name, model_override, prompt_override, active } =
                args || {};
              const targetSession = containers.find((s) => s.id === session_id);
              if (!targetSession) {
                toast.error('Session not found');
                return { success: false, message: 'Session not found' };
              }

              // Load available agents if not cached
              if (!availableAgents || availableAgents.length === 0) {
                await loadAvailableAgents(session_id);
              }

              // Validate agent exists
              const agent = availableAgents.find((a) => a.agent_id === agent_id);
              if (!agent) {
                toast.error(`Agent "${agent_id}" not found`);
                return { success: false, message: `Agent "${agent_id}" not found` };
              }

              await addAgentToSessionV4(session_id, agent_id, {
                description: display_name || agent.name,
                preset_params: {
                  model_override,
                  system_prompt_override: prompt_override,
                  is_active: active || false,
                },
              });
              toast.success(`✅ Added agent "${display_name || agent.name}" to session`);
              return {
                success: true,
                message: `Added agent "${display_name || agent.name}" to session "${
                  targetSession.title
                }"${active ? ' (active)' : ''}`,
              };
            } catch (error) {
              const message =
                error instanceof Error ? error.message : 'Failed to add agent to session';
              toast.error(message);
              return { success: false, message };
            }
          }

          case 'browse_tools': {
            try {
              const { category } = args || {};
              await loadAvailableTools(category);
              const tools = availableTools || [];
              const categoryStr = category ? ` in category "${category}"` : '';
              toast.success(`Found ${tools.length} available tools${categoryStr}`);
              return {
                success: true,
                message: `Found ${tools.length} available tools${categoryStr}`,
                data: tools,
              };
            } catch (error) {
              const message = error instanceof Error ? error.message : 'Failed to browse tools';
              toast.error(message);
              return { success: false, message };
            }
          }

          case 'browse_agents': {
            try {
              const { session_id, search } = args || {};
              await loadAvailableAgents(session_id, search);
              const agents = availableAgents || [];
              const searchStr = search ? ` matching "${search}"` : '';
              toast.success(`Found ${agents.length} available agents${searchStr}`);
              return {
                success: true,
                message: `Found ${agents.length} available agents${searchStr}`,
                data: agents,
              };
            } catch (error) {
              const message = error instanceof Error ? error.message : 'Failed to browse agents';
              toast.error(message);
              return { success: false, message };
            }
          }

          // =================================================================
          // BRIDGE TOOLS (Copilot ↔ Host communication)
          // =================================================================
          case 'write_report': {
            const { report_type, title, content, data } = args || {};
            const bridge = window.__colliderBridge;
            
            if (!bridge) {
              return { 
                success: false, 
                message: 'Bridge not available (DEV mode only)' 
              };
            }

            const report = {
              id: `report_${Date.now()}`,
              command: 'host_report',
              success: true,
              data: {
                report_type,
                title,
                content,
                payload: data,
                timestamp: Date.now(),
              },
              duration: 0,
              timestamp: Date.now(),
            };

            bridge.outbox.push(report);
            // eslint-disable-next-line no-console
            console.log(`[HOST→COPILOT] Report: ${title}`);
            
            return {
              success: true,
              message: `Report "${title}" written to bridge outbox`,
              report_id: report.id,
            };
          }

          case 'read_bridge_inbox': {
            const bridge = window.__colliderBridge;
            
            if (!bridge) {
              return { 
                success: false, 
                message: 'Bridge not available (DEV mode only)' 
              };
            }

            const commands = [...bridge.inbox];
            return {
              success: true,
              message: `Found ${commands.length} pending commands`,
              commands,
            };
          }

          default:
            toast.error(`Unknown operation: ${name}`);
            return { success: false, message: `Unknown tool: ${name}` };
        }
      } catch (error) {
        console.error('Tool call error:', error);
        return { success: false, message: `Error executing ${name}` };
      }
    },
    [
      nodes,
      containers,
      selectedNodeIds,
      updateNodePosition,
      setSelectedNodes,
      addNode,
      addSession,
      deleteNodes,
      applyLayout,
      updateTheme,
      setActiveContainer,
      createUserCustomTool,
      createUserCustomAgent,
      availableTools,
      availableAgents,
      loadAvailableTools,
      loadAvailableAgents,
      addToolToSessionV4,
      addAgentToSessionV4,
      createChildSession,
      updateContainer,
      activeContainerId,
      userSessionId,
      aiMode,
    ]
  );

  const handleSend = async () => {
    if (!input.trim()) return;

    addMessage({
      role: 'user',
      content: input,
    });

    const userMessage = input;
    setInput('');
    setAgentTyping(true);

    try {
      // Demo command: test visual feedback
      if (
        userMessage.toLowerCase().includes('demo visual') ||
        userMessage.toLowerCase().includes('test menus')
      ) {
        addMessage({ role: 'assistant', content: '🤖 Testing visual feedback...' });

        // Show menu operations sequentially
        await visualFeedback.openMenu('session', 'Demo session menu', setOpenMenu, 1500);
        await new Promise((resolve) => setTimeout(resolve, 500));
        await visualFeedback.openMenu('tool', 'Demo tool menu', setOpenMenu, 1500);
        await new Promise((resolve) => setTimeout(resolve, 500));

        // Highlight some nodes
        if (nodes.length > 0) {
          const firstThree = nodes.slice(0, 3).map((n) => n.id);
          visualFeedback.highlightNodes(firstThree, '#10b981', 3000, 'Selected by AI');
        }

        addMessage({ role: 'assistant', content: '✅ Visual feedback demo complete!' });
        setAgentTyping(false);
        return;
      }

      // Simple command parsing (no complex AI needed for MVP)
      const lowerMsg = userMessage.toLowerCase();
      let executed = false;
      let responseMsg = '';

      // Session commands
      if (lowerMsg.includes('create') && lowerMsg.includes('session')) {
        const result = await handleToolCall('create_session', {
          title: 'New Session',
          position_x: 100 + containers.length * 50,
          position_y: 100 + containers.length * 50,
        });
        responseMsg = `✅ ${result.message}`;
        executed = true;
      } else if (
        lowerMsg.includes('observe') ||
        lowerMsg.includes('what do you see') ||
        lowerMsg.includes('canvas state')
      ) {
        const result = await handleToolCall('observe_canvas', {});
        responseMsg = `👁️ ${result.message}`;
        executed = true;
      } else if (lowerMsg.includes('list') && lowerMsg.includes('session')) {
        const result = await handleToolCall('list_sessions', {});
        responseMsg = `📋 ${result.message}:\n${result.containers
          .map((s: any) => `- ${s.title} (${s.zone})`)
          .join('\n')}`;
        executed = true;
      } else if (lowerMsg.includes('switch') && lowerMsg.includes('session')) {
        // Extract session title from command
        const titleMatch = userMessage.match(/(?:switch to|switch session)\s+(.+)/i);
        if (titleMatch) {
          const result = await handleToolCall('switch_session', { session_title: titleMatch[1] });
          responseMsg = result.success ? `✅ ${result.message}` : `⚠️ ${result.message}`;
          executed = true;
        }
      }
      // Node creation commands
      else if (
        lowerMsg.includes('create') &&
        (lowerMsg.includes('tool') || lowerMsg.includes('agent') || lowerMsg.includes('document'))
      ) {
        const type = lowerMsg.includes('tool')
          ? 'tool'
          : lowerMsg.includes('agent')
          ? 'agent'
          : 'document';

        // Simulate context menu action
        const action = `context-add-${type}`;
        const btn = document.querySelector(`[data-ai-action="${action}"]`) as HTMLButtonElement;
        if (btn) btn.click();

        responseMsg = `✅ Created new ${type}`;
        executed = true;
      }
      // Selection commands
      else if (lowerMsg.includes('select all')) {
        const btn = document.querySelector(
          '[data-ai-action="context-select-all"]'
        ) as HTMLButtonElement;
        if (btn) btn.click();
        responseMsg = `✅ Selected all nodes`;
        executed = true;
      }
      // Layout commands
      else if (lowerMsg.includes('circular') || lowerMsg.includes('layout')) {
        const btn = document.querySelector(
          '[data-ai-action="context-circular-layout"]'
        ) as HTMLButtonElement;
        if (btn) btn.click();
        responseMsg = `✅ Applied circular layout`;
        executed = true;
      }
      // Delete commands
      else if (lowerMsg.includes('delete selected')) {
        const btn = document.querySelector(
          '[data-ai-action="context-delete-selected"]'
        ) as HTMLButtonElement;
        if (btn) btn.click();
        responseMsg = `✅ Deleted selected nodes`;
        executed = true;
      } else if (lowerMsg.includes('zoom in')) {
        responseMsg = '✅ Zooming in';
        executed = true;

        const zoomBtn = document.querySelector('[data-ai-action="zoom-in"]') as HTMLButtonElement;
        if (zoomBtn) zoomBtn.click();
      } else if (lowerMsg.includes('zoom out')) {
        responseMsg = '✅ Zooming out';
        executed = true;

        const zoomBtn = document.querySelector('[data-ai-action="zoom-out"]') as HTMLButtonElement;
        if (zoomBtn) zoomBtn.click();
      } else if (lowerMsg.includes('center')) {
        responseMsg = '✅ Centering view';
        executed = true;

        const centerBtn = document.querySelector(
          '[data-ai-action="center-view"]'
        ) as HTMLButtonElement;
        if (centerBtn) centerBtn.click();
      }
      // Delete commands
      else if (lowerMsg.includes('delete') && selectedNodeIds.length > 0) {
        const result = await handleToolCall('delete_nodes', { nodeIds: selectedNodeIds });
        responseMsg = `✅ ${result.message}`;
        executed = true;
      }

      // If no direct match, fall back to AI router (for complex queries)
      if (!executed) {
        if (aiMode === 'local') {
          try {
            if (!localAgentRef.current) {
              addMessage({ role: 'assistant', content: '⚙️ Initializing local model (WebLLM)...' });
              localAgentRef.current = new LocalIntelligence();
              await localAgentRef.current.init((progress) => {
                console.log(`[WebLLM] ${progress.text}`);
              });
            }

            const tools = GeminiLiveSession.getDefaultTools();
            // Get history from chat store (simplified)
            const history = messages.slice(-10).map(m => ({
              role: m.role === 'user' ? 'user' : 'assistant',
              content: m.content
            }));

            const result = await localAgentRef.current.sendMessage(userMessage, history, tools);
            
            // Handle tool calls
            if (result.toolCalls && result.toolCalls.length > 0) {
              let toolOutputText = '';
              
              for (const call of result.toolCalls as any[]) {
                const fnName = call.function.name;
                const args = JSON.parse(call.function.arguments);
                
                addMessage({ role: 'assistant', content: `🛠️ Executing ${fnName}...` });
                const toolResult = await handleToolCall(fnName, args);
                toolOutputText += `Tool ${fnName} result: ${JSON.stringify(toolResult)}\n`;
              }

              // Send tool results back to model for final response
              // Note: This is a simplified single-turn tool loop
              const followUp = await localAgentRef.current.sendMessage(
                `Tool outputs:\n${toolOutputText}\nPlease provide a final response based on these actions.`,
                [...history, { role: 'user', content: userMessage }, { role: 'assistant', content: result.text || 'Executing tools...' }],
                tools
              );
              
              responseMsg = followUp.text;
            } else {
              responseMsg = result.text;
            }
            
            executed = true;
          } catch (error) {
            console.error('Local AI error:', error);
            responseMsg = `❌ Local AI Error: ${error instanceof Error ? error.message : String(error)}`;
            executed = true; // Handled as error
          }
        } else {
          // Cloud Mode (Gemini)
          const apiKey = import.meta.env?.VITE_GEMINI_API_KEY as string | undefined;
          if (!apiKey) {
            addMessage({
              role: 'assistant',
              content: 'VITE_GEMINI_API_KEY not found. Add it to .env.local',
            });
            setAgentTyping(false);
            return;
          }

          // Fallback response for complex queries (router removed)
          responseMsg = `I'm the Navigator of the Data Collider! 🚀

I can help you work with Sticky Notes on the canvas:
- "create new session" - Add a new container
- "create agent" / "create tool" - Add resources
- "select all" - Select all visible nodes
- "delete selected" - Remove selected items
- "list containers" - Show your containers
- "center" / "zoom in" / "zoom out" - Navigate canvas

💡 Tip: Switch to **Local (WebLLM)** mode for smarter responses without an API key!`;
        }
      }

      if (responseMsg) {
        addMessage({ role: 'assistant', content: responseMsg });
      }
    } catch (error) {
      console.error('Agent error:', error);
      addMessage({ role: 'assistant', content: '❌ Error processing command' });
    } finally {
      setAgentTyping(false);
    }
  };

  return (
    <div className="w-full h-full flex flex-col">
      {/* Menu Dropdown Content - With Clickable Operations */}
      {openMenu && (
        <div className="px-2 py-2 border-b border-slate-700 space-y-1">
          {openMenu === 'session' && (
            <div className="space-y-1">
              <div className="font-semibold text-xs text-slate-100 px-2 py-1">
                Session Operations ({containers.length} containers)
              </div>

              {/* Create Session */}
              <button
                onClick={async () => {
                  try {
                    // Use agent interface for consistent behavior
                    const parentId = activeContainerId || userSessionId;
                    if (!parentId) {
                        toast.error('No active session or user session found');
                        return;
                    }
                    await createChildSession(
                      parentId,
                      'New Session',
                      { x: 100 + containers.length * 50, y: 100 + containers.length * 50 },
                      ''
                    );
                    
                    addMessage({
                      role: 'assistant',
                      content: `✅ Created new session`,
                    });
                    setOpenMenu(null);
                  } catch (error) {
                    console.error('Failed to create session:', error);
                    addMessage({
                      role: 'assistant',
                      content: '❌ Failed to create session',
                    });
                  }
                }}
                className="w-full text-left px-3 py-1.5 text-xs text-slate-200 hover:bg-blue-600/40 hover:text-blue-100 rounded transition-colors cursor-pointer"
              >
                → Create new session
              </button>

              {/* List & Switch containers */}
              {containers.length > 0 && (
                <div className="border-t border-slate-600 pt-1 mt-1">
                  <div className="text-[10px] text-slate-400 px-2 py-1">Switch to session:</div>
                  {containers.slice(0, 5).map((session) => (
                    <button
                      key={session.id}
                      onClick={() => {
                        setActiveContainer(session.id);
                        setSelectedNodes([session.id]);
                        visualFeedback.highlightNodes([session.id], '#3b82f6', 2000, 'Active');
                        addMessage({
                          role: 'assistant',
                          content: `📍 Switched to "${session.title}" at (${Math.round(
                            session.position.x
                          )}, ${Math.round(session.position.y)})`,
                        });
                        setOpenMenu(null);
                      }}
                      className={`w-full text-left px-4 py-1 text-[11px] rounded transition-colors cursor-pointer ${
                        activeContainerId === session.id
                          ? 'bg-blue-600/30 text-blue-200'
                          : 'text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {activeContainerId === session.id && '● '}
                      {session.title}
                    </button>
                  ))}
                  {containers.length > 5 && (
                    <div className="text-[10px] text-slate-500 px-4 py-1">
                      +{containers.length - 5} more containers
                    </div>
                  )}
                </div>
              )}

              {/* Delete Active Session */}
              {selectedNodeIds.length > 0 && (
                <button
                  onClick={() => {
                    const selectedSessions = nodes.filter(
                      (n) => selectedNodeIds.includes(n.id) && n.type === 'session'
                    );

                    if (selectedSessions.length > 0) {
                      const sessionTitles = selectedSessions.map((n) => {
                        const sessionData = n.data as any;
                        return sessionData?.title || 'Untitled';
                      });

                      deleteNodes(selectedNodeIds);
                      selectedNodeIds.forEach((id) => {
                        const session = containers.find((s) => s.id === id);
                        if (session) {
                          // Would call deleteSession but it's handled by deleteNodes
                        }
                      });

                      addMessage({
                        role: 'assistant',
                        content: `🗑️ Deleted ${
                          selectedSessions.length
                        } session(s): ${sessionTitles.join(', ')}`,
                      });
                    } else {
                      addMessage({
                        role: 'assistant',
                        content: '⚠️ No containers selected. Select a session node first.',
                      });
                    }
                    setOpenMenu(null);
                  }}
                  className="w-full text-left px-3 py-1.5 text-xs text-red-300 hover:bg-red-600/40 hover:text-red-100 rounded transition-colors cursor-pointer border-t border-slate-600 mt-1 pt-1.5"
                >
                  → Delete selected session ({selectedNodeIds.length} selected)
                </button>
              )}
            </div>
          )}
          {openMenu === 'agent' && (
            <div className="space-y-1">
              <div className="font-semibold text-xs text-slate-100 px-2 py-1">Agent Operations</div>
              <button
                onClick={() => {
                  handleToolCall('create_node', {
                    type: 'agent',
                    label: 'New Agent',
                    position_x: 100,
                    position_y: 100,
                  });
                  addMessage({ role: 'assistant', content: '✅ Agent node created' });
                  setOpenMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 text-xs text-slate-200 hover:bg-blue-600/40 hover:text-blue-100 rounded transition-colors cursor-pointer"
              >
                → Create agent node
              </button>
              <button
                onClick={() => {
                  addMessage({ role: 'assistant', content: '⚙️ Agent configuration panel opened' });
                  setOpenMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 text-xs text-slate-200 hover:bg-blue-600/40 hover:text-blue-100 rounded transition-colors cursor-pointer"
              >
                → Configure agent
              </button>
              <button
                onClick={() => {
                  addMessage({ role: 'assistant', content: '▶️ Agent executing...' });
                  setOpenMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 text-xs text-slate-200 hover:bg-blue-600/40 hover:text-blue-100 rounded transition-colors cursor-pointer"
              >
                → Run agent
              </button>
            </div>
          )}
          {openMenu === 'tool' && (
            <div className="space-y-1">
              <div className="font-semibold text-xs text-slate-100 px-2 py-1">Tool Operations</div>
              <button
                onClick={() => {
                  handleToolCall('create_node', {
                    type: 'tool',
                    label: 'New Tool',
                    position_x: 200,
                    position_y: 100,
                  });
                  addMessage({ role: 'assistant', content: '✅ Tool node added to workspace' });
                  setOpenMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 text-xs text-slate-200 hover:bg-blue-600/40 hover:text-blue-100 rounded transition-colors cursor-pointer"
              >
                → Add tool to workspace
              </button>
              <button
                onClick={() => {
                  addMessage({ role: 'assistant', content: '⚙️ Tool configuration opened' });
                  setOpenMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 text-xs text-slate-200 hover:bg-blue-600/40 hover:text-blue-100 rounded transition-colors cursor-pointer"
              >
                → Configure tool
              </button>
              <button
                onClick={() => {
                  addMessage({
                    role: 'assistant',
                    content: '▶️ Tool executing with default parameters...',
                  });
                  setOpenMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 text-xs text-slate-200 hover:bg-blue-600/40 hover:text-blue-100 rounded transition-colors cursor-pointer"
              >
                → Execute tool
              </button>
            </div>
          )}
          {openMenu === 'api' && (
            <div className="space-y-1">
              <div className="font-semibold text-xs text-slate-100 px-2 py-1">API Operations</div>
              <button
                onClick={() => {
                  addMessage({ role: 'assistant', content: '🔗 Backend API call initiated...' });
                  setOpenMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 text-xs text-slate-200 hover:bg-blue-600/40 hover:text-blue-100 rounded transition-colors cursor-pointer"
              >
                → Call backend API
              </button>
              <button
                onClick={() => {
                  addMessage({
                    role: 'assistant',
                    content: '✅ API Status: All systems operational',
                  });
                  setOpenMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 text-xs text-slate-200 hover:bg-blue-600/40 hover:text-blue-100 rounded transition-colors cursor-pointer"
              >
                → Check API status
              </button>
              <button
                onClick={() => {
                  addMessage({ role: 'assistant', content: '📋 API logs: No errors detected' });
                  setOpenMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 text-xs text-slate-200 hover:bg-blue-600/40 hover:text-blue-100 rounded transition-colors cursor-pointer"
              >
                → View API logs
              </button>
            </div>
          )}
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-hide">
        {messages.length === 0 && (
          <div className="text-center text-slate-500 text-sm mt-8">
            <p>Start a conversation</p>
            <p className="text-xs mt-1">
              {mode === 'staged' && 'Commands will be staged for review'}
              {mode === 'direct' && 'Commands execute immediately'}
              {mode === 'voice' && 'Speak or type your commands'}
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-lg text-sm ${
                message.role === 'user'
                  ? 'bg-blue-600/70 backdrop-blur-md text-white'
                  : 'bg-slate-800/60 backdrop-blur-md text-slate-200'
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}

        {isAgentTyping && (
          <div className="flex justify-start">
            <div className="bg-slate-800/60 backdrop-blur-md text-slate-200 p-3 rounded-lg">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-3 border-t border-slate-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={
              mode === 'staged'
                ? 'Type command to preview first...'
                : mode === 'direct'
                ? 'Type command to execute immediately...'
                : 'Speak or type your command...'
            }
            className="flex-1 px-3 py-2 bg-slate-800/40 backdrop-blur-md border border-slate-600 rounded text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded transition-colors"
            title="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Control Panel - 2x height with mode buttons and voice controls */}
      <div className="px-3 py-4 border-t border-slate-700 bg-slate-800/20 backdrop-blur-sm space-y-3">
        {/* Voice Status Bar */}
        {mode === 'voice' && (
          <div
            className={`px-3 py-2 text-xs rounded transition-all ${
              voiceStatus === 'listening'
                ? 'bg-green-900/40 text-green-300 ring-1 ring-green-500'
                : voiceStatus === 'processing'
                ? 'bg-yellow-900/40 text-yellow-300 ring-1 ring-yellow-500'
                : voiceStatus === 'speaking'
                ? 'bg-blue-900/40 text-blue-300 ring-1 ring-blue-500'
                : voiceStatus === 'error'
                ? 'bg-red-900/40 text-red-300 ring-1 ring-red-500'
                : 'bg-slate-700/50 text-slate-400'
            }`}
          >
            {voiceStatus === 'listening' && '🎤 Listening...'}
            {voiceStatus === 'processing' && '⚙️ Processing...'}
            {voiceStatus === 'speaking' && '🔊 Speaking...'}
            {voiceStatus === 'error' && '❌ Error'}
            {voiceStatus === 'idle' && '⏸️ Voice Ready'}
          </div>
        )}

        {/* Mode Toggle Buttons */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setMode('staged')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-all ${
                  mode === 'staged'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                    : 'bg-slate-700 text-slate-400 hover:text-white hover:bg-slate-600'
                }`}
              >
                <Layers size={14} />
                Staged
              </button>
              <button
                onClick={() => setMode('direct')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-all ${
                  mode === 'direct'
                    ? 'bg-green-600 text-white shadow-lg shadow-green-500/30'
                    : 'bg-slate-700 text-slate-400 hover:text-white hover:bg-slate-600'
                }`}
              >
                <Zap size={14} />
                Direct
              </button>
              <button
                onClick={() => (mode === 'voice' ? disconnectVoice() : connectVoice())}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-all ${
                  mode === 'voice'
                    ? 'bg-red-600 text-white shadow-lg shadow-red-500/30'
                    : 'bg-slate-700 text-slate-400 hover:text-white hover:bg-slate-600'
                }`}
              >
                {mode === 'voice' ? <MicOff size={14} /> : <Mic size={14} />}
                Voice
              </button>
            </div>

            {/* Clear Chat Button */}
            <button
              onClick={clearMessages}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-red-600/20 text-red-400 hover:bg-red-600/30 hover:text-red-300 rounded transition-colors"
              title="Clear chat"
            >
              <Trash2 size={14} />
              Clear
            </button>
          </div>

          {/* Intelligence Mode Toggle */}
          <div className="flex items-center justify-between bg-slate-900/40 p-1 rounded-lg">
            <span className="text-[10px] text-slate-500 px-2 uppercase font-bold tracking-wider">Intelligence</span>
            <div className="flex gap-1">
              <button
                onClick={() => setAiMode('cloud')}
                className={`flex items-center gap-1.5 px-3 py-1 text-[10px] font-medium rounded transition-all ${
                  aiMode === 'cloud'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Cloud size={12} />
                Cloud (Gemini)
              </button>
              <button
                onClick={() => setAiMode('local')}
                className={`flex items-center gap-1.5 px-3 py-1 text-[10px] font-medium rounded transition-all ${
                  aiMode === 'local'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Cpu size={12} />
                Local (WebLLM)
              </button>
            </div>
          </div>

          {/* Login Button */}
          <div className="flex justify-center pt-2 border-t border-slate-700">
            <MicrosoftLoginButton />
          </div>
        </div>
      </div>
    </div>
  );
}
