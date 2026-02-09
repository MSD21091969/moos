import { contextManager } from "./context-manager";
import { initCloudAgent } from "./agents/cloud-agent";
import { handleDomQuery } from "./agents/dom-agent";
import { verifyAuth, fetchApps, fetchTree, connectSSE } from "./external/data-server";
import { searchForTools, executeWorkflow } from "./agents/cloud-agent";
import { readFile, writeFile, listDir } from "./agents/filesyst-agent";
import type { ColliderMessage, ColliderResponse } from "~/types";

// Initialize on install/startup
chrome.runtime.onInstalled.addListener(async () => {
  console.log("[Collider] Extension installed");
  await initialize();
});

chrome.runtime.onStartup.addListener(async () => {
  await initialize();
});

async function initialize(): Promise<void> {
  await contextManager.restore();

  try {
    const user = await verifyAuth();
    contextManager.setUser(user);
    console.log("[Collider] Authenticated as:", user.email);

    const apps = await fetchApps();
    contextManager.setApplications(apps);
    console.log("[Collider] Loaded", apps.length, "applications");
  } catch (error) {
    console.warn("[Collider] Init failed (servers may be offline):", error);
  }

  initCloudAgent();

  // Connect SSE for real-time updates
  try {
    connectSSE(
      (event) => {
        console.log("[Collider] SSE event:", event.type, event.data);
      },
      (error) => {
        console.warn("[Collider] SSE error:", error);
      }
    );
  } catch {
    console.warn("[Collider] SSE connection failed");
  }
}

// Track active tab
chrome.tabs.onActivated.addListener((activeInfo) => {
  contextManager.setActiveTab(activeInfo.tabId);
});

chrome.tabs.onRemoved.addListener((tabId) => {
  contextManager.removeTab(tabId);
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (changeInfo.url || changeInfo.title) {
    contextManager.updateTabContext(tabId, {
      url: changeInfo.url,
      title: changeInfo.title,
    });
  }
});

// Message router
chrome.runtime.onMessage.addListener(
  (
    message: ColliderMessage,
    _sender: chrome.runtime.MessageSender,
    sendResponse: (response: ColliderResponse) => void
  ) => {
    handleMessage(message)
      .then(sendResponse)
      .catch((error) => {
        sendResponse({
          success: false,
          error: error instanceof Error ? error.message : String(error),
        });
      });
    return true; // Keep message channel open for async response
  }
);

async function handleMessage(
  message: ColliderMessage
): Promise<ColliderResponse> {
  switch (message.type) {
    case "AUTH_VERIFY": {
      const user = await verifyAuth();
      contextManager.setUser(user);
      return { success: true, data: user };
    }

    case "FETCH_APPS": {
      const apps = await fetchApps();
      contextManager.setApplications(apps);
      return { success: true, data: apps };
    }

    case "FETCH_TREE": {
      const appId = (message.payload as Record<string, string>)?.app_id;
      if (!appId) return { success: false, error: "Missing app_id" };
      const tree = await fetchTree(appId);
      return { success: true, data: tree };
    }

    case "DOM_QUERY": {
      const tabId = message.tabId ?? contextManager.activeTab?.tabId;
      if (!tabId) return { success: false, error: "No active tab" };
      const selector = (message.payload as Record<string, string>)?.selector ?? "*";
      return handleDomQuery(tabId, selector);
    }

    case "WORKFLOW_EXECUTE": {
      const payload = message.payload as {
        workflow_id: string;
        steps: string[];
      };
      return executeWorkflow(payload.workflow_id, payload.steps);
    }

    case "TOOL_SEARCH": {
      const query = (message.payload as Record<string, string>)?.query ?? "";
      return searchForTools(query);
    }

    case "NATIVE_MESSAGE": {
      const nPayload = message.payload as {
        action: string;
        path?: string;
        content?: string;
      };
      switch (nPayload.action) {
        case "read_file":
          return readFile(nPayload.path ?? "");
        case "write_file":
          return writeFile(nPayload.path ?? "", nPayload.content ?? "");
        case "list_dir":
          return listDir(nPayload.path ?? "");
        default:
          return { success: false, error: `Unknown native action: ${nPayload.action}` };
      }
    }

    case "CONTEXT_UPDATE":
      return {
        success: true,
        data: contextManager.getSerializableContext(),
      };

    default:
      return { success: false, error: `Unknown message type: ${message.type}` };
  }
}

export { };
