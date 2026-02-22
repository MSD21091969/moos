import React, { useState } from "react";
import { useAppStore } from "../stores/appStore";
import AgentSeat from "./AgentSeat";
import type { AppNodeTree, ContextRole, DiscoveredTool, SessionResponse } from "~/types";

const AGENT_RUNNER_URL = "http://localhost:8004";

const ROLES: { value: ContextRole; label: string }[] = [
  { value: "app_user", label: "App User" },
  { value: "app_admin", label: "App Admin" },
  { value: "collider_admin", label: "Collider Admin" },
  { value: "superadmin", label: "Super Admin" },
];

// --- Sub-components (internal) ---

interface NodeCheckboxTreeProps {
  nodes: AppNodeTree[];
  depth?: number;
}

function NodeCheckboxTree({ nodes, depth = 0 }: NodeCheckboxTreeProps) {
  const { selectedNodeIds, toggleNodeSelection } = useAppStore();

  return (
    <ul className={depth === 0 ? "" : "ml-3"}>
      {nodes.map((node) => {
        const label = node.path.split("/").pop() || node.path;
        const checked = selectedNodeIds.includes(node.id);
        return (
          <li key={node.id}>
            <label className="flex items-center gap-1.5 py-0.5 cursor-pointer hover:text-gray-200">
              <input
                type="checkbox"
                checked={checked}
                onChange={() => toggleNodeSelection(node.id)}
                className="accent-blue-500"
              />
              <span className="text-xs truncate max-w-[160px]" title={node.path}>
                {label}
              </span>
            </label>
            {node.children.length > 0 && (
              <NodeCheckboxTree nodes={node.children} depth={depth + 1} />
            )}
          </li>
        );
      })}
    </ul>
  );
}

interface VectorSearchInputProps {
  onResults: (tools: DiscoveredTool[]) => void;
  role: ContextRole;
}

