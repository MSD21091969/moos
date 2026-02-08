import { memo } from 'react'
import { Handle, Position, NodeProps, NodeToolbar } from '@xyflow/react'
import { motion } from 'framer-motion'
import { Bot, Loader2, Trash2 } from 'lucide-react'
import { AgentNodeData } from '../../lib/types'
import { useWorkspaceStore } from '../../lib/workspace-store'

export default memo(function AgentNode({ id, data, selected }: NodeProps) {
  // Use flat data structure
  const { name, role, status } = data as unknown as AgentNodeData;
  const { removeResourceLink, activeContainerId } = useWorkspaceStore()

  const handleDelete = () => {
    if (activeContainerId) removeResourceLink(activeContainerId, id);
  }

  const statusConfig = {
    idle: { color: 'text-gray-400', bg: 'bg-gray-500/20', icon: null },
    working: { color: 'text-green-400', bg: 'bg-green-500/20', icon: Loader2 },
    error: { color: 'text-red-400', bg: 'bg-red-500/20', icon: null },
  }

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.idle
  const StatusIcon = config?.icon

  return (
    <>
      {selected && (
        <NodeToolbar position={Position.Top}>
          {/* <button
            onClick={() => duplicateNode(id!)}
            className="p-2 bg-slate-700 hover:bg-slate-600 text-slate-200 hover:text-white rounded transition-colors flex items-center gap-1"
            title="Duplicate node"
          >
            <Copy className="w-4 h-4" />
          </button>
          <button
            onClick={() => editNode(id!)}
            className="p-2 bg-slate-700 hover:bg-slate-600 text-slate-200 hover:text-white rounded transition-colors flex items-center gap-1"
            title="Edit node"
          >
            <Edit2 className="w-4 h-4" />
          </button> */}
          <button
            onClick={handleDelete}
            className="p-2 bg-slate-700 hover:bg-red-600 text-slate-200 hover:text-red-100 rounded transition-colors flex items-center gap-1"
            title="Delete node"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </NodeToolbar>
      )}
      <motion.div
        whileDrag={{ scale: 1.1, boxShadow: '0px 10px 20px rgba(0,0,0,0.3)' }}
        data-testid="node-agent"
        className={`
          bg-slate-800 border-2 border-purple-500/50 rounded-lg p-3 min-w-[160px]
          ${selected ? 'ring-2 ring-purple-500' : ''}
          ${config.bg}
        `}
      >
        <div className="flex items-start gap-2">
          <Bot className="w-5 h-5 text-purple-400 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-white">{name}</p>
            <p className="text-xs text-slate-400">{role}</p>
            
            {StatusIcon && (
              <div className="flex items-center gap-1 mt-1">
                <StatusIcon className={`w-3 h-3 ${config.color} animate-spin`} />
                <span className={`text-[10px] ${config.color}`}>Working...</span>
              </div>
            )}
          </div>
        </div>

        <Handle type="target" position={Position.Top} className="w-2 h-2 bg-purple-500" />
        <Handle type="source" position={Position.Bottom} className="w-2 h-2 bg-purple-500" />
      </motion.div>
    </>
  )
})
