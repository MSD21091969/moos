import { NodeProps, Handle, Position } from '@xyflow/react';
import { Bot, Database, FileText, Folder, Wrench, Layers } from 'lucide-react';
import { memo, createElement } from 'react';

const getIcon = (type: string) => {
  switch (type) {
    case 'session':
      return Folder;
    case 'agent':
      return Bot;
    case 'tool':
      return Wrench;
    case 'datasource':
      return Database;
    case 'object':
      return FileText;
    default:
      return Layers;
  }
};

const getColor = (type: string) => {
  switch (type) {
    case 'session':
      return 'text-purple-400 bg-purple-400/10 border-purple-400/20';
    case 'agent':
      return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
    case 'tool':
      return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
    default:
      return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
  }
};

function PreviewNode({ data }: NodeProps) {
  const originalType = (data.originalType as string) || 'object';
  const label = (data.label as string) || 'Unknown';
  const count = (data.count as number) || 0;
  
  // Get icon for the original type
  const colorClass = getColor(originalType);

  return (
    <div className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded-md border ${colorClass} min-w-[120px] max-w-[150px] backdrop-blur-sm`}>
      <div className="flex items-center gap-2">
        {createElement(getIcon(originalType), { className: "w-3 h-3 flex-shrink-0" })}
        <span className="text-xs font-medium truncate text-slate-200">{label}</span>
      </div>
      {count > 0 && (
        <span className="text-xs font-bold text-slate-100 bg-slate-700/50 px-1.5 py-0.5 rounded">
          {count}
        </span>
      )}
      
      {/* Hidden handles to satisfy ReactFlow if needed, though these aren't connected */}
      <Handle type="target" position={Position.Top} className="opacity-0" />
      <Handle type="source" position={Position.Bottom} className="opacity-0" />
    </div>
  );
}

export default memo(PreviewNode);
