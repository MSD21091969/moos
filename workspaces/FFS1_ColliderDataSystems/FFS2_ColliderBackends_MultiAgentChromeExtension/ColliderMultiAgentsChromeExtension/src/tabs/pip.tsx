/**
 * DocPiP (Document Picture-in-Picture) - Agent Seat
 * Floating copilot interface that persists across tabs
 */
import { useState, useEffect, useCallback } from "react"

interface PiPState {
  isOpen: boolean
  mode: "single" | "multi"
  focuses: string[] // tab keys
  activeTabKey: string | null
}

interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  timestamp: number
}

export default function DocPiP() {
  const [pipState, setPipState] = useState<PiPState>({
    isOpen: false,
    mode: "single",
    focuses: [],
    activeTabKey: null,
  })
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isConnected, setIsConnected] = useState(false)

  // Listen for state updates from Service Worker
  useEffect(() => {
    const listener = (changes: { [key: string]: chrome.storage.StorageChange }) => {
      if (changes.pipContext) {
        setPipState(changes.pipContext.newValue)
      }
      if (changes.pipMessages) {
        setMessages(changes.pipMessages.newValue || [])
      }
      if (changes.connectionStatus) {
        setIsConnected(changes.connectionStatus.newValue)
      }
    }
    chrome.storage.session.onChanged.addListener(listener)
    
    // Load initial state
    chrome.storage.session.get(["pipContext", "pipMessages", "connectionStatus"], (result) => {
      if (result.pipContext) setPipState(result.pipContext)
      if (result.pipMessages) setMessages(result.pipMessages)
      if (result.connectionStatus) setIsConnected(result.connectionStatus)
    })

    return () => chrome.storage.session.onChanged.removeListener(listener)
  }, [])

  const sendMessage = useCallback(async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input.trim(),
      timestamp: Date.now(),
    }

    // Optimistic update
    setMessages((prev) => [...prev, userMessage])
    setInput("")

    // Send to Service Worker
    try {
      await chrome.runtime.sendMessage({
        type: "PIP_CHAT",
        payload: {
          message: userMessage.content,
          focuses: pipState.focuses,
          mode: pipState.mode,
        },
      })
    } catch (error) {
      console.error("Failed to send message:", error)
    }
  }, [input, pipState])

  const toggleMode = () => {
    const newMode = pipState.mode === "single" ? "multi" : "single"
    chrome.runtime.sendMessage({ type: "PIP_SET_MODE", payload: { mode: newMode } })
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.logo}>⚡</span>
          <span style={styles.title}>Collider Pilot</span>
        </div>
        <div style={styles.headerRight}>
          <span style={{ ...styles.status, backgroundColor: isConnected ? "#4ade80" : "#f87171" }} />
          <button onClick={toggleMode} style={styles.modeButton}>
            {pipState.mode === "multi" ? "🔗 Multi" : "📍 Single"}
          </button>
        </div>
      </div>

      {/* Focus Tabs */}
      {pipState.focuses.length > 0 && (
        <div style={styles.focusTabs}>
          {pipState.focuses.map((tabKey) => (
            <div
              key={tabKey}
              style={{
                ...styles.focusTab,
                opacity: tabKey === pipState.activeTabKey ? 1 : 0.6,
              }}
            >
              {tabKey.split("_")[1]?.slice(0, 4) || "Tab"}
            </div>
          ))}
        </div>
      )}

      {/* Messages */}
      <div style={styles.messages}>
        {messages.length === 0 ? (
          <div style={styles.emptyState}>
            <span style={styles.emptyIcon}>🤖</span>
            <p>Your AI pilot is ready</p>
            <p style={styles.emptyHint}>Type a message to get started</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                ...styles.message,
                ...(msg.role === "user" ? styles.userMessage : styles.assistantMessage),
              }}
            >
              {msg.content}
            </div>
          ))
        )}
      </div>

      {/* Input */}
      <div style={styles.inputContainer}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask anything..."
          style={styles.input}
          rows={1}
        />
        <button onClick={sendMessage} style={styles.sendButton} disabled={!input.trim()}>
          ➤
        </button>
      </div>
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
    fontSize: "14px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "8px 12px",
    borderBottom: "1px solid #1e293b",
    background: "linear-gradient(180deg, #1a1a2e 0%, #0f0f23 100%)",
  },
  headerLeft: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  logo: { fontSize: "18px" },
  title: { fontWeight: 600, fontSize: "15px" },
  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  status: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
  },
  modeButton: {
    padding: "4px 8px",
    fontSize: "12px",
    background: "#1e293b",
    border: "none",
    borderRadius: "4px",
    color: "#e2e8f0",
    cursor: "pointer",
  },
  focusTabs: {
    display: "flex",
    gap: "4px",
    padding: "8px 12px",
    borderBottom: "1px solid #1e293b",
    overflowX: "auto",
  },
  focusTab: {
    padding: "4px 8px",
    fontSize: "11px",
    background: "#1e293b",
    borderRadius: "4px",
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    padding: "12px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  emptyState: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    opacity: 0.7,
    textAlign: "center",
  },
  emptyIcon: { fontSize: "48px", marginBottom: "8px" },
  emptyHint: { fontSize: "12px", opacity: 0.6 },
  message: {
    padding: "10px 14px",
    borderRadius: "12px",
    maxWidth: "85%",
    lineHeight: 1.4,
  },
  userMessage: {
    alignSelf: "flex-end",
    background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
    color: "#fff",
  },
  assistantMessage: {
    alignSelf: "flex-start",
    background: "#1e293b",
  },
  inputContainer: {
    display: "flex",
    gap: "8px",
    padding: "12px",
    borderTop: "1px solid #1e293b",
  },
  input: {
    flex: 1,
    padding: "10px 14px",
    borderRadius: "8px",
    border: "1px solid #334155",
    background: "#1e293b",
    color: "#e2e8f0",
    fontSize: "14px",
    resize: "none",
    outline: "none",
  },
  sendButton: {
    padding: "10px 16px",
    borderRadius: "8px",
    border: "none",
    background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
    color: "#fff",
    fontSize: "16px",
    cursor: "pointer",
  },
}
