import React, { useState, useEffect, useRef } from "react";
import { Send, Mic, StopCircle, RefreshCw, X } from "lucide-react";
// Assuming shadcn/ui utils if available, or standard classnames
// import { cn } from "@/lib/utils";

// Types for the Pilot Interaction
interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
}

interface PilotOverlayProps {
  isConnected: boolean;
  onSendMessage: (msg: string) => void;
  messages: Message[];
  isThinking?: boolean;
  onClose?: () => void; // If we allow minimizing
}

export function PilotOverlay({
  isConnected,
  onSendMessage,
  messages,
  isThinking = false,
}: PilotOverlayProps) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSendMessage(input);
    setInput("");
  };

  return (
    <div
      className="fixed bottom-4 right-4 w-96 max-h-[600px] flex flex-col 
                    bg-black/40 backdrop-blur-xl border border-white/10 
                    rounded-2xl shadow-2xl overflow-hidden z-50 transition-all font-sans text-white"
    >
      {/* Header (Glass) */}
      <div className="h-12 bg-white/5 border-b border-white/10 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-400" : "bg-red-400 animate-pulse"}`}
          />
          <span className="font-medium text-sm tracking-wide text-white/90">
            Collider Pilot
          </span>
        </div>
        <div className="flex items-center gap-1">
          {/* Minimal controls */}
          <button className="p-1 hover:bg-white/10 rounded-md transition-colors">
            <RefreshCw className="w-4 h-4 text-white/60" />
          </button>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px] max-h-[450px] scrollbar-thin scrollbar-thumb-white/10">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-white/30 space-y-2">
            <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-white/20 rounded-full" />
            </div>
            <p className="text-sm">Ready to guide you.</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed
              ${
                msg.role === "user"
                  ? "bg-blue-600/80 text-white rounded-br-none"
                  : "bg-white/10 text-white/90 rounded-bl-none border border-white/5"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {isThinking && (
          <div className="flex justify-start">
            <div className="bg-white/5 rounded-2xl px-4 py-3 rounded-bl-none flex gap-1 items-center">
              <span
                className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce"
                style={{ animationDelay: "0ms" }}
              />
              <span
                className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce"
                style={{ animationDelay: "150ms" }}
              />
              <span
                className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce"
                style={{ animationDelay: "300ms" }}
              />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <form
        onSubmit={handleSubmit}
        className="p-3 bg-white/5 border-t border-white/10"
      >
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type instructions..."
            className="w-full bg-black/20 border border-white/10 rounded-xl pl-4 pr-12 py-3 
                       text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-white/20
                       focus:ring-1 focus:ring-white/10 transition-all"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="absolute right-2 p-1.5 bg-white/10 hover:bg-white/20 disabled:opacity-50 
                       text-white rounded-lg transition-all"
          >
            <Send className="w-4 h-4 transform rotate-0" />
          </button>
        </div>
        <div className="flex justify-between items-center mt-2 px-1">
          <span className="text-[10px] text-white/20 uppercase tracking-widest font-semibold">
            Deep Agent Active
          </span>
          {/* Voice Mode placeholder */}
          <button
            type="button"
            className="text-white/40 hover:text-white transition-colors"
          >
            <Mic className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
