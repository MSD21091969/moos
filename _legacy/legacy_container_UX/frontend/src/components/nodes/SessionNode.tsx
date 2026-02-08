import { Handle, NodeProps, Position } from '@xyflow/react';
import { motion } from 'framer-motion';
import { useEffect, useRef } from 'react';
import { SessionVisualState } from '../../lib/types';
import { hexToRgba, statusBadgeClasses } from '../../lib/workspace-theme';

interface SessionNodeData extends SessionVisualState {
  depth?: number;
  objectCount?: number;
}

export default function SessionNode({ data, selected }: NodeProps) {
  const sessionData = data as unknown as SessionNodeData;
  const {
    title = 'Untitled Session',
    themeColor = '#3b82f6',
    status = 'active',
    expanded = true,
    depth,
    objectCount,
  } = sessionData || {};

  const cardRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);

  // Convert hex color to rgba with opacity (use centralized function)
  const bgColor = hexToRgba(themeColor, 0.06);
  const headerBgColor = hexToRgba(themeColor, 0.12);

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
    card.style.setProperty('--session-width', expanded ? '320px' : '240px');
    card.style.setProperty('--session-height', expanded ? '200px' : '120px');
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
              title="Session"
            >
              <div className={`w-2 h-2 rounded-full ${statusBadgeClasses[status]}`} />
              <h3 className="text-sm font-semibold text-white truncate">{title}</h3>
            </div>
            <div className="flex items-center gap-1.5">
              {objectCount !== undefined && objectCount > 0 && (
                <span className="text-xs font-medium text-slate-300 bg-slate-700/50 px-2 py-0.5 rounded" title={`${objectCount} objects`}>
                  {objectCount}
                </span>
              )}
              {depth !== undefined && depth > 0 && (
                <span className="text-xs font-bold text-blue-300 bg-blue-900/30 px-1.5 py-0.5 rounded" data-testid="depth-badge" title={`Depth L${depth}`}>
                  L{depth}
                </span>
              )}
            </div>
          </div>

          {/* Content */}
          {expanded && (
            <div className="p-3 pointer-events-none">
              {/* Badges removed - actual tool/agent nodes now visible on canvas */}
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
