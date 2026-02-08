/**
 * Runtime Diagnostics for Browser Console
 * Use in F12 console to inspect frontend state, API calls, and authentication
 *
 * Usage in Edge F12 Console:
 *   window.__diagnostics.status()        // Show full diagnostic report
 *   window.__diagnostics.showToken()     // Show auth token
 *   window.__diagnostics.showStore()     // Show Zustand store state
 *   window.__diagnostics.showAPI()       // Show API configuration
 *   window.__diagnostics.testAPI()       // Test backend connectivity
 */

import { SessionVisualState } from './types';
import { useWorkspaceStore } from './workspace-store';

export interface DiagnosticsAPI {
  status: () => void;
  showToken: () => void;
  showStore: () => void;
  showAPI: () => void;
  testAPI: () => Promise<void>;
  showLocalStorage: () => void;
  clearAuthToken: () => void;
  setAuthToken: (token: string) => void;
  createTestSessions: (count: number) => Promise<void>;
}

/**
 * Initialize runtime diagnostics (call once at app startup)
 */
export function initializeDiagnostics(getStoreState: () => any) {
  const diagnostics: DiagnosticsAPI = {
    /**
     * Show complete diagnostic report
     */
    status: () => {
      console.clear();
      console.log('🔍 === MY TINY DATA COLLIDER - RUNTIME DIAGNOSTICS ===');
      console.log('');

      diagnostics.showAPI();
      console.log('');

      diagnostics.showToken();
      console.log('');

      diagnostics.showStore();
      console.log('');

      diagnostics.showLocalStorage();
      console.log('');

      console.log('📋 Available Commands:');
      console.log('  window.__diagnostics.status()       - Full report');
      console.log('  window.__diagnostics.showToken()    - Auth token status');
      console.log('  window.__diagnostics.showStore()    - Zustand store state');
      console.log('  window.__diagnostics.showAPI()      - API configuration');
      console.log('  window.__diagnostics.testAPI()      - Test backend');
      console.log('  window.__diagnostics.showLocalStorage() - Storage contents');
      console.log('  window.__diagnostics.setAuthToken(token) - Set new token');
      console.log('  window.__diagnostics.clearAuthToken() - Clear token');
      console.log('  window.__diagnostics.testSessionOps() - Test session operations');
      console.log('  window.__diagnostics.createTestSessions(n) - Create N test sessions');
      console.log('  window.__diagnostics.showStubCalls() - View stub API calls');
      console.log('  window.__diagnostics.clearStubLogs() - Clear stub logs');
    },

    /**
     * Show authentication token status
     */
    showToken: () => {
      const token = localStorage.getItem('auth_token') || import.meta.env.VITE_API_TOKEN;
      const envToken = import.meta.env.VITE_API_TOKEN;

      console.log('🔑 AUTHENTICATION STATUS:');
      console.log(`  localStorage.auth_token: ${token ? '✅ SET' : '❌ MISSING'}`);
      if (token) {
        console.log(`    Length: ${token.length} chars`);
        console.log(`    Preview: ${token.substring(0, 20)}...`);
      }
      console.log(`  VITE_API_TOKEN env: ${envToken ? '✅ SET' : '❌ MISSING'}`);
      console.log(`  Overall Status: ${token ? '✅ READY' : '❌ NOT CONFIGURED'}`);
    },

    /**
     * Show Zustand store state
     */
    showStore: () => {
      const state = getStoreState();

      console.log('🗂️  ZUSTAND STORE STATE:');
      console.log(`  Nodes: ${state.nodes?.length || 0}`);
      state.nodes?.slice(0, 3).forEach((n: any, i: number) => {
        console.log(`    [${i}] ${n.id} (type: ${n.type}) @ (${n.position?.x}, ${n.position?.y})`);
      });
      if (state.nodes?.length > 3) {
        console.log(`    ... and ${state.nodes.length - 3} more`);
      }

      console.log(`  Containers: ${state.containers?.length || 0}`);
      state.containers?.slice(0, 3).forEach((c: any, i: number) => {
        console.log(`    [${i}] ${c.id}: "${c.title}" (type: ${c.containerType}, status: ${c.status})`);
      });
      if (state.containers?.length > 3) {
        console.log(`    ... and ${state.containers.length - 3} more`);
      }

      console.log(`  Edges: ${state.edges?.length || 0}`);
      console.log(
        `  Viewport: zoom=${state.viewport?.zoom}, x=${state.viewport?.x}, y=${state.viewport?.y}`
      );
      console.log(`  Staged Operations: ${state.stagedOperations?.length || 0}`);

      // Show if data is from backend or demo
      const hasBackendContainers = state.containers?.some((c: any) => c.id?.startsWith('session_'));
      const hasDemoContainers = state.containers?.some((c: any) => c.title?.includes('Santorini'));

      console.log('  Data Source:', {
        backend: hasBackendContainers ? '✅ YES' : '❌ NO',
        demo: hasDemoContainers ? '✅ YES' : '❌ NO',
      });
    },

    /**
     * Show API configuration
     */
    showAPI: () => {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const dev = import.meta.env.DEV;

      console.log('🌐 API CONFIGURATION:');
      console.log(`  API URL: ${apiUrl}`);
      console.log(`  Environment: ${dev ? 'DEVELOPMENT' : 'PRODUCTION'}`);
      console.log(`  Mode: ${import.meta.env.MODE}`);
    },

    /**
     * Test backend connectivity
     */
    testAPI: async () => {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('auth_token') || import.meta.env.VITE_API_TOKEN;

      console.log('🧪 TESTING BACKEND CONNECTIVITY:');
      console.log('');

      // Test 1: Health check (no auth needed)
      try {
        console.log('  [1/3] Health check...');
        const healthResponse = await fetch(`${apiUrl}/health`, {
          signal: AbortSignal.timeout(5000),
        });
        console.log(`    ✅ Status: ${healthResponse.status}`);
        const health = await healthResponse.json();
        console.log(`    Service: ${health.service}`);
        console.log(`    Version: ${health.version}`);
      } catch (error) {
        console.log(`    ❌ Failed: ${error instanceof Error ? error.message : error}`);
      }
      console.log('');

      // Test 2: Sessions endpoint (requires auth)
      try {
        console.log('  [2/3] Sessions endpoint (with auth)...');
        if (!token) {
          console.log('    ⚠️  No auth token - request will fail');
        }
        const sessionsResponse = await fetch(`${apiUrl}/sessions`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: AbortSignal.timeout(5000),
        });
        console.log(`    ✅ Status: ${sessionsResponse.status}`);
        const sessions = await sessionsResponse.json();
        console.log(`    Total sessions: ${sessions.total || sessions.sessions?.length || 0}`);
        if (sessionsResponse.status === 401) {
          console.log('    ⚠️  Unauthorized - check your auth token');
        }
      } catch (error) {
        console.log(`    ❌ Failed: ${error instanceof Error ? error.message : error}`);
      }
      console.log('');

      // Test 3: User info (requires auth)
      try {
        console.log('  [3/3] User info endpoint...');
        const userResponse = await fetch(`${apiUrl}/user/info`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: AbortSignal.timeout(5000),
        });
        console.log(`    ✅ Status: ${userResponse.status}`);
        const user = await userResponse.json();
        console.log(`    User ID: ${user.user_id}`);
        console.log(`    Tier: ${user.tier}`);
        console.log(`    Quota: ${user.quota_remaining}`);
      } catch (error) {
        console.log(`    ❌ Failed: ${error instanceof Error ? error.message : error}`);
      }
      console.log('');
      console.log('  ✅ API testing complete');
    },

    /**
     * Show localStorage contents
     */
    showLocalStorage: () => {
      console.log('📦 LOCALSTORAGE CONTENTS:');
      const keys = Object.keys(localStorage);
      console.log(`  Total keys: ${keys.length}`);

      keys.forEach((key) => {
        const value = localStorage.getItem(key);
        const size = value ? (value.length / 1024).toFixed(2) : '0';
        console.log(`  ${key}: ${size} KB`);
      });

      // Show workspace-storage size breakdown
      const workspaceStorage = localStorage.getItem('workspace-storage');
      if (workspaceStorage) {
        try {
          const parsed = JSON.parse(workspaceStorage);
          console.log('');
          console.log('  📋 workspace-storage breakdown:');
          console.log(`    nodes: ${parsed.state?.nodes?.length || 0} items`);
          console.log(`    edges: ${parsed.state?.edges?.length || 0} items`);
          console.log(`    containers: ${parsed.state?.containers?.length || 0} items`);
        } catch (e) {
          console.log('    ⚠️  Could not parse workspace-storage');
        }
      }
    },

    /**
     * Clear auth token
     */
    clearAuthToken: () => {
      localStorage.removeItem('auth_token');
      console.log('🗑️  Cleared auth token from localStorage');
    },

    /**
     * Set auth token
     */
    setAuthToken: (token: string) => {
      localStorage.setItem('auth_token', token);
      console.log('✅ Auth token set to localStorage');
      console.log(`   Length: ${token.length} chars`);
      console.log(`   Preview: ${token.substring(0, 20)}...`);
    },

    /**
     * Create test sessions with varied data
     */
    createTestSessions: async (count: number = 5) => {
      // const store = useWorkspaceStore.getState();

      const sessionTypes: SessionVisualState['sessionType'][] = ['chat', 'analysis', 'workflow'];
      const statuses: SessionVisualState['status'][] = ['active', 'completed', 'expired', 'archived'];
      const tagSets = [
        ['test', 'demo'],
        ['analysis', 'data'],
        ['workflow', 'automation'],
        ['chat', 'conversation'],
        ['experimental', 'prototype'],
      ];

      console.log(`🔧 Creating ${count} test sessions with varied data...`);

      for (let i = 0; i < count; i++) {
        const x = Math.floor(Math.random() * 800) + 100;
        const y = Math.floor(Math.random() * 600) + 100;

        const sessionId = `test_sess_${Date.now()}_${i}`;
        const sessionType = sessionTypes[i % sessionTypes.length];
        const status = statuses[i % statuses.length];
        const tags = tagSets[i % tagSets.length];

        const newSession: SessionVisualState = {
          id: sessionId,
          title: `Test Session ${i + 1}`,
          position: { x, y },
          size: { width: 280, height: 180 },
          themeColor: '#60a5fa',
          status: status as SessionVisualState['status'],
          expanded: true,
          zoneId: 'diagnostics',
          containerType: 'session',
          description: `Test session ${i + 1} (${sessionType})`,
          sessionType,
          tags,
          createdAt: new Date(Date.now() - i * 3600000).toISOString(),
          updatedAt: new Date().toISOString(),
        };

        useWorkspaceStore.setState((state) => ({
          nodes: [...state.nodes, {
            id: sessionId,
            type: 'session',
            position: { x, y },
            data: newSession as SessionVisualState & Record<string, unknown>,
          }],
          containers: [...state.containers, newSession]
        }));

        // In rare cases Zustand actions may silently no-op (e.g., before persistence rehydration).
        // Ensure the session exists by manually patching state when addSession didn't stick.
        const hasContainer = useWorkspaceStore
          .getState()
          .containers.some((container) => container.id === sessionId);
        if (!hasContainer) {
          useWorkspaceStore.setState((state) => ({
            containers: [...state.containers.filter((container) => container.id !== sessionId), newSession],
          }));
        }

        console.log(`  ✅ Created Test Session ${i + 1} (${sessionType}, ${status})`);
      }

      console.log(`🎉 Created ${count} test sessions!`);
    },


  };

  // Attach to window for console access
  (window as any).__diagnostics = diagnostics;

  // Auto-show message
  console.log('💡 Runtime diagnostics initialized');
  console.log('   Type: window.__diagnostics.status() for full report');

  return diagnostics;
}
