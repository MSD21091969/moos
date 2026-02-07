import { memo, useEffect } from 'react'
import { Handle, Position, NodeProps, Node } from '@xyflow/react'
// import { motion } from 'framer-motion'
import { Folder, Bot, Wrench, Database, User } from 'lucide-react'
import { hexToRgba, statusBadgeClasses } from '../../lib/workspace-theme'
import type { ResourceLinkNodeData } from '../../lib/api'

/**
 * ContainerNode - Unified visual for all container types (Session, Agent, Tool, Source)
 * 
 * V4.1 Architecture: All containers render identically.
 * Data comes from ResourceLink (backend model).
 * 
 * ResourceLink fields used:
 * - title/description → Display name
 * - resource_type → Icon selection
 * - metadata.color → Theme color
 * - metadata.x/y → Position (handled by ReactFlow)
 * - preset_params → Config overrides (for Edit menu)
 * - input_mappings → Data flow (for Edit menu)
 */

// Extended data interface combining ResourceLinkNodeData with legacy session fields
interface ContainerNodeData extends Partial<ResourceLinkNodeData> {
  // Legacy session fields (for demo mode compatibility)
  id?: string
  name?: string
  label?: string
  themeColor?: string
  status?: 'active' | 'idle' | 'working' | 'error'
  depth?: number
  objectCount?: number
  role?: string       // Agent
  category?: string   // Tool
  [key: string]: unknown
}

// Icon mapping by resource type
const iconMap: Record<string, typeof Folder> = {
  session: Folder,
  agent: Bot,
  tool: Wrench,
  source: Database,
  user: User,
}

// Color mapping by resource type (fallback if no themeColor/metadata.color)
const colorMap: Record<string, string> = {
  session: '#3b82f6', // blue
  agent: '#a855f7',   // purple
  tool: '#f59e0b',    // orange
  source: '#10b981',  // emerald
  user: '#ec4899',    // pink
}

export default memo(({ data, selected, type }: NodeProps<Node<ContainerNodeData>>) => {
  console.log('🎨 ContainerNode Render:', data.title, data.resourceType, 'type prop:', type);
  
  useEffect(() => {
    console.log('🎨 ContainerNode MOUNTED:', data.title);
    return () => console.log('🎨 ContainerNode UNMOUNTED:', data.title);
  }, []);

  const nodeData = data as unknown as ContainerNodeData
  
  // Determine resource type (from ResourceLink or node type)
  const resourceType = nodeData.resourceType || type || 'session'
  
  // Normalize title from different data shapes
  // Priority: ResourceLink.title > description > label > legacy name > id
  const title = nodeData.title || nodeData.description || nodeData.label || nodeData.name || nodeData.resourceId || 'Untitled'
  
  // Normalize subtitle based on resource type
  // For ResourceLink: use preset_params or resource type
  // For legacy: use role/category
  const subtitle = resourceType === 'agent' ? (nodeData.role || nodeData.presetParams?.role as string)
    : resourceType === 'tool' ? (nodeData.category || nodeData.presetParams?.category as string)
    : resourceType === 'source' ? (nodeData.presetParams?.source_type as string || 'data')
    : resourceType === 'user' ? (nodeData.presetParams?.role as string || 'member')
    : undefined
  
  // Get theme color (priority: legacy themeColor > metadata.color > resourceType default)
  const metadataColor = (nodeData.metadata as Record<string, unknown>)?.color as string | undefined
  const themeColor = nodeData.themeColor || metadataColor || colorMap[resourceType] || '#3b82f6'
  
  // Get icon based on resource type
  const Icon = iconMap[resourceType] || Folder
  
  // Status (only for sessions/agents)
  const status = nodeData.status || 'active'
  
  // Child count (for sessions at L0)
  const objectCount = nodeData.objectCount
  
  // Depth badge (for sessions at L0)
  const depth = nodeData.depth
  
  // Enabled state (from ResourceLink)
  const enabled = nodeData.enabled !== false

  // Compute colors
  const bgColor = hexToRgba(themeColor, 0.08)
  const borderColor = selected ? '#60a5fa' : themeColor

  console.log('🎨 ContainerNode Rendering JSX:', title, resourceType);

  return (
    <div
      data-testid={`node-${resourceType}`}
      className="relative rounded-lg cursor-pointer transition-all"
      style={{
        backgroundColor: bgColor,
        border: `2px solid ${borderColor}`,
        opacity: enabled ? 1 : 0.5,
        boxShadow: selected 
          ? '0 0 0 4px rgba(96, 165, 250, 0.5), 0 10px 25px -5px rgba(0, 0, 0, 0.3)'
          : '0 10px 25px -5px rgba(0, 0, 0, 0.2)',
        width: '200px',
        minHeight: '80px',
      }}
    >
      {/* Header */}
      <div 
        className="flex items-center gap-2 p-3"
        style={{ backgroundColor: hexToRgba(themeColor, 0.12), borderRadius: '6px 6px 0 0' }}
      >
        <Icon className="w-5 h-5 flex-shrink-0" style={{ color: themeColor }} />
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white truncate">{title}</h3>
          {subtitle && (
            <p className="text-xs text-slate-400 truncate">{subtitle}</p>
          )}
        </div>
      </div>

      {/* Footer badges */}
      <div className="flex items-center justify-between px-3 py-2">
        <div className="flex items-center gap-1">
          <div className={`w-2 h-2 rounded-full ${statusBadgeClasses[status] || 'bg-slate-500'}`} />
        </div>
        <div className="flex items-center gap-1.5">
          {objectCount !== undefined && objectCount > 0 && (
            <span 
              className="text-xs font-medium text-slate-300 bg-slate-700/50 px-2 py-0.5 rounded" 
              title={`${objectCount} objects`}
            >
              {objectCount}
            </span>
          )}
          {depth !== undefined && depth > 0 && (
            <span 
              className="text-xs font-bold text-blue-300 bg-blue-900/30 px-1.5 py-0.5 rounded" 
              data-testid="depth-badge" 
              title={`Depth L${depth}`}
            >
              L{depth}
            </span>
          )}
        </div>
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
    </div>
  )
})
