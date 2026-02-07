import { WorkspaceSliceCreator } from './types';
import * as api from '../api';
import { Container, ResourceLink, ContainerType, isContainerDiveable, getContainerTypeFromId } from '../api';
import { toast } from '../toast-store';
import { CustomNodeData, CustomNode, ContainerVisualState } from '../types';
import { isDemoMode } from '../env';

// Tier + depth helpers
const resolveUserTier = (): string => {
  const raw = (
    localStorage.getItem('user_tier') ||
    localStorage.getItem('tier') ||
    import.meta.env.VITE_USER_TIER ||
    import.meta.env.VITE_TIER ||
    'ENTERPRISE'
  ).toString().toUpperCase();

  if (raw.includes('FREE')) return 'FREE';
  if (raw.includes('PRO')) return 'PRO';
  if (raw.includes('ENTER')) return 'ENTERPRISE';
  return raw;
};

const maxDepthForTier = (tier: string) => (tier === 'FREE' ? 2 : 4);
const navDepthFromBreadcrumbs = (breadcrumbs?: { id: string; title: string; type: string }[]) =>
  Math.max(0, (breadcrumbs?.length || 1) - 1);

const enforceTierDepth = (
  state: { activeContainerType: ContainerType | null; breadcrumbs: { id: string; title: string; type: string }[] },
  options?: { isTerminal?: boolean }
) => {
  const tier = resolveUserTier();
  const maxDepth = maxDepthForTier(tier);
  const navDepth = navDepthFromBreadcrumbs(state.breadcrumbs);
  const isTerminal = options?.isTerminal ?? false;

  if (state.activeContainerType === 'source') {
    toast.warning('Source containers are terminal. Only Users may be added here.');
    return { ok: false, reason: 'source-terminal' as const };
  }

  if (!isTerminal && navDepth >= maxDepth) {
    toast.warning(`Depth limit reached for ${tier}. Terminals only at L${maxDepth}.`);
    return { ok: false, reason: 'depth-limit' as const };
  }

  return { ok: true as const, navDepth, maxDepth, tier };
};

