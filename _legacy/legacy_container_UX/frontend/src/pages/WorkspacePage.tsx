import { motion } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import ChatAgent from '../components/ChatAgent';
import { UI_STYLES } from '../lib/ui-styles';
import GameCanvas from '../components/GameCanvas';
import { NodeHighlightOverlay } from '../components/NodeHighlightOverlay';
import { SessionEditModal } from '../components/SessionEditModal';
import { StagingQueuePanel } from '../components/StagingQueuePanel';
import { createDemoSessions } from '../lib/demo-data';
import { useWorkspaceStore } from '../lib/workspace-store';
// import { MicrosoftLoginButton } from '../components/MicrosoftLoginButton';
import { getContainerTypeFromId } from '../lib/api';
import { isDemoMode } from '../lib/env';

export default function WorkspacePage() {
  const { containerId } = useParams();
  const {
    containers,
    nodes,
    setNodes,
    createContainer,
    editingSessionId,
    setEditingSessionId,
    loadContainer,
    breadcrumbs,
    setInitialized,
  } = useWorkspaceStore();
  const navigate = useNavigate();
  const [chatOpen, setChatOpen] = useState(false);
  const hasInitialized = useRef(false);

  // V5 Navigation Sync
  useEffect(() => {
    if (containerId) {
      const type = getContainerTypeFromId(containerId) || 'session';
      loadContainer(containerId, type);
    } else {
      // Root view (User Session)
      // TODO: Get actual user ID from auth
      loadContainer(null, 'usersession');
    }
  }, [containerId, loadContainer]);

  useEffect(() => {
    // Only run once on mount
    if (typeof window === 'undefined') return;
    
    if (hasInitialized.current) return;
    hasInitialized.current = true;
    setInitialized(true);

    // Clear localStorage if we detect OLD nested data structure (data.data)
    const hasNestedStructure = nodes.some((node) => {
      if (node.type === 'tool' || node.type === 'agent' || node.type === 'object') {
        const nodeData = node.data as any;
        return nodeData?.data !== undefined; // Has nested data.data (old structure)
      }
      return false;
    });

    if (hasNestedStructure) {
      localStorage.removeItem('workspace-storage');
      window.location.reload();
      return;
    }

    // Try to load sessions from backend first
    const initSessions = async () => {
      const hasToken = !!(localStorage.getItem('auth_token') || import.meta.env.VITE_API_TOKEN);
      
      // DEMO MODE: Always use localStorage, never call backend
      if (isDemoMode()) {
        
        // Check if we have persisted data
        let persistedNodesCount = 0;
        try {
          const raw = localStorage.getItem('workspace-storage');
          if (raw) {
            const parsed = JSON.parse(raw);
            const st = parsed.state || parsed;
            persistedNodesCount = Array.isArray(st?.nodes) ? st.nodes.length : 0;
          }
        } catch (e) {
          // ignore
        }

        // Load demo data only if localStorage is empty
        const skipDemo = localStorage.getItem('skip_demo_data') === 'true';
        if (!skipDemo && persistedNodesCount === 0 && containers.length === 0 && nodes.length === 0) {
          const demo = createDemoSessions();
          // Manually inject demo containers since createContainer is async/complex
          // For demo, we might need a simpler way or just set state directly if possible
          // But createContainer is available.
          // Actually demo.containers are SessionVisualState objects.
          // createContainer expects (type, parentId, data).
          // We might need to adapt demo data loading.
          // For now, let's assume setNodes handles the visual part and we just need to populate containers state.
          // But containers state is derived or managed by container-slice.
          // We can't directly set containers.
          // We might need a 'loadDemoData' action in the store or just iterate and create.
          
          // For now, I'll skip explicit container creation in demo mode if setNodes is enough for visuals,
          // but V5 relies on containers for navigation.
          // I'll leave this as a TODO for demo data adaptation.
          // setNodes(demo.nodes);
          (useWorkspaceStore.getState() as any).setDemoData(demo);
        }
        return;
      }

      // STAGING/PRODUCTION MODE: Use backend
      
      // Check for explicit force sync flag
      // const forceCloudSync =
      //   localStorage.getItem('collider_force_cloud_sync') === 'true' ||
      //   new URLSearchParams(location.search).get('sync') === '1';

      // Check persisted localStorage
      let persistedNodesCount = 0;
      try {
        const raw = localStorage.getItem('workspace-storage');
        if (raw) {
          const parsed = JSON.parse(raw);
          const st = parsed.state || parsed;
          persistedNodesCount = Array.isArray(st?.nodes) ? st.nodes.length : 0;
        }
        } catch (e) {
          // ignore
        }      // If we have auth token, try backend first (unless we have local data and not forcing sync)
      if (hasToken) {
        return;
      } else {
        console.warn('⚠️  No auth token in staging/production mode. Backend sync skipped.');
      }

      // Fallback to localStorage if we have data
      if (persistedNodesCount > 0) {
        // Using cached data
      } else {
        console.warn('⚠️  No data available. Set auth_token and reload to sync from backend.');
      }
    };

    initSessions();
  }, [containers.length, nodes.length, createContainer, setNodes, loadContainer]);

  return (
    <div className="relative w-screen h-screen bg-slate-950">
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-10 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center justify-between px-4 py-2">
          {/* Left: Title + Breadcrumbs */}
          <div className="flex items-center gap-4">
            <Link 
              to="/workspace" 
              className="text-xl font-bold text-white hover:text-blue-400 transition-colors"
              title="My Tiny Data Collider"
            >
              my-tiny-data-collider
            </Link>
            
            {/* Breadcrumbs UI - only show when inside a container */}
            {breadcrumbs.length > 0 && (
              <nav aria-label="breadcrumb" className="flex items-center text-sm text-slate-400">
                {breadcrumbs.map((crumb, index) => (
                  crumb.id !== 'root' && (
                    <div key={crumb.id} className="flex items-center">
                      <ChevronRight className="w-4 h-4 mx-1 text-slate-600" />
                      {index === breadcrumbs.length - 1 ? (
                        <span className="text-white font-medium" data-testid="breadcrumb-current">
                          {crumb.title}
                        </span>
                      ) : (
                        <Link 
                          to={`/workspace/${crumb.id}`}
                          className="hover:text-white transition-colors"
                          data-testid="breadcrumb-link"
                        >
                          {crumb.title}
                        </Link>
                      )}
                    </div>
                  )
                ))}
              </nav>
            )}
          </div>

          {/* Right: Menu Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                if (confirm('Reset all local data? This cannot be undone.')) {
                  localStorage.clear();
                  window.location.reload();
                }
              }}
              className="text-sm text-red-400 hover:text-red-300 transition-colors mr-2"
              title="Reset Demo Data"
            >
              Reset Data
            </button>
            <button
              onClick={() => setChatOpen(!chatOpen)}
              className="text-base font-bold text-white hover:text-blue-400 transition-colors"
              title="Menu"
            >
              Menu
            </button>
          </div>
        </div>
      </header>

      {/* Chat Panel - Top Right Corner */}
      {chatOpen && (
        <motion.div
          drag
          dragMomentum={false}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          onClick={(e) => e.stopPropagation()}
          className={`fixed top-[60px] right-[5px] w-96 h-[500px] ${UI_STYLES.panel.full} flex flex-col z-[9999] cursor-move`}
        >
          <ChatAgent />
        </motion.div>
      )}

      {/* Main Canvas - Workspace View (Sessions + Their Children Only) */}
      <div
        className="absolute top-[49px] left-0 right-0 bottom-0"
      >
        <GameCanvas 
          key="workspace-canvas" 
          workspaceView={true} 
          onNodeDoubleClick={(_event, node) => {
            // Navigate into container types (session, agent, tool)
            // Terminal nodes (source, user) cannot be navigated into
            const isContainer = node.type === 'session' || node.type === 'agent' || node.type === 'tool';
            if (isContainer) {
              navigate(`/workspace/${node.id}`);
            }
          }}
        />
        <NodeHighlightOverlay />
      </div>

      {/* Staging Queue Panel */}
      <StagingQueuePanel />

      {/* Global Session Edit Modal */}
      {editingSessionId && (
        <SessionEditModal
          sessionId={editingSessionId}
          isOpen={true}
          onClose={() => setEditingSessionId(null)}
        />
      )}
    </div>
  );
}

