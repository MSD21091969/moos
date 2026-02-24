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
import { listApps, createAgentSession, type Application } from "../lib/api";

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

  // Load apps on mount
  useEffect(() => {
    listApps()
      .then(setApps)
      .catch(() => setApps([]))
      .finally(() => setLoadingApps(false));
  }, []);

  // Compose session from selected nodes
  const handleCompose = useCallback(async () => {
    if (!appId || selectedNodeIds.length === 0) return;

    setComposing(true);
    try {
      const resp = await createAgentSession({
        role,
        app_id: appId,
        node_ids: selectedNodeIds,
        inherit_ancestors: inheritAncestors,
      });
      setSession(resp.session_id, resp.nanoclaw_ws_url, {
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
