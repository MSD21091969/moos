import { useEffect, useRef, useState } from 'react'
import { visualFeedback, type NodeHighlight } from '../lib/visual-feedback'
import { useWorkspaceStore } from '../lib/workspace-store'
import type { CustomNode } from '../lib/types'

/**
 * Overlay that shows visual highlights for nodes being operated by AI
 */
export function NodeHighlightOverlay() {
  const [highlights, setHighlights] = useState<NodeHighlight[]>([])
  const { nodes } = useWorkspaceStore()

  useEffect(() => {
    const unsubscribe = visualFeedback.onNodeHighlight((newHighlights) => {
      setHighlights(newHighlights)
    })
    return unsubscribe
  }, [])

  if (highlights.length === 0) return null

  return (
    <div className="pointer-events-none absolute inset-0 z-50">
      {highlights.map((highlight, idx) =>
        highlight.nodeIds.map((nodeId) => {
          const node = nodes.find((n) => n.id === nodeId)
          if (!node) return null
          return (
            <HighlightBubble
              key={`${nodeId}-${idx}`}
              highlight={highlight}
              node={node}
            />
          )
        })
      )}
    </div>
  )
}

interface HighlightBubbleProps {
  highlight: NodeHighlight
  node: CustomNode
}

function HighlightBubble({ highlight, node }: HighlightBubbleProps) {
  const bubbleRef = useRef<HTMLDivElement>(null)
  const labelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!bubbleRef.current) return
    const bubble = bubbleRef.current
    bubble.style.left = `${node.position.x - 10}px`
    bubble.style.top = `${node.position.y - 10}px`
    bubble.style.width = '220px'
    bubble.style.height = '100px'
    bubble.style.borderColor = highlight.color
    bubble.style.boxShadow = `0 0 20px ${highlight.color}80`
    bubble.style.backgroundColor = `${highlight.color}25`
  }, [highlight.color, node.position.x, node.position.y])

  useEffect(() => {
    if (!labelRef.current) return
    labelRef.current.style.backgroundColor = highlight.color
  }, [highlight.color])

  return (
    <div
      ref={bubbleRef}
      className="absolute transition-all duration-300 animate-pulse border-[3px] rounded-xl"
    >
      {highlight.label && (
        <div
          ref={labelRef}
          className="absolute -top-6 left-0 text-xs font-medium px-2 py-1 rounded text-white"
        >
          🤖 {highlight.label}
        </div>
      )}
    </div>
  )
}
