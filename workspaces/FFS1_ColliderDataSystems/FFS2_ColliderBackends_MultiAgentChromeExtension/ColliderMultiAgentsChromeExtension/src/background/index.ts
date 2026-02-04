/**
 * Service Worker - Main Entry Point
 * Orchestrates Context Manager, agents, and external communication
 */

import { ContextManager } from "./context/manager"
import { processMessage } from "./agents/router"
import { verifyAuth, listApps, getNode, connectSSE } from "./external/data"
import { graphToolClient } from "./external/graphtool"

// Initialize on SW start
ContextManager.init().then(() => {
  console.log("🚀 Collider Service Worker started")
})

// Listen for messages from UI
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  handleMessage(message, sender).then(sendResponse)
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
    case "LOGIN": {
      const { token } = message.payload as { token: string }
      try {
        const auth = await verifyAuth(token)
        await ContextManager.setMain({
          user: {
            id: auth.user.id,
            email: auth.user.email,
            profile: auth.user.profile,
          },
          permissions: auth.permissions,
          secrets: (auth.user.container as { secrets?: Record<string, string> }).secrets || {},
        })
        
        // Load apps
        const apps = await listApps()
        await ContextManager.setMain({ apps })
        
        return { success: true, user: auth.user }
      } catch (err) {
        return { success: false, error: String(err) }
      }
    }

    case "GET_CONTEXT": {
      return ContextManager.getMergedContext(tabKey)
    }

    case "NAVIGATE": {
      const { appId, path } = message.payload as { appId: string; path: string }
      try {
        const node = await getNode(appId, path)
        await ContextManager.setTab(tabKey, {
          app: `cloud://${appId}`,
          node: path,
          domain: "CLOUD",
          container: node.container,
          threadId: `thread_${tabKey}`,
          messages: [],
        })
        return { success: true, node }
      } catch (err) {
        return { success: false, error: String(err) }
      }
    }

    case "CHAT": {
      const { text } = message.payload as { text: string }
      try {
        const response = await processMessage(tabKey, text)
        return { success: true, response }
      } catch (err) {
        return { success: false, error: String(err) }
      }
    }

    case "GET_APPS": {
      const main = ContextManager.getMain()
      return { apps: main.apps }
    }

    case "GET_USER": {
      const main = ContextManager.getMain()
      return { user: main.user }
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

export {}
