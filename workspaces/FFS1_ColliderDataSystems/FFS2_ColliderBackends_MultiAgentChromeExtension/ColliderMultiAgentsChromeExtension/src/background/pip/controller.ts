/**
 * PiP Controller - Manages Document Picture-in-Picture lifecycle
 * 
 * This controller handles:
 * - Opening Document PiP windows
 * - Rendering React content into PiP
 * - Style injection and messaging between windows
 */

let pipWindow: Window | null = null

export interface PiPOptions {
  width?: number
  height?: number
  disallowReturnToOpener?: boolean
}

export interface PiPMessage {
  type: "chat" | "action" | "close"
  payload?: unknown
}

type MessageCallback = (message: PiPMessage) => void
const messageCallbacks: Set<MessageCallback> = new Set()

/**
 * Subscribe to PiP messages
 */
export function onPiPMessage(callback: MessageCallback): () => void {
  messageCallbacks.add(callback)
  return () => messageCallbacks.delete(callback)
}

/**
 * Send message to PiP window
 */
export function sendToPiP(message: PiPMessage): void {
  if (pipWindow) {
    pipWindow.postMessage({ source: "collider-main", ...message }, "*")
  }
}

/**
 * Open the PiP window
 */
export async function openPiP(options: PiPOptions = {}): Promise<boolean> {
  // Check if Document PiP is supported
  if (!("documentPictureInPicture" in window)) {
    console.warn("[PiP] Document Picture-in-Picture not supported")
    return false
  }

  try {
    // @ts-ignore - Document PiP API types not yet in TS
    pipWindow = await window.documentPictureInPicture.requestWindow({
      width: options.width || 400,
      height: options.height || 600,
      disallowReturnToOpener: options.disallowReturnToOpener ?? true,
    })

    if (!pipWindow) {
      throw new Error("Failed to create PiP window")
    }

    // Copy styles to PiP window
    copyStyles(pipWindow)

    // Inject PiP content
    injectPiPContent(pipWindow)

    // Setup message listener
    pipWindow.addEventListener("message", (event) => {
      if (event.data?.source === "collider-pip") {
        const message = event.data as PiPMessage
        messageCallbacks.forEach((cb) => cb(message))
      }
    })

    // Listen for close
    pipWindow.addEventListener("pagehide", () => {
      pipWindow = null
      notifyPiPClosed()
    })

    return true
  } catch (error) {
    console.error("[PiP] Failed to open:", error)
    return false
  }
}

/**
 * Close the PiP window
 */
export function closePiP(): void {
  if (pipWindow) {
    pipWindow.close()
    pipWindow = null
  }
}

/**
 * Check if PiP is open
 */
export function isPiPOpen(): boolean {
  return pipWindow !== null
}

/**
 * Get the PiP window reference
 */
export function getPiPWindow(): Window | null {
  return pipWindow
}

/**
 * Copy styles from main document to PiP window
 */
function copyStyles(targetWindow: Window): void {
  // Copy stylesheets
  const styleSheets = document.querySelectorAll('link[rel="stylesheet"], style')
  styleSheets.forEach((sheet) => {
    const clone = sheet.cloneNode(true)
    targetWindow.document.head.appendChild(clone)
  })

  // Add base styles
  const baseStyles = targetWindow.document.createElement("style")
  baseStyles.textContent = `
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { 
      height: 100%; 
      overflow: hidden;
      font-family: system-ui, -apple-system, sans-serif;
    }
    body {
      background: #0f0f23;
      color: #e2e8f0;
    }
    #pip-root {
      height: 100%;
      display: flex;
      flex-direction: column;
    }
  `
  targetWindow.document.head.appendChild(baseStyles)
}

/**
 * Inject PiP React content
 */
