"use client";

import { useState, FormEvent, useRef, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useChat } from "@/hooks/useChat";
import { Sidebar } from "@/components/Sidebar";
import { ToolCallCard } from "@/components/ToolCallCard";
import { ApprovalPanel } from "@/components/ApprovalPanel";
import { WorkspaceCanvas } from "@/components/WorkspaceCanvas";
import { usePreferencesStore } from "@/stores/usePreferencesStore";
import { Bot, User, Send, Loader2, Save } from "lucide-react";
import { useCanvasStore } from "@/stores/useWorkspaceStore";

export default function Home() {
  const {
    isAuthenticated,
    email,
    logout,
    token,
    isLoading: authLoading,
  } = useAuth();
  const router = useRouter();

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  const {
    messages,
    toolCalls,
    approval,
    skills,
    todos,
    isConnected,
    isLoading,
    sendMessage,
    sendApproval,
    resetSession,
    uploadFile,
  } = useChat();

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, toolCalls]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput("");
  };

  const { theme, sidebarOpen } = usePreferencesStore();
  const isDark = theme === "dark";
  const { commitCanvas, getActiveCanvas } = useCanvasStore();

  // URL Parameter Handling
  const searchParams = useSearchParams();
  const initialCanvasId = searchParams.get("canvas");

  // Check if we have active chat (messages or tool calls)
  const hasActiveChat = messages.length > 0 || toolCalls.length > 0;

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950 text-white">
        <Loader2 size={48} className="animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div
      className={`flex h-screen ${
        theme === "dark"
          ? "bg-zinc-950 text-zinc-100"
          : "bg-gray-100 text-gray-900"
      }`}
    >
      {/* Sidebar */}
      <div
        className={`transition-all duration-300 ease-in-out ${sidebarOpen ? "w-64" : "w-0"} overflow-hidden`}
      >
        <Sidebar
          isConnected={isConnected}
          skills={skills}
          todos={todos}
          onReset={resetSession}
          email={email}
          onLogout={logout}
          token={token}
        />
      </div>

      {/* Main Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {!hasActiveChat ? (
          /* Full Canvas View - No Chat Yet */
          <WorkspaceCanvas
            token={token}
            isConnected={isConnected}
            isLoading={isLoading}
            onSendMessage={sendMessage}
            onUploadFile={uploadFile}
            initialCanvasId={initialCanvasId}
          />
        ) : (
          /* Split View - Canvas + Chat */
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Compact Canvas Header */}
            <WorkspaceCanvas
              token={token}
              isConnected={isConnected}
              isLoading={isLoading}
              onSendMessage={sendMessage}
              onUploadFile={uploadFile}
              initialCanvasId={initialCanvasId}
            />

            {/* Chat Messages */}
            <div
              className={`flex-1 overflow-y-auto p-6 border-t ${
                isDark ? "border-zinc-800" : "border-gray-200"
              }`}
            >
              <div className="max-w-4xl mx-auto space-y-4">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex gap-3 ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {msg.role === "agent" && (
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-purple-600 flex items-center justify-center flex-shrink-0">
                        <Bot size={18} className="text-white" />
                      </div>
                    )}

                    <div
                      className={`max-w-2xl rounded-xl px-4 py-3 ${
                        msg.role === "user"
                          ? "bg-violet-600 text-white"
                          : isDark
                            ? "bg-zinc-800 text-zinc-100"
                            : "bg-white text-gray-900 shadow-sm border border-gray-200"
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                      {msg.isStreaming && (
                        <span className="inline-block w-2 h-4 bg-violet-400 animate-pulse ml-1" />
                      )}
                    </div>

                    {msg.role === "user" && (
                      <div
                        className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                          isDark ? "bg-zinc-700" : "bg-gray-200"
                        }`}
                      >
                        <User
                          size={18}
                          className={isDark ? "text-zinc-300" : "text-gray-600"}
                        />
                      </div>
                    )}
                  </div>
                ))}

                {/* Tool Calls */}
                {toolCalls.length > 0 && (
                  <div className="space-y-2 pl-11">
                    {toolCalls.map((tc) => (
                      <ToolCallCard key={tc.id} {...tc} />
                    ))}
                  </div>
                )}

                {/* Approval Panel */}
                {approval && (
                  <div className="pl-11">
                    <ApprovalPanel
                      action={approval.action}
                      details={approval.details}
                      onApprove={() => sendApproval(true)}
                      onDeny={() => sendApproval(false)}
                    />
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>
        )}

        {/* Input Area - Always Visible */}
        <div
          className={`border-t p-4 ${
            isDark ? "border-zinc-800" : "border-gray-200"
          }`}
        >
          <div className="max-w-4xl mx-auto">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a command or request..."
                disabled={!isConnected || isLoading || !!approval}
                className={`flex-1 border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:opacity-50 ${
                  isDark
                    ? "bg-zinc-800 border-zinc-700 text-zinc-100 placeholder-zinc-500"
                    : "bg-white border-gray-300 text-gray-900 placeholder-gray-400"
                }`}
              />
              <button
                type="button"
                onClick={async () => {
                  if (token && getActiveCanvas()) {
                    await commitCanvas(token);
                  }
                }}
                disabled={!isConnected || !getActiveCanvas()}
                className="px-4 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-700 disabled:opacity-50 rounded-xl transition flex items-center gap-2 font-medium text-white"
                title="Commit canvas to permanent storage"
              >
                <Save size={20} />
              </button>
              <button
                type="submit"
                disabled={
                  !isConnected || isLoading || !input.trim() || !!approval
                }
                className="px-5 py-3 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-700 disabled:opacity-50 rounded-xl transition flex items-center gap-2 font-medium text-white"
              >
                {isLoading ? (
                  <Loader2 size={20} className="animate-spin" />
                ) : (
                  <Send size={20} />
                )}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
