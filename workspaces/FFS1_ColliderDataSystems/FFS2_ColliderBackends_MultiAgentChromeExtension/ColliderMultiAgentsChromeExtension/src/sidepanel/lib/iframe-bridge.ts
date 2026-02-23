/**
 * Iframe Bridge — PostMessage relay between FFS4 iframe and Chrome extension
 *
 * FFS4 runs at localhost:4201 inside an iframe in the extension sidepanel.
 * This bridge relays messages between the iframe and the extension's
 * content scripts and background service worker.
 *
 * Message flow:
 *   FFS4 → postMessage → bridge → chrome.tabs.sendMessage → content script
 *   content script → chrome.runtime.sendMessage → bridge → postMessage → FFS4
 */

const FFS4_ORIGIN = "http://localhost:4201";

type IframeBridgeMessage =
  | { type: "DOM_QUERY"; selector: string; requestId: string }
  | { type: "DOM_CLICK"; selector: string; requestId: string }
  | { type: "DOM_FILL"; selector: string; value: string; requestId: string }
  | { type: "DOM_CAPTURE"; requestId: string }
  | { type: "PAGE_NAVIGATE"; url: string; requestId: string }
  | { type: "CONTEXT_READY"; sessionId: string; nodeIds: string[] }
  | { type: "TAB_CHANGED"; url: string; tabId: number };

/**
 * Start the iframe bridge. Call once when the sidepanel mounts.
 * Returns a cleanup function.
 */
export function startIframeBridge(iframeRef: React.RefObject<HTMLIFrameElement | null>): () => void {
  // Listen for messages FROM the FFS4 iframe
  const handleMessage = async (event: MessageEvent) => {
    if (event.origin !== FFS4_ORIGIN) return;
    const msg = event.data as IframeBridgeMessage;
    if (!msg?.type) return;

    switch (msg.type) {
      case "DOM_QUERY":
      case "DOM_CLICK":
      case "DOM_FILL":
      case "DOM_CAPTURE":
      case "PAGE_NAVIGATE": {
        // Forward to the active tab's content script
        try {
          const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
          if (!tab?.id) {
            replyToIframe(iframeRef, { type: "ERROR", requestId: (msg as { requestId?: string }).requestId, error: "No active tab" });
            return;
          }
          const response = await chrome.tabs.sendMessage(tab.id, {
            source: "collider-sidepanel",
            ...msg,
          });
          replyToIframe(iframeRef, { type: "RESULT", requestId: (msg as { requestId?: string }).requestId, data: response });
        } catch (err) {
          replyToIframe(iframeRef, {
            type: "ERROR",
            requestId: (msg as { requestId?: string }).requestId,
            error: err instanceof Error ? err.message : String(err),
          });
        }
        break;
      }

      case "CONTEXT_READY": {
        // Store context state in extension storage for cross-tab coordination
        await chrome.storage.session.set({
          activeSessionId: msg.sessionId,
          activeNodeIds: msg.nodeIds,
        });
        break;
      }

      default:
        break;
    }
  };

  window.addEventListener("message", handleMessage);

  // Listen for messages FROM content scripts (via background relay)
  const handleRuntimeMessage = (
    message: { source?: string; type?: string;[key: string]: unknown },
    _sender: chrome.runtime.MessageSender,
    _sendResponse: (response?: unknown) => void,
  ) => {
    if (message.source !== "collider-content-script") return;
    // Forward to the iframe
    replyToIframe(iframeRef, message);
  };

  chrome.runtime.onMessage.addListener(handleRuntimeMessage);

  // Notify FFS4 when the active tab changes
  const handleTabActivated = async (activeInfo: chrome.tabs.TabActiveInfo) => {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (tab.url) {
      replyToIframe(iframeRef, {
        type: "TAB_CHANGED",
        url: tab.url,
        tabId: activeInfo.tabId,
      });
    }
  };

  chrome.tabs.onActivated.addListener(handleTabActivated);

  // Cleanup
  return () => {
    window.removeEventListener("message", handleMessage);
    chrome.runtime.onMessage.removeListener(handleRuntimeMessage);
    chrome.tabs.onActivated.removeListener(handleTabActivated);
  };
}

function replyToIframe(
  iframeRef: React.RefObject<HTMLIFrameElement | null>,
  data: unknown,
): void {
  iframeRef.current?.contentWindow?.postMessage(data, FFS4_ORIGIN);
}