function injectPiPContent(targetWindow: Window): void {
  // Create root element
  const root = targetWindow.document.createElement("div")
  root.id = "pip-root"
  targetWindow.document.body.appendChild(root)

  // Inject enhanced HTML with message list
  root.innerHTML = `
    <div class="pip-container">
      <div class="pip-header">
        <div class="pip-header-left">
          <span class="pip-logo">⚡</span>
          <span class="pip-title">Collider Pilot</span>
        </div>
        <div class="pip-header-right">
          <span class="pip-status connected"></span>
          <button class="pip-minimize" title="Minimize">−</button>
          <button class="pip-close" title="Close">×</button>
        </div>
      </div>
      <div class="pip-messages" id="pip-messages">
        <div class="pip-empty-state">
          <span>🤖</span>
          <p>Your AI Pilot is ready</p>
          <p class="hint">Type a message to get started</p>
        </div>
      </div>
      <div class="pip-input-container">
        <textarea id="pip-input" placeholder="Ask anything..." rows="1"></textarea>
        <button id="pip-send">➤</button>
      </div>
    </div>
  `

  // Add enhanced styles
  const styles = targetWindow.document.createElement("style")
  styles.textContent = `
    .pip-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: #0f0f23;
      color: #e2e8f0;
      font-family: system-ui, -apple-system, sans-serif;
    }
    .pip-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      border-bottom: 1px solid #1e293b;
      background: linear-gradient(180deg, #1a1a2e, #0f0f23);
    }
    .pip-header-left {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .pip-logo { font-size: 18px; }
    .pip-title { font-weight: 600; font-size: 15px; }
    .pip-header-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .pip-status {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #f87171;
    }
    .pip-status.connected { background: #4ade80; }
    .pip-minimize, .pip-close {
      width: 24px;
      height: 24px;
      border: none;
      border-radius: 4px;
      background: #1e293b;
      color: #e2e8f0;
      cursor: pointer;
      font-size: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .pip-minimize:hover, .pip-close:hover {
      background: #334155;
    }
    .pip-close:hover {
      background: #dc2626;
    }
    .pip-messages {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .pip-empty-state {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      opacity: 0.7;
    }
    .pip-empty-state span { font-size: 48px; margin-bottom: 12px; }
    .pip-empty-state p { font-size: 15px; margin-bottom: 4px; }
    .pip-empty-state .hint { font-size: 13px; opacity: 0.6; }
    .pip-message {
      padding: 10px 14px;
      border-radius: 12px;
      max-width: 85%;
      line-height: 1.4;
      font-size: 14px;
      white-space: pre-wrap;
    }
    .pip-message.user {
      align-self: flex-end;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      color: #fff;
    }
    .pip-message.assistant {
      align-self: flex-start;
      background: #1e293b;
    }
    .pip-message.streaming::after {
      content: '▌';
      animation: blink 0.7s infinite;
    }
    @keyframes blink {
      0%, 50% { opacity: 1; }
      51%, 100% { opacity: 0; }
    }
    .pip-input-container {
      display: flex;
      gap: 8px;
      padding: 12px;
      border-top: 1px solid #1e293b;
    }
    #pip-input {
      flex: 1;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid #334155;
      background: #1e293b;
      color: #e2e8f0;
      font-size: 14px;
      resize: none;
      outline: none;
      font-family: inherit;
    }
    #pip-input:focus {
      border-color: #6366f1;
    }
    #pip-send {
      padding: 10px 16px;
      border-radius: 8px;
      border: none;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      color: #fff;
      font-size: 16px;
      cursor: pointer;
    }
    #pip-send:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `
  targetWindow.document.head.appendChild(styles)

  // Get elements
  const messagesContainer = root.querySelector("#pip-messages") as HTMLElement
  const input = root.querySelector("#pip-input") as HTMLTextAreaElement
  const sendButton = root.querySelector("#pip-send") as HTMLButtonElement
  const closeButton = root.querySelector(".pip-close") as HTMLButtonElement
  const minimizeButton = root.querySelector(".pip-minimize") as HTMLButtonElement

  // Clear empty state when first message is added
  let hasMessages = false

  // Function to add message to UI
  const addMessage = (role: "user" | "assistant", content: string, streaming = false) => {
    if (!hasMessages) {
      messagesContainer.innerHTML = ""
      hasMessages = true
    }

    const msgEl = targetWindow.document.createElement("div")
    msgEl.className = `pip-message ${role}${streaming ? " streaming" : ""}`
    msgEl.textContent = content
    msgEl.dataset.msgId = Date.now().toString()
    messagesContainer.appendChild(msgEl)
    messagesContainer.scrollTop = messagesContainer.scrollHeight
    return msgEl
  }

  // Function to update streaming message
  const updateStreamingMessage = (content: string) => {
    const streamingMsg = messagesContainer.querySelector(".pip-message.streaming")
    if (streamingMsg) {
      streamingMsg.textContent = content
      messagesContainer.scrollTop = messagesContainer.scrollHeight
    }
  }

  // Function to finalize streaming
  const finalizeStreaming = () => {
    const streamingMsg = messagesContainer.querySelector(".pip-message.streaming")
    if (streamingMsg) {
      streamingMsg.classList.remove("streaming")
    }
  }

  // Handle send
  const handleSend = () => {
    const message = input.value.trim()
    if (!message) return

    addMessage("user", message)
    input.value = ""

    // Start assistant message with streaming indicator
    addMessage("assistant", "", true)

    sendPiPMessage(message)
  }

  // Event listeners
  sendButton.addEventListener("click", handleSend)
  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  })
  closeButton.addEventListener("click", () => {
    closePiP()
  })
  minimizeButton.addEventListener("click", () => {
    // Document PiP doesn't support minimize, but we can make it smaller
    console.log("[PiP] Minimize requested")
  })

  // Listen for streaming tokens from main window
  targetWindow.addEventListener("message", (event) => {
    if (event.data?.source === "collider-main") {
      switch (event.data.type) {
        case "token":
          updateStreamingMessage(event.data.payload.content)
          break
        case "done":
          finalizeStreaming()
          break
        case "error":
          finalizeStreaming()
          addMessage("assistant", `Error: ${event.data.payload.message}`)
          break
      }
    }
  })
}

/**
 * Send message from PiP to Service Worker
 */
function sendPiPMessage(message: string): void {
  chrome.runtime.sendMessage({
    type: "PIP_CHAT",
    payload: { message },
  })
}

/**
 * Notify Service Worker that PiP closed
 */
function notifyPiPClosed(): void {
  chrome.runtime.sendMessage({
    type: "PIP_CLOSED",
  })
}
