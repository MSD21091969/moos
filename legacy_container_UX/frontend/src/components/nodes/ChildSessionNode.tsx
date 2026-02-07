import { Handle, NodeProps, Position } from '@xyflow/react';
import { motion } from 'framer-motion';
import { useEffect, useRef } from 'react';
import { Layers } from 'lucide-react';
import { SessionVisualState } from '../../lib/types';
import { hexToRgba, statusBadgeClasses } from '../../lib/workspace-theme';
import { useWorkspaceStore } from '../../lib/workspace-store';

interface ChildSessionNodeData extends SessionVisualState {
  depth?: number;
  objectCount?: number;
}

export default function ChildSessionNode({ data, selected, id }: NodeProps) {
  const sessionData = data as unknown as ChildSessionNodeData;
  const {
    title = 'Untitled Session',
    themeColor = '#8b5cf6', // Default purple for child sessions
    status = 'active',
    expanded = true,
    depth: passedDepth,
    objectCount,
  } = sessionData || {};

  const { containers } = useWorkspaceStore();
  const cardRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);

  // Calculate depth - use passed prop if available, otherwise calculate from store
  const calculateDepth = (sessionId: string): number => {
    let depth = 0;
    let current = containers.find(s => s.id === sessionId);
    while (current?.parent_id) {
      depth++;
      current = containers.find(s => s.id === current!.parent_id);
    }
    return depth;
  };

  // Prefer passed depth prop (more reliable), fallback to calculated
  const depth = passedDepth !== undefined ? passedDepth : calculateDepth(id);

  // Convert hex color to rgba with opacity
  const bgColor = hexToRgba(themeColor, 0.06)
  const headerBgColor = hexToRgba(themeColor, 0.12)

  useEffect(() => {
    if (!cardRef.current) return;
    const card = cardRef.current;
    card.style.setProperty('--session-border-color', selected ? '#60a5fa' : themeColor);
    card.style.setProperty('--session-bg-color', bgColor);
    card.style.setProperty(
      '--session-shadow',
      selected
        ? '0 0 0 4px rgba(96, 165, 250, 0.5), 0 25px 50px -12px rgba(0, 0, 0, 0.5)'
        : '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
    );
    // Child sessions are slightly smaller
    card.style.setProperty('--session-width', expanded ? '280px' : '200px');
    card.style.setProperty('--session-height', expanded ? '180px' : '100px');
  }, [bgColor, expanded, selected, themeColor]);

  useEffect(() => {
    if (!headerRef.current) return;
    headerRef.current.style.setProperty('--session-header-bg', headerBgColor);
  }, [headerBgColor]);

  return (
    <>
      <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        ref={cardRef}
        data-selected={selected ? 'true' : 'false'}
        className="relative rounded-lg cursor-pointer transition-all border-2 session-node-card"
      >
        <div className="pointer-events-none">
          {/* Header */}
          <div
            ref={headerRef}
            className="flex items-center justify-between p-3 rounded-t-lg pointer-events-none session-node-header"
          >
            <div
              className="flex items-center gap-2 pointer-events-auto"
              title={`Child Session (Level ${depth})`}
            >
              <div className={`w-2 h-2 rounded-full ${statusBadgeClasses[status]}`} />
              <h3 className="text-sm font-semibold text-white truncate max-w-[140px]">{title}</h3>
            </div>
            
            {/* Count & Depth Badges */}
            <div className="flex items-center gap-1.5">
              {objectCount !== undefined && objectCount > 0 && (
                <span className="text-xs font-medium text-slate-300 bg-slate-700/50 px-1.5 py-0.5 rounded" title={`${objectCount} objects`}>
                  {objectCount}
                </span>
              )}
              <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-800/50 border border-slate-700/50">
                <Layers className="w-3 h-3 text-slate-400" />
                <span className="text-[10px] font-mono text-slate-400" data-testid="depth-badge">L{depth}</span>
              </div>
            </div>
          </div>

          {/* Content */}
          {expanded && (
            <div className="p-3 pointer-events-none">
              <div className="text-xs text-slate-400 line-clamp-3">
                {sessionData.description || 'No description'}
              </div>
            </div>
          )}
        </div>
        {/* Handles */}
        <Handle
          type="target"
          position={Position.Top}
          className="w-3 h-3 border-2"
          style={{ borderColor: themeColor, backgroundColor: 'white' }}
        />
        <Handle
          type="source"
          position={Position.Bottom}
          className="w-3 h-3 border-2"
          style={{ borderColor: themeColor, backgroundColor: 'white' }}
        />
      </motion.div>
    </>
  );
}
