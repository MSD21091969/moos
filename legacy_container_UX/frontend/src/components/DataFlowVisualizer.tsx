import { useMemo, useEffect, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  Position,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
// LEGACY: api-backend.ts deleted - using stubs (V4.1 will use Source containers)
interface DocumentResponse { 
  document_id: string; 
  filename: string; 
  mime_type: string; 
  size_bytes: number;
  metadata?: { onedrive_item_id?: string };
}
const getSessionDocuments = async (_sessionId: string) => ({ documents: [] as DocumentResponse[] });

import { toast } from '../lib/toast-store';

interface DataFlowVisualizerProps {
  sessionId: string;
}

export function DataFlowVisualizer({ sessionId }: DataFlowVisualizerProps) {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDocuments();
  }, [sessionId]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const response = await getSessionDocuments(sessionId);
      setDocuments(response.documents);
    } catch (error) {
      console.error('Failed to load documents:', error);
      toast.error('Failed to load data flow');
    } finally {
      setLoading(false);
    }
  };

  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Group Nodes
    nodes.push({
      id: 'backend-storage',
      type: 'group',
      position: { x: 50, y: 50 },
      style: {
        width: 300,
        height: Math.max(400, documents.length * 100 + 100),
        backgroundColor: 'rgba(240, 240, 240, 0.5)',
        border: '1px dashed #ccc',
        borderRadius: 8,
      },
      data: { label: 'Backend Storage (Firestore)' },
    });

    nodes.push({
      id: 'onedrive-storage',
      type: 'group',
      position: { x: 500, y: 50 },
      style: {
        width: 300,
        height: Math.max(400, documents.length * 100 + 100),
        backgroundColor: 'rgba(235, 245, 255, 0.5)',
        border: '1px dashed #3b82f6',
        borderRadius: 8,
      },
      data: { label: 'OneDrive (Microsoft 365)' },
    });

    // File Nodes
    documents.forEach((doc, index) => {
      const yPos = 60 + index * 100;
      const isCheckedOut = !!doc.metadata?.onedrive_item_id;

      // Backend Node
      const backendNodeId = `backend-${doc.document_id}`;
      nodes.push({
        id: backendNodeId,
        position: { x: 20, y: yPos },
        data: { label: doc.filename },
        parentId: 'backend-storage',
        extent: 'parent',
        style: {
          backgroundColor: '#fff',
          border: '1px solid #777',
          borderRadius: 4,
          padding: 10,
          width: 260,
        },
        sourcePosition: Position.Right,
      });

      if (isCheckedOut) {
        // OneDrive Node
        const onedriveNodeId = `onedrive-${doc.document_id}`;
        nodes.push({
          id: onedriveNodeId,
          position: { x: 20, y: yPos },
          data: { label: `${doc.filename} (Editing)` },
          parentId: 'onedrive-storage',
          extent: 'parent',
          style: {
            backgroundColor: '#eff6ff',
            border: '1px solid #3b82f6',
            borderRadius: 4,
            padding: 10,
            width: 260,
          },
          targetPosition: Position.Left,
        });

        // Edge
        edges.push({
          id: `edge-${doc.document_id}`,
          source: backendNodeId,
          target: onedriveNodeId,
          label: 'Checked Out',
          animated: true,
          style: { stroke: '#3b82f6' },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#3b82f6',
          },
        });
      }
    });

    return { nodes, edges };
  }, [documents]);

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading visualization...</div>;
  }

  return (
    <div className="h-full w-full bg-slate-900 rounded-lg border border-slate-700">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        attributionPosition="bottom-right"
      >
        <Background color="#334155" gap={16} />
        <Controls className="bg-slate-800 border-slate-700 fill-white text-white" />
      </ReactFlow>
    </div>
  );
}
