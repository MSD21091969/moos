/**
 * Service Worker - Main Entry Point
 * Orchestrates Context Manager, agents, and external communication
 */

import { ContextManager, contextManager } from "./context/manager"
import { processMessage } from "./agents/router"
import { verifyAuth, listApps, getNode, getNodeTree, connectSSE } from "./external/data"
import { executeFilesystAction, getFilesystemTree } from "./agents/filesyst"
import { executeCloudAction, getCloudTree } from "./agents/cloud"
import { executeDOMAction } from "./agents/dom"
import * as graphtool from "./external/graphtool"

console.log("[Collider] Service Worker loading...")

// PiP state
let pipOpen = false

// SSE connection for real-time updates
let sseConnection: EventSource | null = null

function handleSSEEvent(event: { type: string; data: unknown }) {
  console.log("[SSE] Event received:", event.type, event.data)

  const data = event.data as Record<string, unknown>

  switch (event.type) {
    case "container_updated":
    case "node_modified": {
      const appId = data.app_id as string
      const nodePath = data.node_path as string
      if (appId && nodePath) {
        contextManager.invalidateCache(appId, nodePath)
        // Broadcast to UI
        chrome.storage.session.set({
          lastSSEEvent: { type: event.type, appId, nodePath, timestamp: Date.now() }
        })
      }
      break
    }
    case "permission_changed": {
      // Refetch permissions on next request
      console.log("[SSE] Permission changed, will refetch on next auth check")
      break
    }
    case "app_config_changed": {
      const appId = data.app_id as string
      if (appId) {
        contextManager.invalidateAppConfig(appId)
      }
      break
    }
    default:
      console.log("[SSE] Unhandled event type:", event.type)
  }
}

function startSSE() {
  if (sseConnection) {
    sseConnection.close()
  }
  sseConnection = connectSSE(handleSSEEvent)
  console.log("[SSE] Connection established")
}

function stopSSE() {
  if (sseConnection) {
    sseConnection.close()
    sseConnection = null
    console.log("[SSE] Connection closed")
  }
}

// Initialize on SW start
ContextManager.init()
  .then(() => {
    console.log("[Collider] Service Worker started successfully")
  })
  .catch((err) => {
    console.error("[Collider] Service Worker init failed:", err)
  })

// Listen for messages from UI
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log("[Collider] Message received:", message.type)
  handleMessage(message, sender)
    .then(sendResponse)
    .catch((err) => {
      console.error("[Collider] handleMessage error:", err)
      sendResponse({ success: false, error: String(err) })
    })
  return true // Keep channel open for async response
})

