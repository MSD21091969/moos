import { memo } from 'react'
import { Handle, Position, NodeProps, NodeToolbar } from '@xyflow/react'
import { motion } from 'framer-motion'
import { FileText, Database, FileCode, Trash2 } from 'lucide-react'
import { ObjectNodeData } from '../../lib/types'
import { useWorkspaceStore } from '../../lib/workspace-store'

export default memo(function ObjectNode({ id, data, selected }: NodeProps) {
  // Use flat data structure
  const { label, type, fileType } = data as unknown as ObjectNodeData;
  const { removeResourceLink, activeContainerId } = useWorkspaceStore()

  const handleDelete = () => {
    if (activeContainerId) removeResourceLink(activeContainerId, id);
  }

  const icons = {
    document: FileText,
    data: Database,
    result: FileCode,
  }

  const Icon = icons[type as keyof typeof icons] || FileText

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
        className={`
          bg-slate-800 border border-slate-600 rounded-md p-3 min-w-[140px]
          ${selected ? 'ring-2 ring-blue-500' : ''}
          hover:border-slate-500 transition-colors
        `}
      >
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-blue-400" />
          <div>
            <p className="text-xs font-medium text-white truncate">{label}</p>
            {fileType && <p className="text-[10px] text-slate-400">{fileType}</p>}
          </div>
        </div>

        <Handle type="target" position={Position.Left} className="w-2 h-2" />
        <Handle type="source" position={Position.Right} className="w-2 h-2" />
      </motion.div>
    </>
  )
})