function VectorSearchInput({ onResults, role }: VectorSearchInputProps) {
  const { vectorQuery, setVectorQuery } = useAppStore();
  const [searching, setSearching] = useState(false);

  async function handleSearch() {
    if (!vectorQuery.trim()) return;
    setSearching(true);
    try {
      const params = new URLSearchParams({ query: vectorQuery.trim(), role });
      const resp = await fetch(`${AGENT_RUNNER_URL}/tools/discover?${params}`);
      if (resp.ok) {
        const data = (await resp.json()) as Array<{
          function?: { name?: string; description?: string };
          origin_node_id?: string;
        }>;
        const tools: DiscoveredTool[] = data.map((d) => ({
          name: d.function?.name ?? "",
          description: d.function?.description ?? "",
          score: 0,
          origin_node_id: d.origin_node_id ?? "",
        }));
        onResults(tools);
      }
    } catch {
      // silently ignore if agent runner is offline
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="flex gap-1">
      <input
        type="text"
        value={vectorQuery}
        onChange={(e) => setVectorQuery(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        placeholder="describe your task to discover tools…"
        className="flex-1 bg-gray-800 text-xs text-gray-100 rounded px-2 py-1 outline-none placeholder-gray-600"
      />
      <button
        type="button"
        onClick={handleSearch}
        disabled={searching || !vectorQuery.trim()}
        className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 disabled:opacity-40"
      >
        {searching ? "…" : "🔍"}
      </button>
    </div>
  );
}

// --- Main WorkspaceBrowser ---

export default function WorkspaceBrowser() {
  const {
    selectedAppId,
    applications,
    tree,
    selectedNodeIds,
    contextRole,
    vectorQuery,
    discoveredTools,
    sessionId,
    nanoClawWsUrl,
    composerOpen,
    inheritAncestors,
    setContextRole,
    setDiscoveredTools,
    setSessionId,
    setNanoClawWsUrl,
    setComposerOpen,
    setInheritAncestors,
  } = useAppStore();

  const [composing, setComposing] = useState(false);
  const [composeError, setComposeError] = useState<string | null>(null);

  const selectedApp = applications.find((a) => a.id === selectedAppId);

  async function handleCompose() {
    if (!selectedAppId || selectedNodeIds.length === 0) return;
    setComposing(true);
    setComposeError(null);
    try {
      const resp = await fetch(`${AGENT_RUNNER_URL}/agent/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: contextRole,
          app_id: selectedAppId,
          node_ids: selectedNodeIds,
          vector_query: vectorQuery.trim() || null,
          visibility_filter: ["global", "group"],
          inherit_ancestors: inheritAncestors,
        }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        setComposeError((err as { detail?: string }).detail ?? "Compose failed");
        return;
      }
      const data = (await resp.json()) as SessionResponse;
      setSessionId(data.session_id);
      setNanoClawWsUrl(data.nanoclaw_ws_url ?? null);
      setComposerOpen(false);
    } catch {
      setComposeError("Agent Runner unavailable — is it running on :8004?");
    } finally {
      setComposing(false);
    }
  }

  const canCompose = selectedAppId !== null && selectedNodeIds.length > 0;

  return (
    <div className="flex flex-col h-full">
      {/* Context Composer (collapsible) */}
      <div className="border-b border-gray-700">
        {/* Composer header / toggle */}
        <button
          type="button"
          onClick={() => setComposerOpen(!composerOpen)}
          className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-gray-300 hover:bg-gray-800"
        >
          <span>
            {composerOpen ? "▼" : "▶"} Context Composer
          </span>
          {sessionId && !composerOpen && (
            <span className="text-green-400">● Session active</span>
          )}
        </button>

        {composerOpen && (
          <div className="px-3 pb-3 space-y-2">
            {/* Role selector */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">Role</label>
              <select
                value={contextRole}
                onChange={(e) => setContextRole(e.target.value as ContextRole)}
                className="w-full bg-gray-800 text-xs text-gray-100 rounded px-2 py-1 outline-none"
                aria-label="Context role"
              >
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Node multi-select */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                Nodes
                {selectedNodeIds.length > 0 && (
                  <span className="ml-1 text-blue-400">({selectedNodeIds.length} selected)</span>
                )}
              </label>
              {tree.length > 0 ? (
                <div className="bg-gray-800 rounded px-2 py-1 max-h-28 overflow-y-auto text-gray-300">
                  <NodeCheckboxTree nodes={tree} />
                </div>
              ) : (
                <p className="text-xs text-gray-600">Select an application to see nodes.</p>
              )}
            </div>

            {/* Ancestor context toggle */}
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={inheritAncestors}
                onChange={(e) => setInheritAncestors(e.target.checked)}
                className="accent-blue-500"
              />
              <span className="text-xs text-gray-400">Include parent context</span>
            </label>

            {/* Vector search */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">Discover tools</label>
              <VectorSearchInput
                onResults={(tools) => setDiscoveredTools(tools)}
                role={contextRole}
              />
              {discoveredTools.length > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  {discoveredTools.length} tools matched — included in session
                </p>
              )}
            </div>

            {/* Compose error */}
            {composeError && (
              <p className="text-xs text-red-400">{composeError}</p>
            )}

            {/* Compose button */}
            <button
              type="button"
              onClick={handleCompose}
              disabled={composing || !canCompose}
              className="w-full text-xs py-1.5 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-40 font-medium"
            >
              {composing
                ? "Composing…"
                : sessionId
                  ? "Recompose Session"
                  : `Compose & Start Session →`}
            </button>
            {!canCompose && !composing && (
              <p className="text-xs text-gray-600 text-center">
                {!selectedAppId ? "Select an application first." : "Select at least one node."}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-hidden">
        <AgentSeat sessionId={sessionId} nanoClawWsUrl={nanoClawWsUrl} />
      </div>
    </div>
  );
}
