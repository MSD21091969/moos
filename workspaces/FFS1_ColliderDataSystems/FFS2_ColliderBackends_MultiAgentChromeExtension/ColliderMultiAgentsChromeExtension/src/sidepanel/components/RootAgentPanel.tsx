import React, { useCallback, useEffect, useRef, useState } from "react";
import { AgentEvent, NanoClawRpcClient } from "../lib/nanoclaw-rpc";
import { useAppStore } from "../stores/appStore";

const AGENT_RUNNER_URL = "http://localhost:8004";

interface Message {
  role: "user" | "assistant" | "tool";
  content: string;
  streaming?: boolean;
  toolName?: string;
}

interface SessionPreview {
  node_count: number;
  skill_count: number;
  tool_count: number;
  role: string;
  vector_matches: number;
}

export default function RootAgentPanel() {
  const { selectedAppId, rootSessionId, rootSessionPreview, setRootSessionId, setRootSessionPreview } =
    useAppStore();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [booting, setBooting] = useState(false);
  const [bootError, setBootError] = useState<string | null>(null);
  const [nanoClawWsUrl, setNanoClawWsUrl] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const clientRef = useRef<NanoClawRpcClient | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Boot root session when app selected
  useEffect(() => {
    if (selectedAppId && !rootSessionId && !booting) {
      bootRootSession(selectedAppId);
    }
  }, [selectedAppId]);

  // Reset + reboot when app changes
  useEffect(() => {
    setMessages([]);
    setInput("");
    setBusy(false);
    setBootError(null);
    setNanoClawWsUrl(null);
    clientRef.current?.close();
    clientRef.current = null;
    if (selectedAppId) {
      bootRootSession(selectedAppId);
    }
  }, [selectedAppId]);

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

  async function bootRootSession(appId: string) {
    setBooting(true);
    setBootError(null);
    setRootSessionId(null);
    setRootSessionPreview(null);

    try {
      const resp = await fetch(`${AGENT_RUNNER_URL}/agent/root/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ app_id: appId }),
      });

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`${resp.status}: ${text}`);
      }

      const data = await resp.json();
      setRootSessionId(data.session_id as string);
      setRootSessionPreview(data.preview as SessionPreview);
      setNanoClawWsUrl((data.nanoclaw_ws_url as string | null) ?? null);
    } catch (err) {
      setBootError(err instanceof Error ? err.message : "Failed to boot root agent");
    } finally {
      setBooting(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || busy || !rootSessionId || !nanoClawWsUrl) return;

    const userMsg = input.trim();
    setInput("");
    setBusy(true);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMsg },
      { role: "assistant", content: "", streaming: true },
    ]);

    try {
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

  if (!selectedAppId) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-gray-500 px-4 text-center">
        Select an application to boot the root agent.
      </div>
    );
  }

  if (booting) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2 text-sm text-gray-400">
        <div className="w-4 h-4 border-2 border-green-400 border-t-transparent rounded-full animate-spin" />
        <span>Booting root agent…</span>
      </div>
    );
  }

  if (bootError) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 px-4">
        <p className="text-xs text-red-400 text-center">{bootError}</p>
        <button
          type="button"
          onClick={() => bootRootSession(selectedAppId)}
          className="text-xs px-3 py-1 rounded bg-gray-700 hover:bg-gray-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {rootSessionPreview && (
        <div className="px-3 py-1.5 border-b border-gray-700 flex gap-3 text-xs text-gray-400">
          <span className="text-green-400 font-medium">Root</span>
          <span>{rootSessionPreview.node_count} nodes</span>
          <span>{rootSessionPreview.tool_count} tools</span>
          <span>{rootSessionPreview.skill_count} skills</span>
          <span className="ml-auto text-gray-600">superadmin</span>
        </div>
      )}

      {!nanoClawWsUrl && rootSessionId && (
        <div className="px-3 py-1 text-xs text-yellow-500 border-b border-gray-700">
          No NanoClawBridge configured. Set NANOCLAW_BRIDGE_URL on AgentRunner.
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
        {messages.length === 0 && (
          <p className="text-xs text-gray-600 mt-4 text-center">
            Root agent ready — full graph access, all management tools available.
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
              <span className="inline-block w-1.5 h-3 ml-0.5 bg-green-400 animate-pulse align-middle" />
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
          disabled={busy || !rootSessionId || !nanoClawWsUrl}
          placeholder="Command the root agent…"
          className="flex-1 bg-gray-800 text-sm text-gray-100 rounded px-2 py-1 outline-none placeholder-gray-600 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={busy || !input.trim() || !rootSessionId || !nanoClawWsUrl}
          className="text-xs px-2 py-1 rounded bg-green-700 hover:bg-green-600 disabled:opacity-40"
        >
          {busy ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
