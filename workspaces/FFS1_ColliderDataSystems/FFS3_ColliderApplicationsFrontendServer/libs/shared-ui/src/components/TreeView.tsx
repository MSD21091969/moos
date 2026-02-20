import { useState } from 'react';
import { getContextTheme } from '../utils/theme';

export interface TreeNode {
  id: string;
  path: string;
  children?: TreeNode[];
  metadata_?: Record<string, any>; // Flexible metadata
  container?: Record<string, any>; // Flexible container
}

export interface TreeViewProps {
  node: TreeNode;
  onSelect?: (node: TreeNode) => void;
  depth?: number;
}

export function TreeView({ node, onSelect, depth = 0 }: TreeViewProps) {
  const [isOpen, setIsOpen] = useState(true); // Default open for demo
  const hasChildren = node.children && node.children.length > 0;
  
  // Determine context from container (defaulting to FILESYST if missing)
  const context = (node.container?.config as any)?.domain || 'FILESYST';
  const theme = getContextTheme(context);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onSelect) onSelect(node);
  };

  const toggleOpen = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(!isOpen);
  };

  const displayName = node.path.split('/').pop() || node.path;

  return (
    <div style={{ marginLeft: depth * 12 }}>
      <div 
        onClick={handleClick}
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '4px 8px',
          cursor: 'pointer',
          borderRadius: '4px',
          color: theme.primary,
          fontWeight: 500,
          backgroundColor: 'transparent',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = theme.bg;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'transparent';
        }}
      >
        {hasChildren && (
          <span 
            onClick={toggleOpen}
            style={{ marginRight: '4px', fontSize: '10px', cursor: 'pointer' }}
          >
            {isOpen ? '▼' : '▶'}
          </span>
        )}
        {!hasChildren && <span style={{ width: '14px' }} />}
        
        <span>{displayName}</span>
        
        {/* Visual indicator for context */}
        {depth === 0 && (
          <span style={{ 
            marginLeft: '8px', 
            fontSize: '10px', 
            border: `1px solid ${theme.border}`,
            padding: '1px 4px',
            borderRadius: '4px',
            color: theme.primary
          }}>
            {context}
          </span>
        )}
      </div>

      {hasChildren && isOpen && (
        <div style={{ borderLeft: `1px solid ${theme.border}30`, marginLeft: '6px' }}>
          {node.children!.map((child) => (
            <TreeView 
              key={child.id} 
              node={child} 
              onSelect={onSelect} 
              depth={depth + 1} 
            />
          ))}
        </div>
      )}
    </div>
  );
}
