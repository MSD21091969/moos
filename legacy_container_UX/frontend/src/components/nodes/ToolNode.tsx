import { memo } from 'react'
import { Handle, Position, NodeProps, NodeToolbar } from '@xyflow/react'
import { motion } from 'framer-motion'
import { Wrench, Trash2 } from 'lucide-react'
import { ToolNodeData } from '../../lib/types'
import { useWorkspaceStore } from '../../lib/workspace-store'

export default memo(function ToolNode({ id, data, selected }: NodeProps) {
  // Use flat data structure
  const { name, category } = data as unknown as ToolNodeData;
  const { removeResourceLink, activeContainerId } = useWorkspaceStore()

  const handleDelete = () => {
    if (activeContainerId) removeResourceLink(activeContainerId, id);
  }

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
        data-testid="node-tool"
        className={`
          bg-slate-800 border border-orange-500/50 rounded p-3 min-w-[140px]
          ${selected ? 'ring-2 ring-orange-500' : ''}
          hover:border-orange-500 transition-colors
        `}
      >
        <div className="flex items-center gap-2">
          <Wrench className="w-4 h-4 text-orange-400" />
          <div>
            <p className="text-xs font-medium text-white truncate">{name}</p>
            <p className="text-[10px] text-slate-400">{category}</p>
          </div>
        </div>

        <Handle
          type="target"
          position={Position.Left}
          className="w-2 h-2 bg-orange-500"
        />
        <Handle
          type="source"
          position={Position.Right}
          className="w-2 h-2 bg-orange-500"
        />
      </motion.div>
    </>
  )
})
