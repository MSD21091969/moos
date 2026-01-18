"use client";

import {
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
  Terminal,
  FileEdit,
  Play,
} from "lucide-react";
import { useState } from "react";

interface ToolCallProps {
  id: string;
  tool: string;
  args: Record<string, unknown>;
  status: "running" | "success" | "error";
  result?: string;
}

export function ToolCallCard({ tool, args, status, result }: ToolCallProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [copied, setCopied] = useState(false);

  const getIcon = () => {
    if (tool.includes("write") || tool.includes("file"))
      return <FileEdit size={14} />;
    if (tool.includes("execute") || tool.includes("run"))
      return <Terminal size={14} />;
    return <Play size={14} />;
  };

  const getStatusColor = () => {
    switch (status) {
      case "running":
        return "text-yellow-400 bg-yellow-400/10 border-yellow-400/30";
      case "success":
        return "text-emerald-400 bg-emerald-400/10 border-emerald-400/30";
      case "error":
        return "text-red-400 bg-red-400/10 border-red-400/30";
    }
  };

  const copyResult = () => {
    if (result) {
      navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className={`border rounded-lg overflow-hidden ${getStatusColor()}`}>
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-white/5 transition"
      >
        {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {getIcon()}
        <span className="font-mono text-sm">./{tool}</span>
        <span className="ml-auto text-xs uppercase">
          {status === "running" && "⏳ Running..."}
          {status === "success" && "✓ Done"}
          {status === "error" && "✗ Error"}
        </span>
      </button>

      {/* Body */}
      {isOpen && (
        <div className="px-3 pb-3 space-y-2">
          {/* Args */}
          {Object.keys(args).length > 0 && (
            <div className="bg-black/30 rounded p-2 font-mono text-xs overflow-x-auto">
              {Object.entries(args).map(([key, val]) => (
                <div key={key}>
                  <span className="text-zinc-500">{key}: </span>
                  <span className="text-zinc-300">{JSON.stringify(val)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="relative">
              <pre className="bg-black/30 rounded p-2 font-mono text-xs text-zinc-300 overflow-x-auto max-h-32">
                {result}
              </pre>
              <button
                onClick={copyResult}
                className="absolute top-2 right-2 p-1 bg-zinc-700 rounded hover:bg-zinc-600 transition"
              >
                {copied ? (
                  <Check size={12} className="text-emerald-400" />
                ) : (
                  <Copy size={12} />
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