async function handleMessage(
  message: { type: string; payload?: unknown },
  sender: chrome.runtime.MessageSender
): Promise<unknown> {
  const tabKey = sender.tab
    ? `${sender.tab.windowId}_${sender.tab.id}`
    : "popup"

  switch (message.type) {
    // ========== AUTH ==========
    case "LOGIN": {
      const { token } = message.payload as { token: string }
      console.log("[Collider LOGIN] Starting login with token:", token)
      try {
        console.log("[Collider LOGIN] Calling verifyAuth...")
        const auth = await verifyAuth(token)
        console.log("[Collider LOGIN] verifyAuth success:", auth.user.email)

        await ContextManager.setMain({
          user: {
            id: auth.user.id,
            email: auth.user.email,
            profile: auth.user.profile,
          },
          permissions: auth.permissions,
          secrets: (auth.user.container as { secrets?: Record<string, string> }).secrets || {},
        })
        console.log("[Collider LOGIN] ContextManager.setMain done")

        // Load apps
        console.log("[Collider LOGIN] Loading apps...")
        const apps = await listApps()
        console.log("[Collider LOGIN] Got", apps.length, "apps")
        // Add domain info (mock for now)
        const appsWithDomain = apps.map((app) => ({
          ...app,
          domain: (app.app_id.startsWith("ffs") ? "FILESYST" : "CLOUD") as "FILESYST" | "CLOUD" | "ADMIN",
        }))
        await ContextManager.setMain({ apps: appsWithDomain as unknown[] as typeof appsWithDomain })

        // Sync to storage for UI
        console.log("[Collider LOGIN] Syncing to session storage...")
        await chrome.storage.session.set({
          mainContext: ContextManager.getMain(),
        })
        console.log("[Collider LOGIN] Session storage updated")

        // Start SSE connection for real-time updates
        startSSE()

        console.log("[Collider LOGIN] Returning success")
        return { success: true, user: auth.user }
      } catch (err) {
        console.error("[Collider LOGIN] Error:", err)
        return { success: false, error: String(err) }
      }
    }

    // ========== APP SELECTION ==========
    case "SELECT_APP": {
      const { appId } = message.payload as { appId: string }
      try {
        // Get node tree for the app
        const nodes = await getNodeTree(appId)

        // Store nodes for UI
        await chrome.storage.session.set({ currentNodes: nodes })

        // Set tab context
        const main = ContextManager.getMain()
        const app = main.apps.find((a) => a.app_id === appId)
        const domain = app?.domain || "CLOUD"

        await ContextManager.setTab(tabKey, {
          app: `${domain.toLowerCase()}://${appId}`,
          node: "/",
          domain,
          container: (nodes[0]?.container ?? null) as any,
          threadId: `thread_${tabKey}`,
          messages: [],
        })

        return { success: true, nodes }
      } catch (err) {
        return { success: false, error: String(err) }
      }
    }

    case "SELECT_NODE": {
      const { path } = message.payload as { path: string }
      const tab = await contextManager.getTabContext(tabKey)
      if (!tab) {
        return { success: false, error: "No tab context" }
      }

      try {
        const appId = tab.app.split("://")[1]
        const node = await getNode(appId, path)

        await contextManager.updateTabContext(tabKey, {
          node: path,
          container: node.container,
        })

        return { success: true, node }
      } catch (err) {
        return { success: false, error: String(err) }
      }
    }

    // ========== CONTEXT ==========
    case "GET_CONTEXT": {
      return ContextManager.getMergedContext(tabKey)
    }

    case "GET_APPS": {
      const main = ContextManager.getMain()
      return { apps: main.apps }
    }

    case "GET_USER": {
      const main = ContextManager.getMain()
      return { user: main.user }
    }

    // ========== NAVIGATION ==========
    case "NAVIGATE": {
      const { appId, path } = message.payload as { appId: string; path: string }
      try {
        const node = await getNode(appId, path)
        await ContextManager.setTab(tabKey, {
          app: `cloud://${appId}`,
          node: path,
          domain: "CLOUD",
          container: node.container as any,
          threadId: `thread_${tabKey}`,
          messages: [],
        })
        return { success: true, node }
      } catch (err) {
        return { success: false, error: String(err) }
      }
    }

    // ========== CHAT / AGENTS ==========
    case "CHAT": {
      const { text } = message.payload as { text: string }
      try {
        const response = await processMessage(tabKey, text)
        return { success: true, response }
      } catch (err) {
        return { success: false, error: String(err) }
      }
    }

    case "PIP_CHAT": {
      const { message: text, focuses } = message.payload as { message: string; focuses?: string[] }
      try {
        // Route to agent based on focused tabs
        const targetKey = focuses?.[0] || tabKey
        const response = await processMessage(targetKey, text)

        // Store response for PiP UI
        const existingMessages = await chrome.storage.session.get("pipMessages")
        const messages = existingMessages.pipMessages || []
        messages.push({
          id: crypto.randomUUID(),
          role: "user",
          content: text,
          timestamp: Date.now(),
        })
        messages.push({
          id: crypto.randomUUID(),
          role: "assistant",
          content: response || "No response from agent",
          timestamp: Date.now(),
        })
        await chrome.storage.session.set({ pipMessages: messages })

        return { success: true, response }
      } catch (err) {
        return { success: false, error: String(err) }
      }
    }

    // ========== AGENT ACTIONS ==========
    case "FILESYST_ACTION": {
      const action = message.payload as { type: string; path?: string }
      return executeFilesystAction(tabKey, action as any)
    }

    case "CLOUD_ACTION": {
      const action = message.payload as { type: string; query?: string }
      return executeCloudAction(tabKey, action as any)
    }

    case "DOM_ACTION": {
      const action = message.payload as { type: string; selector?: string }
      return executeDOMAction(tabKey, action as any)
    }

    // ========== PIP ==========
    case "OPEN_PIP": {
      pipOpen = true
      await chrome.storage.session.set({
        pipContext: { isOpen: true, mode: "single", focuses: [tabKey], activeTabKey: tabKey },
        connectionStatus: true,
      })
      // PiP window is created by the calling context (sidepanel)
      return { success: true }
    }

    case "CLOSE_PIP":
    case "PIP_CLOSED": {
      pipOpen = false
      await chrome.storage.session.set({
        pipContext: { isOpen: false, mode: "single", focuses: [], activeTabKey: null },
      })
      return { success: true }
    }

    case "PIP_SET_MODE": {
      const { mode } = message.payload as { mode: "single" | "multi" }
      const existing = await chrome.storage.session.get("pipContext")
      await chrome.storage.session.set({
        pipContext: { ...existing.pipContext, mode },
      })
      return { success: true }
    }

    // ========== CONTENT SCRIPT ==========
    case "CONTENT_SCRIPT_READY": {
      const { url, title } = message.payload as { url: string; title: string }
      console.log(`[Collider] Content script ready: ${title} (${url})`)
      return { success: true }
    }

    default:
      return { error: `Unknown message type: ${message.type}` }
  }
}

// Handle tab removal
chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
  const tabKey = `${removeInfo.windowId}_${tabId}`
  ContextManager.removeTab(tabKey)
})

// Open sidepanel when extension icon clicked
chrome.action.onClicked.addListener((tab) => {
  if (tab.id) {
    chrome.sidePanel.open({ tabId: tab.id })
  }
})

export { }

