import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: (string | undefined | null | false)[]): string {
  return twMerge(clsx(inputs));
}

const DOMAIN_COLORS: Record<string, { border: string; accent: string }> = {
  CLOUD: { border: "border-green-500", accent: "text-green-400" },
  FILESYST: { border: "border-blue-500", accent: "text-blue-400" },
  ADMIN: { border: "border-red-500", accent: "text-red-400" },
  SIDEPANEL: { border: "border-purple-500", accent: "text-purple-400" },
  AGENT_SEAT: { border: "border-yellow-500", accent: "text-yellow-400" },
};

export interface CardProps {
  appId: string;
  displayName: string | null;
  domain: string;
  nodeCount?: number;
  onClick?: () => void;
  className?: string;
}

export function Card({
  appId,
  displayName,
  domain,
  nodeCount,
  onClick,
  className,
}: CardProps) {
  const colors = DOMAIN_COLORS[domain] ?? {
    border: "border-gray-500",
    accent: "text-gray-400",
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left p-4 rounded-lg border-2 bg-gray-800 hover:bg-gray-750 transition-colors",
        colors.border,
        className
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-base font-semibold text-gray-100">
          {displayName ?? appId}
        </h3>
        <span
          className={cn(
            "text-xs font-mono px-2 py-0.5 rounded-full border",
            colors.accent,
            colors.border
          )}
        >
          {domain}
        </span>
      </div>
      <p className="text-sm text-gray-400 font-mono">{appId}</p>
      {nodeCount !== undefined && (
        <p className="text-xs text-gray-500 mt-1">{nodeCount} nodes</p>
      )}
    </button>
  );
}
