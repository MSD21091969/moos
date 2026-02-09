export interface TreeNode {
  id: string;
  path: string;
  children: TreeNode[];
}

export interface TreeViewProps {
  nodes: TreeNode[];
  depth?: number;
}

export function TreeView({ nodes, depth = 0 }: TreeViewProps) {
  return (
    <div>
      {nodes.map((node) => (
        <div key={node.id}>
          <div
            className="flex items-center gap-2 py-1.5 px-2 hover:bg-gray-800 rounded text-sm"
            style={{ paddingLeft: `${depth * 20 + 8}px` }}
          >
            {node.children.length > 0 && (
              <span className="text-gray-500 text-xs">&#9660;</span>
            )}
            <span className="font-mono text-gray-300">
              {node.path === "/" ? "/" : node.path.split("/").pop()}
            </span>
            <span className="text-xs text-gray-600 ml-auto font-mono">
              {node.id.slice(0, 8)}
            </span>
          </div>
          {node.children.length > 0 && (
            <TreeView nodes={node.children} depth={depth + 1} />
          )}
        </div>
      ))}
    </div>
  );
}
