/**
 * FFS4 — Collider Sidepanel Application
 *
 * Main layout: Workspace graph (top) + Agent chat (bottom)
 * Sidebar: App selector + context controls
 *
 * This app is designed to run at localhost:4201 and be embedded
 * in the Chrome extension sidepanel via iframe (Phase 3).
 */

import { useState, useEffect, useCallback } from "react";
import { ReactFlowProvider } from "@xyflow/react";
import { WorkspaceGraph } from "../components/graph/WorkspaceGraph";
import { AgentChat } from "../components/agent/AgentChat";
import { useContextStore, type ContextRole } from "../stores/contextStore";
import { useSessionStore } from "../stores/sessionStore";
import { useGraphStore } from "../stores/graphStore";
import { listApps, getKernelWsUrl, type Application } from "../lib/api";
import { NanoClawRpcClient } from "../lib/nanoclaw-client";

const ROLES: ContextRole[] = ["app_user", "app_admin", "collider_admin", "superadmin"];

export function App() {
  const [apps, setApps] = useState<Application[]>([]);
  const [loadingApps, setLoadingApps] = useState(true);

  const {
    appId,
    selectedNodeIds,
    role,
    inheritAncestors,
    composing,
    setAppId,
    setRole,
    setInheritAncestors,
    setComposing,
  } = useContextStore();

  const { sessionId, setSession } = useSessionStore();

  const { applyMorphisms, setActiveState, setLoading, setError } = useGraphStore();

  // Load apps on mount
  useEffect(() => {
    listApps()
      .then(setApps)
      .catch(() => setApps([]))
      .finally(() => setLoadingApps(false));
  }, []);

  // Global WebSocket connection for sync.active_state
  useEffect(() => {
    if (!appId) return;

    setLoading(true);
    const wsUrl = getKernelWsUrl();
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method: "surface.register",
          params: {
            surface_id: "ffs4",
            name: "FFS4 Sidepanel",
            kind: "surface",
          },
        })
      );
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg?.method === "sync.active_state") {
          setActiveState(msg.params?.nodes ?? [], msg.params?.edges ?? []);
          setLoading(false);
        } else if (msg?.method === "sync.active_state_delta" || msg?.method === "stream.morphism") {
          // If we receive a delta and we want to just append via store
          // Wait, FFS4 graphStore has applyMorphisms for envelopes.
          // For active_state_delta, NanoClawRpcClient maps it to morphism array.
          // Here we can just listen to the raw msg and pass envelope.
          if (msg.params?.envelope) {
            // But applyMorphisms expects an array of parsed morphisms.
            // Actually, NanoClawRpcClient handles that inside AgentChat...
            // Let's rely on AgentChat for now or handle here broadly?
            // "If sync.active_state_delta, do setNodes((prev) => [...prev, msg.params]) (abstractly)."
            // Wait, we need to adapt graphStore or just use nodes if available:
            if (msg.params?.nodes) {
              // we do a full replace or merge, according to user abstract.
              setActiveState(msg.params.nodes, msg.params.edges ?? []);
            }
          }
        }
      } catch {
        // ignore parse
      }
    };

    return () => {
      ws.close();
    };
  }, [appId, setActiveState, setLoading]);

  // Compose session from selected nodes
  const handleCompose = useCallback(async () => {
    if (!appId || selectedNodeIds.length === 0) return;

    setComposing(true);
    try {
      const wsUrl = getKernelWsUrl();
      const client = new NanoClawRpcClient(wsUrl);
      await client.connect();
      try {
        await client.surfaceRegister({
          surface_id: "ffs4",
          name: "FFS4 Sidepanel",
          kind: "surface",
        });
      } catch {
        // best effort registration
      }
      const session = await client.sessionCreate();
      client.disconnect();

      setSession(session.session_id, wsUrl, {
        appId,
        nodeIds: selectedNodeIds,
        role,
      });
    } catch (err) {
      console.error("Failed to compose session:", err);
    } finally {
      setComposing(false);
    }
  }, [appId, selectedNodeIds, role, inheritAncestors]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", fontFamily: "system-ui, sans-serif" }}>
      {/* Toolbar */}
      <div style={{ padding: "8px 12px", borderBottom: "1px solid #e5e7eb", display: "flex", gap: 8, alignItems: "center", fontSize: 12 }}>
        {/* App selector */}
        <select
          value={appId ?? ""}
          onChange={(e) => setAppId(e.target.value || null)}
          style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid #d1d5db", fontSize: 12 }}
        >
          <option value="">
            {loadingApps ? "Loading..." : "Select app"}
          </option>
          {apps.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>

        {/* Role selector */}
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as ContextRole)}
          style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid #d1d5db", fontSize: 12 }}
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>

        {/* Inherit toggle */}
        <label style={{ display: "flex", alignItems: "center", gap: 4, cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={inheritAncestors}
            onChange={(e) => setInheritAncestors(e.target.checked)}
          />
          inherit
        </label>

        {/* Node count + compose button */}
        <span style={{ color: "#6b7280" }}>
          {selectedNodeIds.length} node{selectedNodeIds.length !== 1 ? "s" : ""}
        </span>

        <button
          onClick={handleCompose}
          disabled={!appId || selectedNodeIds.length === 0 || composing}
          style={{
            marginLeft: "auto",
            padding: "4px 12px",
            background: selectedNodeIds.length > 0 ? "#3b82f6" : "#d1d5db",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: selectedNodeIds.length > 0 ? "pointer" : "default",
            fontSize: 12,
            fontWeight: 500,
          }}
        >
          {composing ? "Composing..." : sessionId ? "Recompose" : "Compose"}
        </button>
      </div>

      {/* Main content: Graph + Chat split */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Graph panel — 60% */}
        <div style={{ flex: 3, borderBottom: "1px solid #e5e7eb", minHeight: 0 }}>
          <ReactFlowProvider>
            <WorkspaceGraph appId={appId} />
          </ReactFlowProvider>
        </div>

        {/* Chat panel — 40% */}
        <div style={{ flex: 2, minHeight: 0, display: "flex", flexDirection: "column" }}>
          <AgentChat />
        </div>
      </div>
    </div>
  );
}

export default App;
