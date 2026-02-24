/**
 * Session Store — Agent session + messages state
 *
 * Manages the current agent session, conversation messages,
 * and WebSocket connection state.
 */

import { create } from "zustand";

export interface Message {
  role: "user" | "assistant" | "tool";
  content: string;
  streaming?: boolean;
  toolName?: string;
}

interface SessionState {
  sessionId: string | null;
  wsUrl: string | null;
  sessionContext: {
    appId: string;
    nodeIds: string[];
    role: string;
  } | null;
  connected: boolean;
  messages: Message[];
  sending: boolean;

  setSession: (
    sessionId: string,
    wsUrl: string,
    sessionContext?: { appId: string; nodeIds: string[]; role: string },
  ) => void;
  setConnected: (connected: boolean) => void;
  addMessage: (message: Message) => void;
  updateLastAssistant: (text: string) => void;
  finalizeLastAssistant: () => void;
  addToolMessage: (toolName: string, result: string) => void;
  setSending: (sending: boolean) => void;
  clearMessages: () => void;
  reset: () => void;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessionId: null,
  wsUrl: null,
  sessionContext: null,
  connected: false,
  messages: [],
  sending: false,

  setSession: (sessionId, wsUrl, sessionContext) =>
    set({ sessionId, wsUrl, sessionContext: sessionContext ?? null }),

  setConnected: (connected) => set({ connected }),

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  updateLastAssistant: (text) =>
    set((state) => {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant" && last.streaming) {
        msgs[msgs.length - 1] = { ...last, content: last.content + text };
      } else {
        msgs.push({ role: "assistant", content: text, streaming: true });
      }
      return { messages: msgs };
    }),

  finalizeLastAssistant: () =>
    set((state) => {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant" && last.streaming) {
        msgs[msgs.length - 1] = { ...last, streaming: false };
      }
      return { messages: msgs };
    }),

  addToolMessage: (toolName, result) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { role: "tool" as const, content: result, toolName },
      ],
    })),

  setSending: (sending) => set({ sending }),
  clearMessages: () => set({ messages: [] }),
  reset: () =>
    set({
      sessionId: null,
      wsUrl: null,
      sessionContext: null,
      connected: false,
      messages: [],
      sending: false,
    }),
}));
