export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ChatStore {
  messages: ChatMessage[];
  isAgentTyping: boolean;
  currentWorkflow: string | null;
  addMessage: (msg: Omit<ChatMessage, "id" | "timestamp">) => void;
  clearMessages: () => void;
  setAgentTyping: (typing: boolean) => void;
}
