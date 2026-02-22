import React, { useState } from "react";
import type { AppNodeTree } from "~/types";

interface AppTreeProps {
  tree: AppNodeTree[];
  domain: string;
  onSelectNode: (path: string) => void;
  selectedPath: string | null;
}

function TreeNode({
  node,
  depth,
  onSelectNode,
  selectedPath,
}: {
  node: AppNodeTree;
  depth: number;
  onSelectNode: (path: string) => void;
  selectedPath: string | null;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedPath === node.path;
  const label = node.path.split("/").pop() || node.path;

  return (
    <div>
      <div
        className={`flex items-center gap-1 px-2 py-1 cursor-pointer text-xs hover:bg-gray-700 ${isSelected ? "bg-gray-700 text-white" : "text-gray-300"
          }`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => {
          onSelectNode(node.path);
          if (hasChildren) setExpanded(!expanded);
        }}
      >
        {hasChildren ? (
          <span className="w-3 text-gray-500">{expanded ? "▾" : "▸"}</span>
        ) : (
          <span className="w-3 text-gray-600">·</span>
        )}
        <span className="truncate">{label}</span>
      </div>
      {expanded &&
        hasChildren &&
        node.children.map((child) => (
          <TreeNode
            key={child.id}
            node={child}
            depth={depth + 1}
            onSelectNode={onSelectNode}
            selectedPath={selectedPath}
          />
        ))}
    </div>
  );
}

export function AppTree({ tree, domain, onSelectNode, selectedPath }: AppTreeProps) {
  if (!tree || tree.length === 0) {
    return (
      <div className="p-3 text-xs text-gray-500">No nodes found.</div>
    );
  }

  return (
    <div className="py-1">
      <div className="px-3 py-1 text-[10px] uppercase text-gray-500 tracking-wider">
        {domain}
      </div>
      {tree.map((node) => (
        <TreeNode
          key={node.id}
          node={node}
          depth={0}
          onSelectNode={onSelectNode}
          selectedPath={selectedPath}
        />
      ))}
    </div>
  );
}
