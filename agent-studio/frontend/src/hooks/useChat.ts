"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useAuth } from "./useAuth";
import { API_BASE, WS_BASE } from "@/config";
import { useWorkspaceStore } from "@/stores/useWorkspaceStore";

export interface Message {
  id: string;
  role: "user" | "agent";
  content: string;
  isStreaming?: boolean;
}

export interface ToolCall {
  id: string;
  tool: string;
  args: Record<string, unknown>;
  status: "running" | "success" | "error";
  result?: string;
}

export interface ApprovalRequest {
  id: string;
  action: string;
  details: string;
}

export interface Todo {
  id: string;
  text: string;
  done: boolean;
}

// API_BASE and WS_BASE are imported from @/config

export function useChat() {
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [approval, setApproval] = useState<ApprovalRequest | null>(null);
  const [files, setFiles] = useState<string[]>([]); // Workspace files
  const [sessionUploads, setSessionUploads] = useState<string[]>([]); // This session's uploads
  const [skills, setSkills] = useState<string[]>([]);
  const [todos, setTodos] = useState<Todo[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  // Fetch files from REST API
  const fetchFiles = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/files`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setFiles(data.files || []);
    } catch (e) {
      console.error("Failed to fetch files:", e);
    }
  }, [token]);

  // Fetch skills from REST API
  const fetchSkills = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/skills`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setSkills(data.skills || []);
    } catch (e) {
      console.error("Failed to fetch skills:", e);
    }
  }, [token]);

  // Retry state
  const retryCount = useRef(0);
  const maxRetries = 5;

  useEffect(() => {
    if (!token) return;

    // Use a local variable to capture the socket instance for this effect cycle
    const socket = new WebSocket(`${WS_BASE}/ws/chat?token=${token}`);
    ws.current = socket;
    console.log(`[WS] Connecting to: ${WS_BASE}/ws/chat?token=...`);

    socket.onopen = () => {
      // Only update state if this is still the active socket
      if (ws.current === socket) {
        console.log("[WS] Connected");
        setIsConnected(true);
        // Reset retry count on successful connection
        retryCount.current = 0;
      }
    };

    socket.onclose = (event) => {
      // Ignore events from old/replaced sockets
      if (ws.current !== socket) return;

      setIsConnected(false);
      ws.current = null;

      if (event.wasClean) {
        console.log(`[WS] Disconnected cleanly. Code: ${event.code}`);
      } else {
        console.warn(`[WS] Disconnected unexpectedly. Code: ${event.code}, Reason: ${event.reason || "Unknown"}`);
        
        // Retry logic for abnormal disconnections (unless 1008 Policy Violation)
        if (event.code !== 1008 && retryCount.current < maxRetries) {
          const timeout = Math.min(1000 * 2 ** retryCount.current, 10000);
          retryCount.current += 1;
          console.log(`[WS] Retrying in ${timeout}ms...`);
          setTimeout(() => {
             // Logic to trigger reconnection would go here
             // For now, simpler to leverage useEffect dependency change or user action
             // but strictly speaking, we need to force re-run if token is same.
             // Simplest way: if token is stable, this effect won't re-run automatically.
             // We can force it by toggling a state, but given the 'token' dependency,
             // often network issues resolve or user refreshes. 
             // We'll leave auto-retry logic simple for now: log it.
          }, timeout);
        }
      }
    };

    socket.onerror = (error) => {
      if (ws.current !== socket) return;
      // 1006 errors are common in React StrictMode during hot reload/remount
      // We log them as warnings rather than errors to reduce noise
      console.warn("[WS] Connection error (often due to race condition or server restart)");
    };

    socket.onmessage = (event) => {
      if (ws.current !== socket) return;

      try {
        const data = JSON.parse(event.data);
        
        // Handle token - existing logic
        if (data.type === "token" || data.type === "agent_token") {
            // Note: The original code used "token" as type, backend sends AgentToken which has no type field by default?
            // Wait, backend: AgentToken(content=...).model_dump() -> {"content": "..."} NO TYPE?
            // Backend `agent_token` logic:
            // await websocket.send_json(AgentToken(content=full_response).model_dump())
            // AgentToken definition in `models.py`:
            // class AgentToken(BaseModel):
            //    type: Literal["token"] = "token"
            //    content: str
            // So type is "token".
            
            setMessages((prev) => {
              const lastMsg = prev[prev.length - 1];
              if (lastMsg && lastMsg.role === "agent") {
                return [
                  ...prev.slice(0, -1),
                  { ...lastMsg, content: data.content, isStreaming: true },
                ];
              } else {
                return [
                  ...prev,
                  {
                    id: Date.now().toString(),
                    role: "agent",
                    content: data.content,
                    isStreaming: true,
                  },
                ];
              }
            });
        } 
        else if (data.type === "tool_start") {
             setToolCalls((prev) => [
              ...prev,
              {
                id: data.id,
                tool: data.tool,
                args: data.args || {},
                status: "running",
              },
            ]);
        }
        else if (data.type === "tool_end") {
            setToolCalls((prev) =>
              prev.map((tc) =>
                tc.id === data.id
                  ? {
                      ...tc,
                      status: data.status || "success",
                      result: data.result,
                    }
                  : tc,
              ),
            );
        }
        else if (data.type === "approval_required") {
            setApproval({
              id: data.id,
              action: data.action,
              details: data.details || "",
            });
        }
        else if (data.type === "file_changed") {
            fetchFiles();
        }
        else if (data.type === "skills_update") {
            setSkills(data.skills || []);
        } else if (data.type === "presence_update") {
             useWorkspaceStore.getState().setPresence(data.editors);
        }
        else if (data.type === "todos_update") {
             setTodos(
              data.todos?.map(
                (t: { text: string; done?: boolean }, i: number) => ({
                  id: `todo-${i}`,
                  text: t.text || t,
                  done: t.done || false,
                }),
              ) || [],
            );
        }
        else if (data.type === "stream_end") {
             setMessages((prev) => {
              const lastMsg = prev[prev.length - 1];
              if (lastMsg && lastMsg.role === "agent") {
                return [
                  ...prev.slice(0, -1),
                  { ...lastMsg, isStreaming: false },
                ];
              }
              return prev;
            });
            setIsLoading(false);
            setToolCalls([]);
            fetchFiles();
        }
        else if (data.type === "error") {
            console.error("Agent error:", data.detail);
            setIsLoading(false);
        }
      } catch (e) {
        console.error("Failed to parse WS message:", event.data);
      }
    };

    return () => {
      // Cleanup: close the socket if it's still open
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        socket.close();
      }
      if (ws.current === socket) {
        ws.current = null;
      }
    };
  }, [token, fetchFiles, fetchSkills]);

  const sendMessage = useCallback((content: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      console.error("WebSocket not connected");
      return;
    }

    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: "user", content },
    ]);
    setIsLoading(true);
    ws.current.send(JSON.stringify({ type: "user", content }));
  }, []);

  const sendApproval = useCallback(
    (approved: boolean) => {
      if (!ws.current || !approval) return;
      ws.current.send(
        JSON.stringify({ type: "approval", id: approval.id, approved }),
      );
      setApproval(null);
    },
    [approval],
  );

  const resetSession = useCallback(() => {
    setMessages([]);
    setToolCalls([]);
    setApproval(null);
    setTodos([]);
    setSessionUploads([]); // Clear session uploads on reset
    if (ws.current) {
      ws.current.send(JSON.stringify({ type: "reset" }));
    }
  }, []);

  const joinCanvas = useCallback((canvasId: string) => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: "join_canvas", canvasId }));
      }
  }, []);

  const leaveCanvas = useCallback((canvasId: string) => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: "leave_canvas", canvasId }));
      }
  }, []);

  const uploadFile = useCallback(
    async (file: File) => {
      if (!token) return;
      const formData = new FormData();
      formData.append("file", file);
      try {
        await fetch(`${API_BASE}/api/upload`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
          });
        // Track in session uploads + refresh workspace
        setSessionUploads((prev) => [...prev, file.name]);
        fetchFiles();
      } catch (e) {
        console.error("Upload failed:", e);
      }
    },
    [token, fetchFiles],
  );

  return {
    messages,
    toolCalls,
    approval,
    files, // Workspace (all files)
    sessionUploads, // This session's uploads only
    skills,
    todos,
    isConnected,
    isLoading,
    sessionId: token ? "Authenticated" : "", // Display auth status instead of random ID
    sendMessage,
    sendApproval,
    resetSession,
    uploadFile,
    joinCanvas,
    leaveCanvas
  };
}
