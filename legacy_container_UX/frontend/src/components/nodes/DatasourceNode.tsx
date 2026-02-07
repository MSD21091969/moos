/**
 * DatasourceNode - Represents a data source inside a session
 * Datasources are attached to sessions via their IDs stored in sessionDatasources
 */

import { Database } from 'lucide-react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

export interface DatasourceNodeData {
  datasourceId: string;
  datasourceName: string;
  datasourceType?: 'api' | 'database' | 'file' | 'custom';
  description?: string;
  connectionStatus?: 'connected' | 'disconnected' | 'error';
}

export function DatasourceNode({ data, selected }: NodeProps) {
  const nodeData = data as unknown as DatasourceNodeData;
  const statusColors = {
    connected: 'bg-green-100 text-green-700 dark:bg-green-800 dark:text-green-300',
    disconnected: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    error: 'bg-red-100 text-red-700 dark:bg-red-800 dark:text-red-300',
  };

  return (
    <div
      className={`p-4 rounded-lg shadow-lg border-2 transition-all
        ${selected ? 'border-blue-400 ring-2 ring-blue-200' : 'border-blue-500'} 
        min-w-[180px] bg-blue-50 dark:bg-blue-900/20`}
    >
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      
      <div className="flex items-start gap-3">
        <div className="p-2 bg-blue-100 dark:bg-blue-800/50 rounded">
          <Database className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm text-slate-900 dark:text-white truncate">
            {nodeData.datasourceName}
          </h3>
          {nodeData.description && (
            <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 mt-1">
              {nodeData.description}
            </p>
          )}
          <div className="flex gap-2 mt-2">
            {nodeData.datasourceType && (
              <span className="inline-block px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-800 
                text-blue-700 dark:text-blue-300 rounded">
                {nodeData.datasourceType}
              </span>
            )}
            {nodeData.connectionStatus && (
              <span className={`inline-block px-2 py-0.5 text-xs rounded ${statusColors[nodeData.connectionStatus]}`}>
                {nodeData.connectionStatus}
              </span>
            )}
          </div>
        </div>
      </div>
      
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}
