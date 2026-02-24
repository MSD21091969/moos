/**
 * AgentChat — Chat panel for agent interaction
 *
 * Ported from Chrome extension's AgentSeat.
 * Connects to NanoClawBridge via WebSocket and streams agent events.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { NanoClawRpcClient } from "../../lib/nanoclaw-client";
import { useSessionStore } from "../../stores/sessionStore";

export function AgentChat() {
  const {
    sessionId,
    wsUrl,
    sessionContext,
    connected,
    messages,
    sending,
    setConnected,
    addMessage,
    updateLastAssistant,
    finalizeLastAssistant,
    addToolMessage,
    setSending,
  } = useSessionStore();

  const [input, setInput] = useState("");
  const clientRef = useRef<NanoClawRpcClient | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Connect/disconnect WebSocket
  useEffect(() => {
    if (!wsUrl || !sessionId) {
      setConnected(false);
      return;
    }

    const client = new NanoClawRpcClient(wsUrl);
    clientRef.current = client;

    const unsubscribe = client.onAgentEvent((event) => {
      switch (event.kind) {
        case "text_delta":
          updateLastAssistant(event.text);
          break;
        case "tool_use_start":
          addToolMessage(event.name, `Calling ${event.name}...`);
          break;
        case "tool_result":
          addToolMessage(event.name, event.result);
          break;
        case "message_end":
          finalizeLastAssistant();
          setSending(false);
          break;
        case "error":
          addMessage({ role: "assistant", content: `Error: ${event.message}` });
          setSending(false);
          break;
      }
    });

    client
      .connect()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));

    return () => {
      unsubscribe();
      client.disconnect();
      clientRef.current = null;
      setConnected(false);
    };
  }, [wsUrl, sessionId]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || !clientRef.current || !connected || sending) return;

    setInput("");
    addMessage({ role: "user", content: text });
    setSending(true);

    try {
      await clientRef.current.agentRequest(text, {
        sessionKey: sessionId ?? undefined,
        role: sessionContext?.role,
        appId: sessionContext?.appId,
        nodeIds: sessionContext?.nodeIds,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      addMessage({ role: "assistant", content: `Send error: ${msg}` });
      setSending(false);
    }
  }, [input, connected, sending, sessionId, sessionContext, addMessage, setSending]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!sessionId) {
    return (
      <div style={{ padding: 16, color: "#6b7280", textAlign: "center", fontSize: 13 }}>
        Select nodes in the graph and compose a session to start chatting.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", fontFamily: "system-ui, sans-serif" }}>
      {/* Header */}
      <div style={{ padding: "8px 12px", borderBottom: "1px solid #e5e7eb", fontSize: 11, color: "#6b7280" }}>
        Session: {sessionId?.slice(0, 12)}...
        <span style={{ marginLeft: 8, color: connected ? "#10b981" : "#ef4444" }}>
          {connected ? "connected" : "disconnected"}
        </span>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflow: "auto", padding: "8px 12px" }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <div
              style={{
                fontSize: 10,
                fontWeight: 600,
                color:
                  msg.role === "user"
                    ? "#3b82f6"
                    : msg.role === "tool"
                      ? "#f59e0b"
                      : "#6b7280",
                marginBottom: 2,
              }}
            >
              {msg.role === "tool" ? `tool: ${msg.toolName}` : msg.role}
            </div>
            <div
              style={{
                fontSize: 12,
                lineHeight: 1.5,
                whiteSpace: "pre-wrap",
                color: "#1f2937",
                background: msg.role === "user" ? "#eff6ff" : msg.role === "tool" ? "#fef3c7" : "#f9fafb",
                padding: "6px 10px",
                borderRadius: 6,
              }}
            >
              {msg.content}
              {msg.streaming && (
                <span style={{ opacity: 0.5, animation: "blink 1s infinite" }}>|</span>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ borderTop: "1px solid #e5e7eb", padding: 8, display: "flex", gap: 6 }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!connected || sending}
          placeholder={connected ? "Type a message..." : "Connecting..."}
          rows={2}
          style={{
            flex: 1,
            resize: "none",
            border: "1px solid #d1d5db",
            borderRadius: 6,
            padding: "6px 10px",
            fontSize: 12,
            fontFamily: "inherit",
            outline: "none",
          }}
        />
        <button
          onClick={handleSend}
          disabled={!connected || sending || !input.trim()}
          style={{
            padding: "6px 16px",
            background: connected ? "#3b82f6" : "#9ca3af",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            cursor: connected ? "pointer" : "default",
            fontSize: 12,
            fontWeight: 500,
          }}
        >
          {sending ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
