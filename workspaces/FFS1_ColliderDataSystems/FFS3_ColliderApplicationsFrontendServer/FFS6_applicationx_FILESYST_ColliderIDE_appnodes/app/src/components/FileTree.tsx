import { useState } from 'react';

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
}

interface FileTreeProps {
  files: FileNode[];
  depth?: number;
}

function FileTreeNode({ node, depth }: { node: FileNode; depth: number }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const isDirectory = node.type === 'directory';
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div>
      <button
        onClick={() => isDirectory && setExpanded(!expanded)}
        className="flex items-center gap-1 w-full text-left px-2 py-1 text-sm hover:bg-blue-900/30 rounded"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {isDirectory && <span className="text-xs">{expanded ? '▼' : '▶'}</span>}
        <span className="text-blue-400">{isDirectory ? '📁' : '📄'}</span>
        <span className="truncate">{node.name}</span>
      </button>
      {expanded && hasChildren && (
        <div>
          {node.children?.map((child, i) => (
            <FileTreeNode key={i} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function FileTree({ files, depth = 0 }: FileTreeProps) {
  if (!files || files.length === 0) {
    return <div className="p-4 text-sm text-gray-500">No files found.</div>;
  }

  return (
    <div className="py-1">
      {files.map((node, i) => (
        <FileTreeNode key={i} node={node} depth={depth} />
      ))}
    </div>
  );
}
