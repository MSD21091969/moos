import React, { useCallback, useEffect, useRef, useState } from "react";
import { AgentEvent, NanoClawRpcClient } from "../lib/nanoclaw-rpc";

interface Message {
  role: "user" | "assistant" | "tool";
  content: string;
  streaming?: boolean;
  toolName?: string;
}

interface AgentSeatProps {
  sessionId: string | null;
  nanoClawWsUrl: string | null;
}

export default function AgentSeat({ sessionId, nanoClawWsUrl }: AgentSeatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const clientRef = useRef<NanoClawRpcClient | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Reset on session change
  useEffect(() => {
    setMessages([]);
    setInput("");
    setBusy(false);
    clientRef.current?.close();
    clientRef.current = null;
  }, [sessionId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clientRef.current?.close();
    };
  }, []);

  const appendToLastAssistant = useCallback((chunk: string) => {
    setMessages((prev) => {
      const updated = [...prev];
      const last = updated[updated.length - 1];
      if (last?.role === "assistant") {
        updated[updated.length - 1] = { ...last, content: last.content + chunk };
      }
      return updated;
    });
  }, []);

  const finishLastAssistant = useCallback(() => {
    setMessages((prev) => {
      const updated = [...prev];
      const last = updated[updated.length - 1];
      if (last?.role === "assistant") {
        updated[updated.length - 1] = { ...last, streaming: false };
      }
      return updated;
    });
    setBusy(false);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || busy || !sessionId || !nanoClawWsUrl) return;

    const userMsg = input.trim();
    setInput("");
    setBusy(true);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMsg },
      { role: "assistant", content: "", streaming: true },
    ]);

    try {
      // Connect (or reuse) the RPC client
      if (!clientRef.current || clientRef.current.state !== "connected") {
        clientRef.current?.close();
        const client = new NanoClawRpcClient(nanoClawWsUrl);
        clientRef.current = client;

        client.onAgentEvent((event: AgentEvent) => {
          switch (event.kind) {
            case "text_delta":
              appendToLastAssistant(event.text);
              break;

            case "tool_use_start":
              setMessages((prev) => [
                ...prev,
                {
                  role: "tool" as const,
                  content: `Calling ${event.name}...`,
                  toolName: event.name,
                },
              ]);
              break;

            case "tool_result":
              setMessages((prev) => {
                const updated = [...prev];
                const toolIdx = updated.findLastIndex(
                  (m) => m.role === "tool" && m.toolName === event.name,
                );
                if (toolIdx >= 0) {
                  updated[toolIdx] = {
                    ...updated[toolIdx],
                    content: `${event.name}: ${event.result.slice(0, 200)}`,
                  };
                }
                return updated;
              });
              break;

            case "message_end":
              finishLastAssistant();
              break;

            case "error":
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.role === "assistant") {
                  updated[updated.length - 1] = {
                    ...last,
                    content: `[Error: ${event.message}]`,
                    streaming: false,
                  };
                }
                return updated;
              });
              setBusy(false);
              break;
          }
        });

        await client.connect();
      }

      await clientRef.current.agentRequest(userMsg);
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.role === "assistant" && last.streaming) {
          updated[updated.length - 1] = {
            ...last,
            content:
              last.content ||
              `[NanoClawBridge unavailable — ${err instanceof Error ? err.message : "connection failed"}]`,
            streaming: false,
          };
        }
        return updated;
      });
      setBusy(false);
    }
  }

  if (!sessionId) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-gray-500 px-4 text-center">
        Compose a context set above to start an agent session.
      </div>
    );
  }

  if (!nanoClawWsUrl) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-gray-500 px-4 text-center">
        No NanoClawBridge configured. Set NANOCLAW_BRIDGE_URL on AgentRunner.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-1 text-xs text-gray-500 border-b border-gray-700 truncate">
        Session: <span className="text-green-400">{sessionId.slice(0, 8)}…</span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
        {messages.length === 0 && (
          <p className="text-xs text-gray-600 mt-4 text-center">
            Ask anything about this composed context.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`text-xs rounded px-3 py-2 whitespace-pre-wrap leading-relaxed ${msg.role === "user"
                ? "bg-gray-700 text-gray-100 ml-6"
                : msg.role === "tool"
                  ? "bg-gray-900 text-yellow-400 mx-6 font-mono"
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

      <form onSubmit={handleSubmit} className="flex gap-1 px-3 py-2 border-t border-gray-700">
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
