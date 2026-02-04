/**
 * Sidepanel - Graph Browser + Chat UI
 */

import React, { useState, useEffect } from "react"

interface User {
  id: string
  email: string
  profile: { display_name?: string }
}

interface App {
  id: string
  app_id: string
  display_name: string
}

interface Message {
  role: "user" | "assistant"
  content: string
}

export default function Sidepanel() {
  const [user, setUser] = useState<User | null>(null)
  const [apps, setApps] = useState<App[]>([])
  const [selectedApp, setSelectedApp] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Load user and apps on mount
    chrome.runtime.sendMessage({ type: "GET_USER" }).then((res) => {
      if (res?.user) setUser(res.user)
    })

    chrome.runtime.sendMessage({ type: "GET_APPS" }).then((res) => {
      if (res?.apps) setApps(res.apps)
    })
  }, [])

  const handleLogin = async () => {
    // MVP: Use test email as token
    const token = "superuser@test.com"
    const res = await chrome.runtime.sendMessage({
      type: "LOGIN",
      payload: { token },
    })
    if (res?.success) {
      setUser(res.user)
      // Refresh apps
      const appsRes = await chrome.runtime.sendMessage({ type: "GET_APPS" })
      if (appsRes?.apps) setApps(appsRes.apps)
    }
  }

  const handleAppSelect = async (appId: string) => {
    setSelectedApp(appId)
    await chrome.runtime.sendMessage({
      type: "NAVIGATE",
      payload: { appId, path: "/" },
    })
  }

  const handleSend = async () => {
    if (!input.trim()) return

    const userMsg: Message = { role: "user", content: input }
    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setLoading(true)

    try {
      const res = await chrome.runtime.sendMessage({
        type: "CHAT",
        payload: { text: input },
      })
      const assistantMsg: Message = {
        role: "assistant",
        content: res?.response || res?.error || "No response",
      }
      setMessages((prev) => [...prev, assistantMsg])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>⚡ Collider</h1>
        {user ? (
          <span style={styles.user}>{user.profile?.display_name || user.email}</span>
        ) : (
          <button onClick={handleLogin} style={styles.loginBtn}>
            Login
          </button>
        )}
      </header>

      {user && (
        <div style={styles.appList}>
          <h3 style={styles.sectionTitle}>Applications</h3>
          {apps.length === 0 ? (
            <p style={styles.empty}>No apps available</p>
          ) : (
            apps.map((app) => (
              <button
                key={app.id}
                onClick={() => handleAppSelect(app.app_id)}
                style={{
                  ...styles.appBtn,
                  background: selectedApp === app.app_id ? "#4f46e5" : "#374151",
                }}
              >
                {app.display_name || app.app_id}
              </button>
            ))
          )}
        </div>
      )}

      <div style={styles.chat}>
        <div style={styles.messages}>
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                ...styles.message,
                alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                background: msg.role === "user" ? "#4f46e5" : "#374151",
              }}
            >
              {msg.content}
            </div>
          ))}
          {loading && <div style={styles.loading}>...</div>}
        </div>

        <div style={styles.inputRow}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask anything..."
            style={styles.input}
          />
          <button onClick={handleSend} style={styles.sendBtn}>
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    background: "#1f2937",
    color: "#f9fafb",
    fontFamily: "system-ui, sans-serif",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 16px",
    borderBottom: "1px solid #374151",
  },
  title: {
    margin: 0,
    fontSize: "18px",
  },
  user: {
    fontSize: "14px",
    color: "#9ca3af",
  },
  loginBtn: {
    background: "#4f46e5",
    color: "white",
    border: "none",
    padding: "8px 16px",
    borderRadius: "6px",
    cursor: "pointer",
  },
  appList: {
    padding: "12px 16px",
    borderBottom: "1px solid #374151",
  },
  sectionTitle: {
    margin: "0 0 8px 0",
    fontSize: "14px",
    color: "#9ca3af",
  },
  appBtn: {
    display: "block",
    width: "100%",
    padding: "8px 12px",
    marginBottom: "4px",
    background: "#374151",
    color: "white",
    border: "none",
    borderRadius: "4px",
    textAlign: "left",
    cursor: "pointer",
  },
  empty: {
    color: "#6b7280",
    fontSize: "14px",
  },
  chat: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    padding: "12px 16px",
  },
  messages: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    overflowY: "auto",
  },
  message: {
    padding: "8px 12px",
    borderRadius: "8px",
    maxWidth: "80%",
    fontSize: "14px",
  },
  loading: {
    color: "#9ca3af",
    fontSize: "14px",
  },
  inputRow: {
    display: "flex",
    gap: "8px",
    marginTop: "12px",
  },
  input: {
    flex: 1,
    padding: "10px 12px",
    background: "#374151",
    border: "1px solid #4b5563",
    borderRadius: "6px",
    color: "white",
    fontSize: "14px",
  },
  sendBtn: {
    background: "#4f46e5",
    color: "white",
    border: "none",
    padding: "10px 20px",
    borderRadius: "6px",
    cursor: "pointer",
  },
}
