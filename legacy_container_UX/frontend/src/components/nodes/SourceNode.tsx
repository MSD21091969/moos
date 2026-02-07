import { memo } from 'react'
import { Handle, Position, NodeProps, NodeToolbar } from '@xyflow/react'
import { motion } from 'framer-motion'
import { Database, Trash2 } from 'lucide-react'
import { useWorkspaceStore } from '../../lib/workspace-store'
import type { ResourceLinkNodeData } from '../../lib/api'

/**
 * SourceNode - V4.1 Source ResourceLink node
 * 
 * Renders data sources (files, APIs, databases) on the canvas.
 * Position and metadata come from ResourceLink.metadata.
 */
export default memo(function SourceNode({ id, data, selected }: NodeProps) {
  const nodeData = data as unknown as ResourceLinkNodeData
  const { removeResourceLink, activeContainerId } = useWorkspaceStore()

  const handleDelete = () => {
    if (activeContainerId) removeResourceLink(activeContainerId, id);
  }

  const title = nodeData.title || nodeData.resourceId || 'Source'
  const sourceType = nodeData.presetParams?.source_type as string || 'data'

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
        data-testid="node-source"
        className={`
          bg-slate-800 border border-emerald-500/50 rounded p-3 min-w-[140px]
          ${selected ? 'ring-2 ring-emerald-500' : ''}
          ${!nodeData.enabled ? 'opacity-50' : ''}
          hover:border-emerald-500 transition-colors
        `}
      >
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400" />
          <div>
            <p className="text-xs font-medium text-white truncate max-w-[120px]">{title}</p>
            <p className="text-[10px] text-slate-400">{sourceType}</p>
          </div>
        </div>

        {/* Source nodes only have output handles (they provide data) */}
        <Handle
          type="source"
          position={Position.Right}
          className="w-2 h-2 bg-emerald-500"
        />
      </motion.div>
    </>
  )
})
