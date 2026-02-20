import React, { useEffect, useRef, useState } from "react";
import { useAppStore } from "../stores/appStore";

const AGENT_RUNNER_URL = "http://localhost:8004";

interface Message {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

export default function AgentSeat() {
  const { selectedNodePath } = useAppStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);

  // Derive leaf node_id from the selected path (last segment)
  const nodeId = selectedNodePath?.split("/").pop() ?? null;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Clean up open SSE connection on unmount
  useEffect(() => {
    return () => {
      esRef.current?.close();
    };
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || busy || !nodeId) return;

    const userMsg = input.trim();
    setInput("");
    setBusy(true);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMsg },
      { role: "assistant", content: "", streaming: true },
    ]);

    const params = new URLSearchParams({ node_id: nodeId, message: userMsg });
    const es = new EventSource(`${AGENT_RUNNER_URL}/agent/chat?${params}`);
    esRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as {
          type: "delta" | "done" | "error";
          text?: string;
          message?: string;
        };

        if (data.type === "delta" && data.text) {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === "assistant") {
              updated[updated.length - 1] = {
                ...last,
                content: last.content + data.text,
              };
            }
            return updated;
          });
        } else if (data.type === "done") {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === "assistant") {
              updated[updated.length - 1] = { ...last, streaming: false };
            }
            return updated;
          });
          es.close();
          setBusy(false);
        } else if (data.type === "error") {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === "assistant") {
              updated[updated.length - 1] = {
                ...last,
                content: `[Error: ${data.message ?? "Unknown error"}]`,
                streaming: false,
              };
            }
            return updated;
          });
          es.close();
          setBusy(false);
        }
      } catch {
        // Ignore parse errors on keepalive / empty events
      }
    };

    es.onerror = () => {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.role === "assistant" && last.streaming) {
          updated[updated.length - 1] = {
            ...last,
            content:
              last.content || "[Agent Runner unavailable — is it running on :8003?]",
            streaming: false,
          };
        }
        return updated;
      });
      es.close();
      setBusy(false);
    };
  }

  if (!nodeId) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-gray-500 px-4 text-center">
        Select a node from the Tree view to start an agent session.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Node context indicator */}
      <div className="px-3 py-1 text-xs text-gray-500 border-b border-gray-700 truncate">
        Node: <span className="text-gray-400">{nodeId}</span>
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
        {messages.length === 0 && (
          <p className="text-xs text-gray-600 mt-4 text-center">
            Ask anything about this workspace node.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`text-xs rounded px-3 py-2 whitespace-pre-wrap leading-relaxed ${
              msg.role === "user"
                ? "bg-gray-700 text-gray-100 ml-6"
                : "bg-gray-800 text-gray-200 mr-6"
            }`}
          >
            {msg.content}
            {msg.streaming && (
              <span className="inline-block w-1.5 h-3 ml-0.5 bg-blue-400 animate-pulse align-middle" />
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="flex gap-1 px-3 py-2 border-t border-gray-700"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={busy}
          placeholder="Message the agent…"
          className="flex-1 bg-gray-800 text-sm text-gray-100 rounded px-2 py-1 outline-none placeholder-gray-600 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="text-xs px-2 py-1 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-40"
        >
          {busy ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
