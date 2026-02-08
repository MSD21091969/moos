"use client";

import { Sparkles } from "lucide-react";

// Default quick actions for the canvas
export const QUICK_ACTIONS = [
  { label: "Query GitHub", prompt: "Search GitHub for pydantic-ai examples" },
  { label: "Load Data Skill", prompt: "Load the math helper skill" },
  { label: "Analyze Data", prompt: "Analyze the uploaded data file" },
  { label: "Write Script", prompt: "Write a Python script to process files" },
];

interface QuickActionsProps {
  actions: { label: string; prompt: string }[];
  onSelect: (prompt: string) => void;
  disabled: boolean;
}

export function QuickActions({
  actions,
  onSelect,
  disabled,
}: QuickActionsProps) {
  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {actions.map((action, i) => (
        <button
          key={i}
          onClick={() => onSelect(action.prompt)}
          disabled={disabled}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-full text-xs text-zinc-400 hover:text-zinc-200 transition disabled:opacity-50"
        >
          <Sparkles size={12} className="text-violet-400" />
          {action.label}
        </button>
      ))}
    </div>
  );
}
