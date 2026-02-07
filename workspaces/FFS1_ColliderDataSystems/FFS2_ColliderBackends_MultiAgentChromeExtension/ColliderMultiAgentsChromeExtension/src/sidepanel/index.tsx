/**
 * Sidepanel - Graph Browser for navigating appnode structure
 * Refactored from chat UI to navigation-focused interface
 */
import { useState, useEffect, useCallback } from "react"
import { NodeBrowser, type AppNode, type Domain } from "./components/NodeBrowser"

interface AppInfo {
  id: string
  app_id: string
  display_name: string
  domain: Domain
}

type ViewMode = "tree" | "graph" | "cabinet"

export default function Sidepanel() {
  const [user, setUser] = useState<{ email: string; profile: { display_name?: string } } | null>(null)
  const [apps, setApps] = useState<AppInfo[]>([])
  const [selectedApp, setSelectedApp] = useState<AppInfo | null>(null)
  const [nodes, setNodes] = useState<AppNode[]>([])
  const [selectedNode, setSelectedNode] = useState<AppNode | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>("tree")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Listen for state updates from Service Worker
  useEffect(() => {
    console.log("[Sidepanel] Setting up listeners...")
    const listener = (changes: { [key: string]: chrome.storage.StorageChange }) => {
      console.log("[Sidepanel] Storage changed:", Object.keys(changes))
      if (changes.mainContext) {
        const ctx = changes.mainContext.newValue
        console.log("[Sidepanel] MainContext updated:", ctx?.user?.email, "apps:", ctx?.apps?.length)
        setUser(ctx?.user || null)
        setApps(ctx?.apps || [])
      }
      if (changes.currentNodes) {
        setNodes(changes.currentNodes.newValue || [])
      }
    }
    chrome.storage.session.onChanged.addListener(listener)

    // Load initial state
    chrome.storage.session.get(["mainContext", "currentNodes"], (result) => {
      console.log("[Sidepanel] Initial state:", result)
      if (result.mainContext) {
        setUser(result.mainContext.user || null)
        setApps(result.mainContext.apps || [])
      }
      if (result.currentNodes) {
        setNodes(result.currentNodes)
      }
    })

    return () => chrome.storage.session.onChanged.removeListener(listener)
  }, [])

  const handleLogin = async () => {
    console.log("[Sidepanel] handleLogin called - setting loading state")
    setIsLoading(true)
    setError(null)
    try {
      // MVP: Use email as token (Data Server auth looks up user by email)
      console.log("[Sidepanel] Sending LOGIN message to service worker...")
      const response = await chrome.runtime.sendMessage({ type: "LOGIN", payload: { token: "superuser@test.com" } })
      console.log("[Sidepanel] Login response:", response)
      if (response && !response.success) {
        setError(response.error || "Login failed")
      }
    } catch (err) {
      console.error("[Sidepanel] Login error:", err)
      setError(String(err))
    } finally {
      setIsLoading(false)
    }
  }

  const selectApp = async (app: AppInfo) => {
    setSelectedApp(app)
    setIsLoading(true)
    try {
      await chrome.runtime.sendMessage({
        type: "SELECT_APP",
        payload: { appId: app.app_id },
      })
    } catch (err) {
      setError(String(err))
    } finally {
      setIsLoading(false)
    }
  }

  const selectNode = async (node: AppNode) => {
    setSelectedNode(node)
    await chrome.runtime.sendMessage({
      type: "SELECT_NODE",
      payload: { path: node.path },
    })
  }

  const openPiP = async () => {
    // Use popup window instead of Document PiP (which doesn't work in extension contexts)
    const pipUrl = chrome.runtime.getURL("tabs/pip.html")
    chrome.windows.create({
      url: pipUrl,
      type: "popup",
      width: 400,
      height: 600,
      focused: true,
    })
  }

  const getViewIcon = (mode: ViewMode) => {
    switch (mode) {
      case "tree": return "🌲"
      case "graph": return "🕸️"
      case "cabinet": return "🗄️"
    }
  }

  // Not logged in
  if (!user) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <span style={styles.logo}>⚡</span>
          <span style={styles.title}>Collider</span>
        </div>
        <div style={styles.loginContainer}>
          <span style={styles.loginIcon}>🔐</span>
          <p style={styles.loginText}>Sign in to access your apps</p>
          <button onClick={handleLogin} style={styles.loginButton} disabled={isLoading}>
            {isLoading ? "Signing in..." : "Login"}
          </button>
          {error && <p style={styles.error}>{error}</p>}
        </div>
      </div>
    )
  }

  // Logged in - show app list or node browser
  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.logo}>⚡</span>
          <span style={styles.title}>
            {selectedApp ? selectedApp.display_name : "Collider"}
          </span>
        </div>
        <div style={styles.headerRight}>
          <button onClick={openPiP} style={styles.pipButton} title="Open Pilot">
            🤖
          </button>
        </div>
      </div>

      {/* Breadcrumb */}
      {selectedApp && (
        <div style={styles.breadcrumb}>
          <button onClick={() => { setSelectedApp(null); setNodes([]) }} style={styles.breadcrumbButton}>
            Apps
          </button>
          <span style={styles.breadcrumbSeparator}>›</span>
          <span>{selectedApp.display_name}</span>
          {selectedNode && (
            <>
              <span style={styles.breadcrumbSeparator}>›</span>
              <span>{selectedNode.path}</span>
            </>
          )}
        </div>
      )}

      {/* View Mode Toggle */}
      {selectedApp && (
        <div style={styles.viewModes}>
          {(["tree", "graph", "cabinet"] as ViewMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              style={{
                ...styles.viewModeButton,
                ...(viewMode === mode ? styles.viewModeActive : {}),
              }}
            >
              {getViewIcon(mode)} {mode}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      <div style={styles.content}>
        {isLoading ? (
          <div style={styles.loading}>Loading...</div>
        ) : !selectedApp ? (
          // App list
          <div style={styles.appList}>
            {apps.length === 0 ? (
              <div style={styles.emptyState}>
                <p>No apps available</p>
              </div>
            ) : (
              apps.map((app) => (
                <button
                  key={app.id}
                  onClick={() => selectApp(app)}
                  style={styles.appItem}
                >
                  <span style={styles.appIcon}>
                    {app.domain === "FILESYST" ? "📁" : app.domain === "CLOUD" ? "☁️" : "⚙️"}
                  </span>
                  <div style={styles.appInfo}>
                    <span style={styles.appName}>{app.display_name || app.app_id}</span>
                    <span style={styles.appDomain}>{app.domain}</span>
                  </div>
                </button>
              ))
            )}
          </div>
        ) : (
          // Node browser
          <div style={styles.nodeTree}>
            {viewMode === "tree" && (
              <NodeBrowser
                nodes={nodes}
                domain={selectedApp.domain}
                selectedPath={selectedNode?.path}
                onSelect={selectNode}
                isLoading={isLoading}
              />
            )}
            {viewMode === "graph" && (
              <div style={styles.placeholder}>
                <span style={{ fontSize: "48px" }}>🕸️</span>
                <p>3D Force Graph coming soon</p>
              </div>
            )}
            {viewMode === "cabinet" && (
              <div style={styles.placeholder}>
                <span style={{ fontSize: "48px" }}>🗄️</span>
                <p>Filing Cabinet view coming soon</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Selected Node Details */}
      {selectedNode && (
        <div style={styles.nodeDetails}>
          <h3 style={styles.nodeTitle}>{selectedNode.path}</h3>
          <div style={styles.nodeStats}>
            <span>📝 {selectedNode.container.instructions.length} instructions</span>
            <span>🔧 {selectedNode.container.tools.length} tools</span>
            <span>📚 {selectedNode.container.knowledge.length} knowledge</span>
          </div>
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    backgroundColor: "#0f0f23",
    color: "#e2e8f0",
    fontFamily: "system-ui, -apple-system, sans-serif",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 16px",
    borderBottom: "1px solid #1e293b",
    background: "linear-gradient(180deg, #1a1a2e 0%, #0f0f23 100%)",
  },
  headerLeft: { display: "flex", alignItems: "center", gap: "8px" },
  headerRight: { display: "flex", alignItems: "center", gap: "8px" },
  logo: { fontSize: "20px" },
  title: { fontWeight: 600, fontSize: "16px" },
  pipButton: {
    padding: "6px 10px",
    fontSize: "16px",
    background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
  },
  breadcrumb: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "8px 16px",
    fontSize: "13px",
    borderBottom: "1px solid #1e293b",
  },
  breadcrumbButton: {
    background: "none",
    border: "none",
    color: "#818cf8",
    cursor: "pointer",
    padding: 0,
  },
  breadcrumbSeparator: { opacity: 0.5 },
  viewModes: {
    display: "flex",
    gap: "4px",
    padding: "8px 16px",
    borderBottom: "1px solid #1e293b",
  },
  viewModeButton: {
    padding: "6px 12px",
    fontSize: "12px",
    background: "#1e293b",
    border: "none",
    borderRadius: "4px",
    color: "#e2e8f0",
    cursor: "pointer",
    textTransform: "capitalize",
  },
  viewModeActive: {
    background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
  },
  content: { flex: 1, overflowY: "auto", padding: "12px" },
  loading: { display: "flex", justifyContent: "center", padding: "20px" },
  appList: { display: "flex", flexDirection: "column", gap: "8px" },
  appItem: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "12px",
    background: "#1e293b",
    border: "none",
    borderRadius: "8px",
    color: "#e2e8f0",
    cursor: "pointer",
    textAlign: "left",
  },
  appIcon: { fontSize: "24px" },
  appInfo: { display: "flex", flexDirection: "column" },
  appName: { fontWeight: 500 },
  appDomain: { fontSize: "12px", opacity: 0.6 },
  nodeTree: {},
  treeNode: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "8px 12px",
    background: "none",
    border: "none",
    borderRadius: "4px",
    color: "#e2e8f0",
    cursor: "pointer",
    width: "100%",
    textAlign: "left",
  },
  treeNodeSelected: { background: "#334155" },
  treeIcon: { fontSize: "14px" },
  nodeDetails: {
    padding: "12px 16px",
    borderTop: "1px solid #1e293b",
    background: "#1a1a2e",
  },
  nodeTitle: { fontSize: "14px", fontWeight: 500, marginBottom: "8px" },
  nodeStats: {
    display: "flex",
    gap: "12px",
    fontSize: "12px",
    opacity: 0.7,
  },
  placeholder: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px",
    textAlign: "center",
    opacity: 0.6,
  },
  loginContainer: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: "12px",
  },
  loginIcon: { fontSize: "48px" },
  loginText: { opacity: 0.7 },
  loginButton: {
    padding: "12px 32px",
    fontSize: "15px",
    background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
    border: "none",
    borderRadius: "8px",
    color: "#fff",
    cursor: "pointer",
    fontWeight: 500,
  },
  error: { color: "#f87171", fontSize: "13px" },
  emptyState: { textAlign: "center", padding: "20px", opacity: 0.6 },
}
