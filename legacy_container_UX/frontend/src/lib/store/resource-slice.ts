import { WorkspaceSliceCreator } from './types';
import * as api from '../api';
import { AgentDefinition, ToolDefinition, CustomToolDefinition, CustomAgentDefinition, CreateToolPayload, CreateAgentPayload } from '../api-types';
import { ResourceCategory } from '../types';
import { generateId } from '../id-generator';
import { DEMO_AGENT_DEFINITIONS, DEMO_TOOL_DEFINITIONS } from '../demo-data';
import { isDemoMode } from '../env';

export const createResourceSlice: WorkspaceSliceCreator<any> = (set, get) => ({
  // State
  availableTools: [],
  availableAgents: [],
  userCustomTools: [],
  userCustomAgents: [],
  toolsCache: null,
  agentsCache: null,

  // Actions
  loadAvailableTools: async (category: ResourceCategory | 'all', forceRefresh: boolean = false) => {
    if (isDemoMode()) {
      const tools: ToolDefinition[] = DEMO_TOOL_DEFINITIONS.map(d => ({
        tool_id: d.definition_id,
        name: d.title,
        description: d.description || '',
        category: (d.category as any) || 'general',
        is_system: true,
        config_schema: d.spec || {},
        tier_required: (d.tier as any) || 'FREE',
        tags: d.tags || [],
      }));

      set({
        availableTools: tools,
        toolsCache: { timestamp: Date.now(), category },
      });
      console.log(`🎮 Loaded ${tools.length} demo tools`);
      return;
    }

    const cache = get().toolsCache;
    const CACHE_DURATION_MS = 5 * 60 * 1000; // 5 minutes

    // Use cache if fresh and category matches
    if (
      !forceRefresh &&
      cache &&
      Date.now() - cache.timestamp < CACHE_DURATION_MS &&
      cache.category === category
    ) {
      console.log('✅ Using cached available tools');
      return;
    }

    try {
      // V4: Use listDefinitions
      const definitions = await api.listDefinitions('tool');
      const tools: ToolDefinition[] = definitions.map(d => ({
        tool_id: d.definition_id,
        name: d.title,
        description: d.description || '',
        category: (d.category as any) || 'general',
        is_system: true,
        config_schema: d.spec || {},
        tier_required: (d.tier as any) || 'FREE',
        tags: d.tags || [],
      }));
      
      set({
        availableTools: tools,
        toolsCache: { timestamp: Date.now(), category },
      });
      console.log(`✅ Loaded ${tools.length} available tools (V4)`);
    } catch (error) {
      console.error('Failed to load available tools:', error);
      set({ availableTools: [] });
    }
  },

  loadAvailableAgents: async (sessionId: string | null, search: string, forceRefresh: boolean = false) => {
    if (isDemoMode()) {
      const agents: AgentDefinition[] = DEMO_AGENT_DEFINITIONS.map(d => ({
        agent_id: d.definition_id,
        name: d.title,
        description: d.description || '',
        is_system: true,
        tier_required: (d.tier as any) || 'FREE',
        tags: d.tags || [],
      }));

      set({
        availableAgents: agents,
        agentsCache: { timestamp: Date.now(), sessionId, search },
      });
      console.log(`🎮 Loaded ${agents.length} demo agents`);
      return;
    }

    const cache = get().agentsCache;
    const CACHE_DURATION_MS = 5 * 60 * 1000; // 5 minutes

    // Use cache if fresh and parameters match
    if (
      !forceRefresh &&
      cache &&
      Date.now() - cache.timestamp < CACHE_DURATION_MS &&
      cache.sessionId === sessionId &&
      cache.search === search
    ) {
      console.log('✅ Using cached available agents');
      return;
    }

    try {
      // V4: Use listDefinitions
      const definitions = await api.listDefinitions('agent');
      const agents: AgentDefinition[] = definitions.map(d => ({
        agent_id: d.definition_id,
        name: d.title,
        description: d.description || '',
        is_system: true,
        tier_required: (d.tier as any) || 'FREE',
        tags: d.tags || [],
      }));

      set({
        availableAgents: agents,
        agentsCache: { timestamp: Date.now(), sessionId, search },
      });
      console.log(`✅ Loaded ${agents.length} available agents (V4)`);
    } catch (error) {
      console.error('Failed to load available agents:', error);
      set({ availableAgents: [] });
    }
  },

  loadUserCustomDefinitions: async (_userId: string) => {
    // TODO: Implement fetching user custom definitions when API supports it
    // For now, we can assume they are part of the listDefinitions response 
    // or we need a specific endpoint.
    console.warn('loadUserCustomDefinitions not fully implemented');
    set({ userCustomTools: [], userCustomAgents: [] });
  },

  createUserCustomTool: async (payload: CreateToolPayload) => {
    const userId = get().userIdentity?.id || 'user';
    const newTool: CustomToolDefinition = {
      tool_id: generateId('tool'),
      user_id: userId,
      type: 'builtin',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      ...payload,
      tags: payload.tags || []
    };
    
    // Optimistic update
    set((state) => ({
      userCustomTools: [...state.userCustomTools, newTool]
    }));
    
    // TODO: Call API
    console.warn('createUserCustomTool API call mocked');
  },

  createUserCustomAgent: async (payload: CreateAgentPayload) => {
    const userId = get().userIdentity?.id || 'user';
    const newAgent: CustomAgentDefinition = {
      agent_id: generateId('agent'),
      user_id: userId,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      ...payload,
      tags: payload.tags || []
    };
    
    // Optimistic update
    set((state) => ({
      userCustomAgents: [...state.userCustomAgents, newAgent]
    }));
    
    // TODO: Call API
    console.warn('createUserCustomAgent API call mocked');
  },
});

