import React, { useEffect, useState } from "react";
import { useAppStore } from "./stores/appStore";
import { AppTree } from "@collider/sidepanel-ui";
import WorkspaceBrowser from "./components/WorkspaceBrowser";
import type { Application, AppNodeTree, ColliderMessage } from "~/types";
import "~/style.css";

type ViewMode = "tree" | "agent";

function SidePanel() {
  const {
    applications,
    selectedAppId,
    tree,
    loading,
    error,
    setApplications,
    selectApp,
    selectNode,
    selectedNodePath,
    setTree,
    setLoading,
    setError,
  } = useAppStore();

  const [viewMode, setViewMode] = useState<ViewMode>("tree");

  useEffect(() => {
    loadApps();
  }, []);

  useEffect(() => {
    if (selectedAppId) {
      loadTree(selectedAppId);
    }
  }, [selectedAppId]);

  async function loadApps() {
    setLoading(true);
    setError(null);
    try {
      const response = await chrome.runtime.sendMessage({
        type: "FETCH_APPS",
      } satisfies ColliderMessage);
      if (response.success) {
        setApplications(response.data as Application[]);
      } else {
        setError(response.error ?? "Failed to load apps");
      }
    } catch (err) {
      setError("Could not connect to background service");
    } finally {
      setLoading(false);
    }
  }

  async function loadTree(appId: string) {
    setLoading(true);
    try {
      const response = await chrome.runtime.sendMessage({
        type: "FETCH_TREE",
        payload: { app_id: appId },
      } satisfies ColliderMessage);
      if (response.success) {
        setTree(response.data as AppNodeTree[]);
      }
    } catch {
      // Tree load may fail if server is offline
    } finally {
      setLoading(false);
    }
  }

  const selectedApp = applications.find((a) => a.app_id === selectedAppId);
  const domain = (selectedApp?.config as Record<string, string>)?.domain ?? "CLOUD";

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700">
        <h1 className="text-sm font-semibold">Collider</h1>
        <div className="flex gap-1">
          <button
            onClick={() => setViewMode("tree")}
            className={`text-xs px-2 py-1 rounded ${viewMode === "tree" ? "bg-gray-700" : "hover:bg-gray-800"
              }`}
          >
            Tree
          </button>
          <button
            onClick={() => setViewMode("agent")}
            className={`text-xs px-2 py-1 rounded ${viewMode === "agent" ? "bg-gray-700" : "hover:bg-gray-800"
              }`}
          >
            Agent
          </button>
        </div>
      </div>

      {/* App selector */}
      <div className="px-3 py-2 border-b border-gray-700">
        <select
          value={selectedAppId ?? ""}
          onChange={(e) => selectApp(e.target.value || null)}
          className="w-full bg-gray-800 text-sm rounded px-2 py-1 outline-none"
        >
          <option value="">Select application...</option>
          {applications.map((app) => (
            <option key={app.app_id} value={app.app_id}>
              {app.display_name ?? app.app_id}
            </option>
          ))}
        </select>
      </div>

      {/* Error display */}
      {error && (
        <div className="px-3 py-2 text-xs text-red-400 bg-red-900/20">
          {error}
        </div>
      )}

      {/* Loading indicator */}
      {loading && (
        <div className="px-3 py-2 text-xs text-gray-400">Loading...</div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {viewMode === "tree" ? (
          <div className="h-full overflow-y-auto">
            {selectedAppId ? (
              <AppTree
                tree={tree}
                domain={domain}
                onSelectNode={selectNode}
                selectedPath={selectedNodePath}
              />
            ) : (
              <div className="p-4 text-sm text-gray-500">
                Select an application to browse its nodes.
              </div>
            )}
          </div>
        ) : (
          <WorkspaceBrowser />
        )}
      </div>
    </div>
  );
}

export default SidePanel;
