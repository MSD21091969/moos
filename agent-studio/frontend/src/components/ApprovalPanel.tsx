"use client";

import { AlertTriangle, Check, X } from "lucide-react";

interface ApprovalPanelProps {
  action: string;
  details: string;
  onApprove: () => void;
  onDeny: () => void;
}

export function ApprovalPanel({
  action,
  details,
  onApprove,
  onDeny,
}: ApprovalPanelProps) {
  return (
    <div className="bg-amber-900/30 border border-amber-500/50 rounded-lg p-4 my-4">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-amber-500/20 rounded-lg">
          <AlertTriangle size={20} className="text-amber-400" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-amber-200 mb-1">
            Approval Required
          </h3>
          <p className="text-sm text-amber-100/80 mb-1">
            The following operation requires your approval:
          </p>
          <div className="bg-black/30 rounded px-3 py-2 my-2">
            <p className="font-mono text-sm text-amber-200">{action}</p>
            <p className="text-xs text-zinc-400 mt-1">{details}</p>
          </div>
          <div className="flex gap-2 mt-3">
            <button
              onClick={onApprove}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition"
            >
              <Check size={16} />
              Approve All
            </button>
            <button
              onClick={onDeny}
              className="flex items-center gap-2 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-zinc-300 rounded-lg text-sm font-medium transition"
            >
              <X size={16} />
              Deny All
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
