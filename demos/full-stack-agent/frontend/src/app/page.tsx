"use client";

import { useChat } from "@/hooks/useChat";
import { Send, Terminal, Loader2, Play, Bot, User, Menu, Plus, MessageSquare, Settings } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useState } from "react";

export default function Home() {
  const { messages, input, setInput, sendMessage, isConnected, isLoading } = useChat();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-[#09090b] text-gray-100 font-sans overflow-hidden">
      
      {/* Sidebar */}
      <aside className={`${isSidebarOpen ? 'w-[260px]' : 'w-0'} bg-black/40 border-r border-[#27272a] transition-all duration-300 ease-in-out flex flex-col overflow-hidden`}>
        <div className="p-4 flex items-center gap-2 border-b border-[#27272a]">
             <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-900/20">
                <Terminal className="w-5 h-5 text-white" />
             </div>
             <span className="font-semibold text-sm tracking-tight">Agent Workspace</span>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
            <button className="w-full text-left px-3 py-2 rounded-lg bg-[#27272a] hover:bg-[#27272a]/80 text-sm font-medium flex items-center gap-2 transition-colors">
                <Plus className="w-4 h-4" />
                New Chat
            </button>
            
            <div className="pt-4 pb-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Recents
            </div>
            
            <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-[#27272a]/50 text-sm text-gray-400 flex items-center gap-2 transition-colors">
                <MessageSquare className="w-4 h-4" />
                Project Planning
            </button>
        </div>

        <div className="p-4 border-t border-[#27272a]">
             <div className="flex items-center gap-2 text-xs text-gray-500">
                <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" : "bg-red-500"}`} />
                {isConnected ? "System Online" : "System Offline"}
             </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative">
        {/* Header */}
        <header className="h-14 border-b border-[#27272a] flex items-center justify-between px-4 bg-[#09090b]/50 backdrop-blur-sm z-10">
            <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 hover:bg-[#27272a] rounded-md transition-colors text-gray-400">
                <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-4">
                <button className="p-2 hover:bg-[#27272a] rounded-md transition-colors text-gray-400">
                    <Settings className="w-5 h-5" />
                </button>
            </div>
        </header>

        {/* Chat Area */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 scroll-smooth">
          {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-gray-500 opacity-60 max-w-md mx-auto text-center">
                  <div className="w-16 h-16 bg-[#27272a] rounded-2xl flex items-center justify-center mb-6">
                    <Bot className="w-8 h-8 text-gray-400" />
                  </div>
                  <h2 className="text-xl font-semibold text-gray-200 mb-2">How can I help you?</h2>
                  <p className="text-sm">I can analyze files, write code, and coordinate tasks using subagents.</p>
              </div>
          )}
          
          {messages.map((msg, i) => (
            <div key={i} className={`group flex gap-4 max-w-3xl mx-auto ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
               {/* Avatar */}
               <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                   msg.role === 'user' ? 'bg-blue-600' : 
                   msg.role === 'error' ? 'bg-red-500' : 'bg-[#eab308]'
               }`}>
                   {msg.role === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-black" />}
               </div>

               {/* Message Bubble */}
               <div className={`flex-1 min-w-0 space-y-2`}>
                   <div className="flex items-baseline gap-2">
                       <span className="text-sm font-semibold text-gray-200">
                           {msg.role === 'user' ? 'You' : 'Deep Agent'}
                       </span>
                   </div>
                   
                   <div className={`text-sm leading-7 prose prose-invert prose-p:leading-7 prose-pre:bg-[#18181b] prose-pre:border prose-pre:border-[#27272a] max-w-none ${
                     msg.role === 'error' ? 'text-red-300' : 'text-gray-300'
                   }`}>
                      {msg.role === 'agent' ? (
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                      ) : (
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                      )}
                   </div>
               </div>
            </div>
          ))}

          {isLoading && (
              <div className="flex gap-4 max-w-3xl mx-auto">
                 <div className="w-8 h-8 rounded-lg bg-[#eab308] flex items-center justify-center flex-shrink-0">
                     <Bot className="w-5 h-5 text-black" />
                 </div>
                 <div className="flex items-center gap-2 text-gray-400 text-sm pt-1.5">
                     <Loader2 className="w-4 h-4 animate-spin" />
                     Thinking...
                 </div>
              </div>
          )}
        </main>

        {/* Input Area */}
        <footer className="p-6">
          <div className="max-w-3xl mx-auto relative">
            <div className="relative flex items-end gap-2 bg-[#18181b] border border-[#27272a] rounded-xl p-2 shadow-sm focus-within:ring-1 focus-within:ring-blue-600/50 transition-all">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Send a message..."
                  className="flex-1 bg-transparent text-gray-100 placeholder-gray-500 border-0 focus:ring-0 resize-none h-14 min-h-[56px] py-3.5 px-2 max-h-[200px]"
                />
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || !isConnected}
                  className="mb-1 bg-[#27272a] hover:bg-blue-600 disabled:opacity-50 disabled:hover:bg-[#27272a] text-gray-400 hover:text-white rounded-lg p-2 transition-all"
                >
                  <Send className="w-4 h-4" />
                </button>
            </div>
            <div className="text-center mt-2">
                <p className="text-[10px] text-gray-600">Deep Agent can make mistakes. Verify important information.</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
