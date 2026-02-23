/**
 * NodeCard — Custom XYFlow node for workspace graph
 *
 * Renders a Collider node with:
 * - Context selection checkbox
 * - Domain-colored badge
 * - Skill/tool counts
 * - Container indicator
 */

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { NodeData } from "../../stores/graphStore";
import { useContextStore } from "../../stores/contextStore";

const DOMAIN_COLORS: Record<string, string> = {
  FILESYST: "#10b981",
  ADMIN: "#ef4444",
  CLOUD: "#3b82f6",
  DATA: "#8b5cf6",
  AI: "#f59e0b",
  DEV: "#06b6d4",
};

function NodeCardComponent({ data, id }: NodeProps) {
  const nodeData = data as unknown as NodeData;
  const toggleNode = useContextStore((s) => s.toggleNode);
  const color = DOMAIN_COLORS[nodeData.domain ?? ""] ?? "#6b7280";

  return (
    <div
      style={{
        padding: "8px 12px",
        borderRadius: 8,
        border: `2px solid ${nodeData.isSelected ? color : "#e5e7eb"}`,
        background: nodeData.isSelected ? `${color}10` : "#fff",
        minWidth: 200,
        fontFamily: "system-ui, sans-serif",
        fontSize: 12,
      }}
    >
      <Handle type="target" position={Position.Top} />

      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <input
          type="checkbox"
          checked={nodeData.isSelected}
          onChange={() => toggleNode(id)}
          style={{ cursor: "pointer" }}
        />
        <span
          style={{
            fontWeight: 600,
            flex: 1,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {nodeData.emoji ? `${nodeData.emoji} ` : ""}
          {nodeData.label}
        </span>
        {nodeData.domain && (
          <span
            style={{
              fontSize: 9,
              padding: "1px 5px",
              borderRadius: 4,
              background: color,
              color: "#fff",
              fontWeight: 500,
            }}
          >
            {nodeData.domain}
          </span>
        )}
      </div>

      {nodeData.hasContainer && (
        <div
          style={{
            marginTop: 4,
            display: "flex",
            gap: 8,
            color: "#6b7280",
            fontSize: 10,
          }}
        >
          {nodeData.skillCount > 0 && <span>{nodeData.skillCount} skills</span>}
          {nodeData.toolCount > 0 && <span>{nodeData.toolCount} tools</span>}
          {!nodeData.skillCount && !nodeData.toolCount && <span>container</span>}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export const NodeCard = memo(NodeCardComponent);
