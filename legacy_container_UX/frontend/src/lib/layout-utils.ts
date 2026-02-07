import { Node } from '@xyflow/react';

/**
 * Calculates the position for a node in a grid layout.
 * Used for positioning preview nodes inside a session.
 * 
 * @param index Index of the item in the list
 * @param startX Starting X offset (default: 20)
 * @param startY Starting Y offset (default: 50)
 * @param colWidth Width of each column (default: 60)
 * @param rowHeight Height of each row (default: 40)
 * @param cols Number of columns (default: 2)
 */
export function calculateGridPosition(
  index: number, 
  startX: number = 40, 
  startY: number = 60, 
  colWidth: number = 100, 
  rowHeight: number = 50,
  cols: number = 3
) {
  const col = index % cols;
  const row = Math.floor(index / cols);
  return {
    x: startX + col * colWidth,
    y: startY + row * rowHeight,
  };
}

/**
 * Groups nodes by their parent session ID for preview rendering.
 * 
 * @param nodes All nodes in the workspace
 * @param maxItemsPerSession Maximum number of preview items to show per session
 */
export function groupNodesBySession(nodes: Node[], maxItemsPerSession: number = 5) {
  const objectsBySession: Record<string, Node[]> = {};
  
  nodes.forEach((node) => {
    const data = node.data as any;
    
    // Include child sessions that have a parentSessionId
    if (node.type === 'session' && data?.parentSessionId) {
      const parentId = data.parentSessionId;
      if (!objectsBySession[parentId]) objectsBySession[parentId] = [];
      if (objectsBySession[parentId].length < maxItemsPerSession) {
        objectsBySession[parentId].push(node);
      }
    }
    // Include regular objects (agents, tools, datasources)
    else if (node.type !== 'session' && data?.sessionId) {
      const sid = data.sessionId;
      if (!objectsBySession[sid]) objectsBySession[sid] = [];
      if (objectsBySession[sid].length < maxItemsPerSession) {
        objectsBySession[sid].push(node);
      }
    }
  });
  
  return objectsBySession;
}

/**
 * Groups nodes by type and counts them per session.
 * Returns type summaries instead of individual nodes.
 * Used for showing type count cards in workspace view.
 * 
 * @param nodes All nodes in the workspace
 * @returns Record of sessionId -> type -> count
 */
export function groupNodesByTypePerSession(nodes: Node[]) {
  const typeCountsBySession: Record<string, Record<string, number>> = {};
  
  nodes.forEach((node) => {
    const data = node.data as any;
    
    // Count child sessions
    if (node.type === 'session' && data?.parentSessionId) {
      const parentId = data.parentSessionId;
      if (!typeCountsBySession[parentId]) typeCountsBySession[parentId] = {};
      typeCountsBySession[parentId]['session'] = (typeCountsBySession[parentId]['session'] || 0) + 1;
    }
    // Count regular objects by type
    else if (node.type !== 'session' && data?.sessionId) {
      const sid = data.sessionId;
      const nodeType = node.type || 'object';
      if (!typeCountsBySession[sid]) typeCountsBySession[sid] = {};
      typeCountsBySession[sid][nodeType] = (typeCountsBySession[sid][nodeType] || 0) + 1;
    }
  });
  
  return typeCountsBySession;
}