export const createContainerSlice: WorkspaceSliceCreator<any> = (set, get) => ({
  // State
  containers: [],
  activeContainerId: null,
  activeContainerType: null,
  userSessionId: null,
  containerRegistry: {},
  breadcrumbs: [{ id: 'root', title: 'Workspace', type: 'session' }],

  // Legacy V4 compatibility - computed at access time via store selector
  // NOTE: These should be accessed via computed selectors, not stored directly
  // activeSessionId: use selector -> (s) => s.activeContainerId
  // workspaceResources: use selector -> (s) => s.containerRegistry[s.userSessionId]?.resources || []

  // V4 Compatibility Actions
  loadWorkspaceResources: async () => {
    // This just calls loadContainer with null (root)
    await get().loadContainer(null, 'session', true);
  },

  addToolToSessionV4: async (sessionId: string, toolId: string, data: any) => {
    console.log('[V4 Compat] addToolToSessionV4 called - use V5 API instead');
    // Stub - should use V5 addResourceLink
    const position = data.position || { x: 100, y: 100 };
    await get().addResourceLink(sessionId, {
      resource_type: 'tool',
      resource_id: toolId,
      metadata: { x: position.x, y: position.y },
    });
  },

  addAgentToSessionV4: async (sessionId: string, agentId: string, data: any) => {
    console.log('[V4 Compat] addAgentToSessionV4 called - use V5 API instead');
    // Stub - should use V5 addResourceLink
    const position = data.position || { x: 100, y: 100 };
    await get().addResourceLink(sessionId, {
      resource_type: 'agent',
      resource_id: agentId,
      description: 'New Agent',
      metadata: { x: position.x, y: position.y },
    });
  },

  addSourceToSessionV4: async (sessionId: string, sourceId: string, data: any) => {
    console.log('[V4 Compat] addSourceToSessionV4 called - use V5 API instead');
    // Stub - should use V5 addResourceLink  
    const position = data.position || { x: 100, y: 100 };
    await get().addResourceLink(sessionId, {
      resource_type: 'source',
      resource_id: sourceId,
      metadata: { x: position.x, y: position.y },
    });
  },

  // Actions
  setDemoData: (data: { containers: ContainerVisualState[]; nodes: CustomNode[]; registry: Record<string, unknown> }) => {
    set({
      containers: data.containers,
      nodes: data.nodes,
      containerRegistry: data.registry as Record<string, { container: Container | null; resources: ResourceLink[]; timestamp: number }>,
      userSessionId: 'demo-root'
    });
  },

  loadContainer: async (containerId: string | null, type: ContainerType = 'session', forceRefresh = false) => {
    // DEMO MODE
    if (isDemoMode()) {
      console.log(`🎮 Demo Mode: loadContainer(${containerId || 'root'})`);
      if (!containerId) {
        set({
          activeContainerId: null,
          activeContainerType: null,
          userSessionId: 'demo-user-session', // Fix: Set dummy user session ID for root context
          breadcrumbs: [{ id: 'root', title: 'Workspace', type: 'session' }]
        });
      } else {
        const currentBreadcrumbs = get().breadcrumbs;
        const allContainers = get().containers;
        const nodes = get().nodes;
        
        const container = allContainers.find(c => c.id === containerId);
        const node = nodes.find(n => n.id === containerId);
        const containerTitle = container?.title || (node?.data as any)?.label || (node?.data as any)?.title || containerId;
        
        const existingIndex = currentBreadcrumbs.findIndex(b => b.id === containerId);
        let newBreadcrumbs;
        
        if (existingIndex >= 0) {
          newBreadcrumbs = currentBreadcrumbs.slice(0, existingIndex + 1);
        } else {
          newBreadcrumbs = [
            ...currentBreadcrumbs,
            { id: containerId, title: containerTitle, type: 'session' }
          ];
        }

        set({
          activeContainerId: containerId,
          activeContainerType: 'session',
          breadcrumbs: newBreadcrumbs,
        });
      }
      return;
    }

    // BACKEND MODE
    // 1. Root (UserSession)
    if (!containerId) {
      let userId = localStorage.getItem('user_id');
      if (!userId) {
        // Try decode token
        const token = localStorage.getItem('auth_token');
        if (token) {
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            userId = payload.sub || payload.email || payload.user_id;
            if (userId) localStorage.setItem('user_id', userId);
          } catch (e) { console.warn('Token decode failed', e); }
        }
      }
      
      if (!userId) {
        console.error('No user_id found');
        return;
      }
      
      try {
        const workspace = await api.getWorkspace();
        const resources = workspace.resources;
        
        set((state) => ({ 
          userSessionId: workspace.usersession.instance_id,
          activeContainerId: null,
          activeContainerType: null,
          breadcrumbs: [{ id: 'root', title: 'Workspace', type: 'session' }],
          nodes: resources.map(r => api.resourceLinkToNode(r) as CustomNode),
          // Populate registry for the root UserSession so drag → update works
          containerRegistry: {
            ...state.containerRegistry,
            [workspace.usersession.instance_id]: {
              container: workspace.usersession,
              resources,
              timestamp: Date.now(),
            },
          },
        }));
        
        // Start SSE
        // Note: We need to access startEventSubscription from somewhere, 
        // but it's not in this slice. We'll assume it's available on the store 
        // or we implement it here. 
        // Actually, handleContainerEvent is here, but the subscription starter 
        // was in workspace-store. We should probably move subscription logic here too.
        // For now, let's assume the component calls it or we add it to this slice.
      } catch (error) {
        console.error('Failed to load user session:', error);
      }
      return;
    }

    // 2. Container (L1+)
    try {
      const detectedType = getContainerTypeFromId(containerId);
      let containerTitle = containerId;
      const containerType: ContainerType = detectedType || type || 'session';
      
      // Registry Check
      const registry = get().containerRegistry;
      const cached = registry[containerId];
      const CACHE_TTL = 5 * 60 * 1000;
      
      let resources: ResourceLink[] = [];
      let containerData: any = null;
      let usedCache = false;

      if (!forceRefresh && cached && (Date.now() - cached.timestamp < CACHE_TTL)) {
        console.log(`✅ Using cached data for ${containerId}`);
        resources = cached.resources;
        containerData = cached.container;
        if (containerType === 'session') {
          containerTitle = containerData?.metadata?.title || containerTitle;
        } else {
          containerTitle = containerData?.title || containerTitle;
        }
        usedCache = true;
      }

      if (!usedCache) {
        // Fetch fresh
        const actualResourceId = containerId; // Simplified for V5
        
        if (containerType === 'session') {
          try {
            const session = await api.getSession(actualResourceId);
            containerTitle = session.metadata?.title || containerTitle;
            containerData = session;
          } catch (e) { console.warn('Fetch session failed', e); }
        } else if (['agent', 'tool', 'source'].includes(containerType)) {
          try {
            const container = await api.getContainer(containerType, actualResourceId);
            containerTitle = (container as any).title || containerTitle;
            containerData = container;
          } catch (e) { console.warn(`Fetch ${containerType} failed`, e); }
        }
      }

      // Update Breadcrumbs
      const currentBreadcrumbs = get().breadcrumbs;
      const existingIndex = currentBreadcrumbs.findIndex(b => b.id === containerId);
      let newBreadcrumbs;
      
      if (existingIndex >= 0) {
        newBreadcrumbs = currentBreadcrumbs.slice(0, existingIndex + 1);
      } else {
        newBreadcrumbs = [
          ...currentBreadcrumbs,
          { id: containerId, title: containerTitle, type: containerType }
        ];
      }

      set({
        activeContainerId: containerId,
        activeContainerType: containerType as ContainerType,
        breadcrumbs: newBreadcrumbs,
      });

      if (!usedCache) {
        try {
          if (containerType === 'session') {
            resources = await api.listContainerResources('session', containerId);
          } else if (isContainerDiveable(containerType)) {
            resources = await api.listContainerResources(containerType, containerId);
          }
          
          set(state => ({
            containerRegistry: {
              ...state.containerRegistry,
              [containerId]: {
                container: containerData,
                resources: resources,
                timestamp: Date.now()
              }
            }
          }));
        } catch (error) {
          console.error(`Failed to load resources for ${containerId}:`, error);
          resources = [];
        }
      }
      
      set({ 
        nodes: resources.map(r => api.resourceLinkToNode(r) as CustomNode)
      });

    } catch (error) {
      console.error(`Failed to load container ${containerId}:`, error);
    }
  },

  loadUserSession: async (_userId: string) => {
    // Implemented as part of loadContainer(null) logic above
    // But kept for explicit calls
    get().loadContainer(null, 'session');
  },

  setActiveContainer: (id: string) => {
    // Just a wrapper for loadContainer
    get().loadContainer(id, 'session');
  },

  createContainer: async (type: ContainerType, parentId: string, data: { title: string; description?: string; position?: { x: number; y: number } }) => {
    const mode = import.meta.env.VITE_MODE || 'unknown';
    
    if (mode === 'demo') {
      const newId = `${type}_${Date.now()}`;
      const newNode = {
        id: newId,
        type,
        position: data.position || { x: 100, y: 100 },
        data: { ...data, id: newId }
      };
      set(state => ({ nodes: [...state.nodes, newNode as any] }));
      return newId;
    }

    try {
      // V5 API Call
      // Note: This depends on what we are creating. 
      // If creating a session inside a session -> createSession
      // If adding a resource -> addContainerResource
      // This method seems to mix "Creating a Container Entity" and "Adding it to parent"
      
      // For V5, we usually "Add Resource" which might create a container implicitly or link an existing one.
      // But if we are creating a NEW session:
      if (type === 'session') {
        const session = await api.createSession(parentId, {
          title: data.title,
          session_type: 'interactive',
          description: data.description,
          tags: [],
          ttl_hours: 24
        });
        return session.session_id;
      }
      
      // For other types, we usually add them as resources.
      // This might need refinement based on specific UI actions.
      return '';
    } catch (error) {
      console.error('Create container failed:', error);
      throw error;
    }
  },

  createChildSession: async (
    parentId: string,
    title: string,
    position: { x: number; y: number },
    description?: string
  ) => {
    const state = get();
    
    // Enforce tier depth before creating
    const guard = enforceTierDepth(state, { isTerminal: false });
    if (!guard.ok) {
      throw new Error(`Tier depth guard blocked createChildSession: ${guard.reason}`);
    }
    
    try {
      // V5 API: Create session under parent
      const session = await api.createSession(parentId, {
        title,
        session_type: 'interactive',
        description: description || '',
        tags: [],
        ttl_hours: 24
      });
      
      // Add node to canvas
      const newNode = {
        id: session.session_id,
        type: 'session' as const,
        position,
        data: {
          id: session.session_id,
          label: title,
          title,
          description: description || '',
          type: 'session',
          metadata: {}
        }
      };
      
      // P2-CACHE-001 FIX: Invalidate parent's cache so next load fetches fresh data
      set(s => {
        const updatedRegistry = { ...s.containerRegistry };
        
        // Delete parent's cache entry to force refresh on next access
        if (parentId && updatedRegistry[parentId]) {
          delete updatedRegistry[parentId];
          console.log(`🔄 Invalidated cache for parent ${parentId}`);
        }
        
        // Also invalidate root workspace cache if parent is UserSession
        if (parentId?.startsWith('usersession_')) {
          // UserSession resources will be stale
          console.log(`🔄 UserSession cache will refresh on next workspace load`);
        }
        
        return { 
          nodes: [...s.nodes, newNode as any],
          containerRegistry: updatedRegistry
        };
      });
      
      toast.success(`Session "${title}" created`);
      return session.session_id;
    } catch (error) {
      console.error('createChildSession failed:', error);
      toast.error('Failed to create session');
      throw error;
    }
  },

  updateContainer: async (id: string, updates: Partial<Container>) => {
    // P2-EDIT-001 FIX: Persist updates to Firestore, not just local state
    try {
      const containerType = getContainerTypeFromId(id) || 'session';
      
      // 1. Call backend to persist
      if (containerType === 'session') {
        // For sessions, updates might include metadata like title
        await api.updateSession(id, updates as any);
        console.log(`✅ Session ${id} updated in Firestore`);
      } else {
        await api.updateContainer(containerType, id, updates);
        console.log(`✅ Container ${id} updated in Firestore`);
      }
      
      // 2. Update local cache/registry
      set(state => {
        const registry = { ...state.containerRegistry };
        if (registry[id]) {
          registry[id].container = { ...registry[id].container, ...updates } as any;
          registry[id].timestamp = Date.now(); // Refresh cache timestamp
        }
        
        // Also update nodes if title changed
        const nodes = state.nodes.map(node => {
          if (node.id === id && (updates as any).title) {
            return {
              ...node,
              data: {
                ...node.data,
                label: (updates as any).title,
                title: (updates as any).title
              }
            };
          }
          return node;
        });
        
        return { containerRegistry: registry, nodes };
      });
      
      toast.success('Changes saved');
    } catch (error) {
      console.error('updateContainer failed:', error);
      toast.error('Failed to save changes');
      throw error;
    }
  },

  deleteContainer: async (id: string) => {
    // Optimistic delete
    set(state => ({
      nodes: state.nodes.filter(n => n.id !== id),
      // Also remove from registry
      containerRegistry: Object.fromEntries(
        Object.entries(state.containerRegistry).filter(([key]) => key !== id)
      )
    }));
    
    // Backend call
    try {
      const type = getContainerTypeFromId(id) || 'session';
      if (type === 'session') {
        await api.deleteSession(id);
      } else {
        await api.deleteContainer(type, id);
      }
      console.log(`✅ Container ${id} deleted from Firestore`);
    } catch (error) {
      console.error('Failed to delete container:', error);
      toast.error('Failed to delete container');
      // TODO: Revert optimistic delete if needed
    }
  },

  addResourceLink: async (containerId: string, resource: Partial<ResourceLink>) => {
    try {
      // V5 API: Add resource link
      const linkId = await api.addContainerResource(
        getContainerTypeFromId(containerId) || 'session',
        containerId,
        {
          resource_type: resource.resource_type || 'agent',
          resource_id: resource.resource_id || '',
          instance_id: resource.instance_id,
          role: resource.role || 'user',
          description: resource.description || '',
          enabled: true,
          preset_params: resource.preset_params || {},
          input_mappings: resource.input_mappings || {},
          metadata: resource.metadata || {}
        }
      );
      
      // Add node to canvas
      const newNode = api.resourceLinkToNode({
        ...resource,
        link_id: linkId,
        enabled: true,
        preset_params: resource.preset_params || {},
        input_mappings: resource.input_mappings || {},
        metadata: resource.metadata || {}
      } as ResourceLink);
      
      set(s => {
        const updatedRegistry = { ...s.containerRegistry };
        
        // Invalidate cache for this container
        if (updatedRegistry[containerId]) {
          delete updatedRegistry[containerId];
          console.log(`🔄 Invalidated cache for ${containerId}`);
        }
        
        return { 
          nodes: [...s.nodes, newNode as any],
          containerRegistry: updatedRegistry
        };
      });
      
      toast.success('Resource added');
      return linkId;
    } catch (error) {
      console.error('addResourceLink failed:', error);
      toast.error('Failed to add resource');
      throw error;
    }
  },

  updateResourceLink: async (containerId: string, linkId: string, updates: Partial<ResourceLink>) => {
    const type = get().activeContainerType || 'session';
    await api.updateContainerResource(type, containerId, linkId, updates);
  },

  removeResourceLink: async (containerId: string, linkId: string) => {
    const type = get().activeContainerType || 'session';
    await api.removeContainerResource(type, containerId, linkId);
  },

  // ==========================================================================
  // Library (Orphan Containers)
  // ==========================================================================
  
  loadOrphans: async (type: ContainerType): Promise<Container[]> => {
    try {
      // Fetch all containers of this type
      const containers = await api.listContainers(type);
      
      // Filter to orphans (parent_id === null)
      const orphans = containers.filter((c: any) => c.parent_id === null);
      
      // Add orphans to registry for UI access
      set((state) => {
        const registry = { ...state.containerRegistry };
        for (const orphan of orphans) {
          // Only add if not already in registry (don't overwrite fresher data)
          if (!registry[orphan.instance_id]) {
            registry[orphan.instance_id] = {
              container: orphan,
              resources: [],
              timestamp: Date.now()
            };
          }
        }
        return { containerRegistry: registry };
      });
      
      console.log(`📚 Library: Loaded ${orphans.length} orphan ${type}(s)`);
      return orphans;
    } catch (error) {
      console.error(`Failed to load orphan ${type}s:`, error);
      return [];
    }
  },

  handleContainerEvent: (event: any) => {
    const state = get();
    const isRoot = !state.activeContainerId;
    const isCurrentContainer = state.activeContainerId === event.container_id;
    
    // Helper to update Registry (Cache)
    const updateRegistry = (updater: (entry: typeof state.containerRegistry[string]) => typeof state.containerRegistry[string]) => {
      const registry = { ...state.containerRegistry };
      const entry = registry[event.container_id];
      if (entry) {
        registry[event.container_id] = updater(entry);
        return registry;
      }
      return null;
    };

    switch (event.action) {
      case 'resource_added': {
        const resource = event.data?.resource as ResourceLink;
        if (!resource) return;

        // 1. Update Active View
        if (isCurrentContainer || (isRoot && event.container_type === 'usersession')) {
          const newNode = api.resourceLinkToNode(resource) as CustomNode;
          set({ nodes: [...state.nodes, newNode] });
        }

        // 2. Update Registry Cache
        const newRegistry = updateRegistry((entry) => ({
          ...entry,
          resources: [...entry.resources, resource]
        }));
        if (newRegistry) set({ containerRegistry: newRegistry });
        
        break;
      }

      case 'resource_removed': {
        const linkId = event.data?.link_id as string;
        if (!linkId) return;

        // 1. Update Active View
        if (isCurrentContainer || (isRoot && event.container_type === 'usersession')) {
          set({ nodes: state.nodes.filter(n => n.id !== linkId) });
        }

        // 2. Update Registry Cache
        const newRegistry = updateRegistry((entry) => ({
          ...entry,
          resources: entry.resources.filter(r => (r.link_id || r.resource_id) !== linkId)
        }));
        if (newRegistry) set({ containerRegistry: newRegistry });

        break;
      }

      case 'updated': {
        const linkId = event.data?.link_id as string;
        const updates = event.data?.updates || event.data as Partial<ResourceLink>;
        const currentUserId = localStorage.getItem('user_id');

        // CASE 1: ResourceLink update (has link_id) - visual sync
        if (linkId && updates) {
          // Resource Update
          if (isCurrentContainer || (isRoot && event.container_type === 'usersession')) {
             // We need to find the resource to update the node correctly
             set(s => ({
               nodes: s.nodes.map(n => {
                 if (n.id === linkId) {
                   // Merge updates into data
                   const newMetadata = { ...(n.data.metadata as any), ...updates.metadata };
                   
                   // Handle Position Sync
                   let newPosition = n.position;
                   if (updates.metadata && (typeof updates.metadata.x === 'number' || typeof updates.metadata.y === 'number')) {
                     newPosition = {
                       x: typeof updates.metadata.x === 'number' ? updates.metadata.x : n.position.x,
                       y: typeof updates.metadata.y === 'number' ? updates.metadata.y : n.position.y
                     };
                   }

                   return {
                     ...n,
                     position: newPosition,
                     data: { ...n.data, ...updates, metadata: newMetadata } as CustomNodeData
                   };
                 }
                 return n;
               })
             }));

             // Toast for external updates
             if (event.user_id && event.user_id !== currentUserId) {
               // Only toast if position changed or significant update
               if (updates.metadata && (updates.metadata.x !== undefined || updates.metadata.y !== undefined)) {
                  const node = state.nodes.find(n => n.id === linkId);
                  const title = node?.data?.title || 'Item';
                  toast.info(`${title} moved by another user`);
               }
             }
          }

          // Update Registry resources
          const newRegistry = updateRegistry((entry) => ({
            ...entry,
            resources: entry.resources.map(r => (r.link_id || r.resource_id) === linkId ? { ...r, ...updates } : r)
          }));
          if (newRegistry) set({ containerRegistry: newRegistry });
        }
        
        // CASE 2: Container instance update (no link_id) - parent_id change = orphan/adopt
        if (!linkId && event.container_id) {
          const containerUpdates = event.data as { parent_id?: string | null; depth?: number; [key: string]: unknown };
          
          set(s => {
            const registry = { ...s.containerRegistry };
            const entry = registry[event.container_id];
            
            if (entry?.container) {
              // Update container's parent_id/depth (tracks orphan state for Library)
              registry[event.container_id] = {
                ...entry,
                container: { ...entry.container, ...containerUpdates }
              };
              return { containerRegistry: registry };
            }
            
            // Container not in registry yet - add it if we have enough data
            if (containerUpdates.parent_id !== undefined) {
              registry[event.container_id] = {
                container: { 
                  instance_id: event.container_id,
                  parent_id: containerUpdates.parent_id,
                  depth: containerUpdates.depth || 1,
                  ...containerUpdates
                } as any,
                resources: [],
                timestamp: Date.now()
              };
              return { containerRegistry: registry };
            }
            
            return {};
          });
        }
        break;
      }
      
      case 'acl_changed': {
        const newAcl = event.data?.acl as { owner: string; editors: string[]; viewers: string[] };
        const containerId = event.container_id;
        const userId = localStorage.getItem('user_id');
        
        if (newAcl && userId) {
            const hasAccess = newAcl.owner === userId || 
                              newAcl.editors.includes(userId) || 
                              newAcl.viewers.includes(userId);
            
            if (!hasAccess) {
              // LOST ACCESS
              if (state.activeContainerId === containerId) {
                  toast.error('Access revoked');
                  get().loadContainer(null, 'usersession'); 
              }
              
              const registry = { ...state.containerRegistry };
              if (registry[containerId]) {
                delete registry[containerId];
                set({ containerRegistry: registry });
              }
              
              set({ nodes: state.nodes.filter(n => n.id !== containerId) });
            } else {
              // GAINED ACCESS
              if (event.user_id !== userId) {
                  const title = (event.data as any).title || containerId;
                  toast.info(`Access granted to ${title}`);
              }
            }
        }
        break;
      }
    }
  }
});

