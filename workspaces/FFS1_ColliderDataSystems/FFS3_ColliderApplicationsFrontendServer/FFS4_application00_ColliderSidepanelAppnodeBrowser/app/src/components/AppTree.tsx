import { useState } from "react";

export interface AppNodeTree {
  id: string;
  path: string;
  children: AppNodeTree[];
}

interface AppTreeProps {
  tree: AppNodeTree[];
  domain?: string;
  onSelectNode: (path: string) => void;
  selectedPath: string | null;
}

const DOMAIN_COLORS: Record<string, string> = {
  CLOUD: "text-green-500",
  FILESYST: "text-blue-500",
  ADMIN: "text-red-500",
  SIDEPANEL: "text-purple-500",
  AGENT_SEAT: "text-yellow-500",
};

function TreeNode({
  node,
  depth,
  domain,
  onSelectNode,
  selectedPath,
}: {
  node: AppNodeTree;
  depth: number;
  domain: string;
  onSelectNode: (path: string) => void;
  selectedPath: string | null;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children.length > 0;
  const isSelected = node.path === selectedPath;
  const domainColor = DOMAIN_COLORS[domain] ?? "text-gray-400";

  return (
    <div>
      <button
        onClick={() => {
          onSelectNode(node.path);
          if (hasChildren) setExpanded(!expanded);
        }}
        className={`flex items-center gap-1 w-full text-left px-2 py-1 text-sm hover:bg-gray-700 rounded ${isSelected ? "bg-gray-700 font-medium" : ""
          }`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {hasChildren && <span className="text-xs">{expanded ? "▼" : "▶"}</span>}
        <span className={domainColor}>●</span>
        <span className="truncate">
          {node.path === "/" ? "root" : node.path.split("/").pop()}
        </span>
      </button>
      {expanded &&
        hasChildren &&
        node.children.map((child) => (
          <TreeNode
            key={child.id}
            node={child}
            depth={depth + 1}
            domain={domain}
            onSelectNode={onSelectNode}
            selectedPath={selectedPath}
          />
        ))}
    </div>
  );
}

export function AppTree({
  tree,
  domain = "CLOUD",
  onSelectNode,
  selectedPath,
}: AppTreeProps) {
  if (tree.length === 0) {
    return <div className="p-4 text-sm text-gray-500">No nodes found.</div>;
  }

  return (
    <div className="py-1">
      {tree.map((node) => (
        <TreeNode
          key={node.id}
          node={node}
          depth={0}
          domain={domain}
          onSelectNode={onSelectNode}
          selectedPath={selectedPath}
        />
      ))}
    </div>
  );
}
