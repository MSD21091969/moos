import React, { useState } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function AgentSeat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm the Collider AI Pilot. How can I help you?",
    },
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // Stub: echo back for now
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Received: "${userMessage.content}". Agent integration pending.`,
        },
      ]);
    }, 500);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`rounded-lg px-3 py-2 text-sm max-w-[85%] ${msg.role === "user"
                ? "ml-auto bg-blue-600 text-white"
                : "bg-gray-700 text-gray-100"
              }`}
          >
            {msg.content}
          </div>
        ))}
      </div>
      <div className="border-t border-gray-700 p-2 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask the AI pilot..."
          className="flex-1 bg-gray-800 text-white text-sm rounded px-3 py-2 outline-none focus:ring-1 focus:ring-blue-500"
        />
        <button
          onClick={handleSend}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-2 rounded"
        >
          Send
        </button>
      </div>
    </div>
  );
}
