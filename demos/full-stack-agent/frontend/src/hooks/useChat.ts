import { useState, useRef, useEffect, useCallback } from "react";

type MessageType = "user" | "agent" | "error";

export interface Message {
  role: MessageType;
  content: string;
  thoughts?: string; // Accumulate thoughts here
}

interface UseChatReturn {
  messages: Message[];
  input: string;
  setInput: (value: string) => void;
  sendMessage: () => void;
  isConnected: boolean;
  isLoading: boolean;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const socket = new WebSocket("ws://localhost:8000/ws/chat");

    socket.onopen = () => {
      console.log("Connected to WS");
      setIsConnected(true);
    };

    socket.onclose = () => {
      console.log("Disconnected from WS");
      setIsConnected(false);
      setIsLoading(false);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "token") {
        // Append token to the last message if it's from agent, otherwise create new
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.role === "agent") {
            return [
              ...prev.slice(0, -1),
              { ...lastMsg, content: data.content }, // Replace content (presuming snapshot)
            ];
          } else {
            // Start a new agent message
            setIsLoading(false);
            return [...prev, { role: "agent", content: data.content }];
          }
        });
      } else if (data.type === "agent_response") {
        // Final response (often redundant if streaming tokens, but good for validation)
        // For now, we trust tokens.
        setIsLoading(false);
      } else if (data.type === "agent_thought") {
        // Handle thoughts (TBD)
      } else if (data.type === "error") {
        setMessages((prev) => [
          ...prev,
          { role: "error", content: data.detail },
        ]);
        setIsLoading(false);
      }
    };

    ws.current = socket;

    return () => {
      socket.close();
    };
  }, []);

  const sendMessage = useCallback(() => {
    if (
      !input.trim() ||
      !ws.current ||
      ws.current.readyState !== WebSocket.OPEN
    )
      return;

    // Add user message
    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // Send to backend
    ws.current.send(JSON.stringify({ type: "user_message", content: input }));
    setInput("");
  }, [input]);

  return { messages, input, setInput, sendMessage, isConnected, isLoading };
}
