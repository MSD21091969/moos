import { memo, useCallback, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, Trash2, CheckCircle2, Clock, FileSpreadsheet } from 'lucide-react'
import { useWorkspaceStore } from '../lib/workspace-store'
import { uploadFileToOneDrive } from '../lib/onedrive-storage'
import { getCurrentUser } from '../lib/microsoft-auth'

export const StagingQueuePanel = memo(function StagingQueuePanel() {
  const stagedOperations = useWorkspaceStore(state => state.stagedOperations || [])
  const removeStagedOperation = useWorkspaceStore(state => state.removeStagedOperation)
  const executeStagedOperations = useWorkspaceStore(state => state.executeStagedOperations)
  const [exporting, setExporting] = useState(false)

  const handleRemove = useCallback((id: string) => {
    removeStagedOperation?.(id)
  }, [removeStagedOperation])

  const handleExecuteAll = useCallback(async () => {
    await executeStagedOperations?.()
  }, [executeStagedOperations])

  const handleExportToExcel = async () => {
    if (!getCurrentUser()) {
      alert('Please sign in with Microsoft first!');
      return;
    }

    setExporting(true);
    try {
      // Create a simple CSV from operations
      const headers = ['ID', 'Type', 'Status', 'Title', 'Description', 'Timestamp'];
      const rows = stagedOperations.map(op => [
        op.id,
        op.type,
        op.status,
        op.title,
        op.description,
        new Date(op.timestamp).toISOString()
      ]);
      
      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
      ].join('\n');

      const fileName = `collider-operations-${new Date().toISOString().split('T')[0]}.csv`;
      const webUrl = await uploadFileToOneDrive(fileName, csvContent, 'text/csv');
      
      // Open in Excel Online (or default CSV viewer)
      window.open(webUrl, '_blank');
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export to Excel. See console for details.');
    } finally {
      setExporting(false);
    }
  };

  if (!stagedOperations || stagedOperations.length === 0) {
    return null
  }

  const pendingCount = stagedOperations.filter(op => op.status === 'pending').length

  return (
    <motion.div
      initial={{ x: 300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 300, opacity: 0 }}
      className="absolute top-4 right-4 w-80 bg-[rgba(15,23,42,0.95)] backdrop-blur-sm border border-slate-700 rounded-lg shadow-2xl z-50"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-blue-400" />
          <h3 className="text-sm font-semibold text-white">Staging Queue</h3>
          <span className="px-2 py-0.5 text-xs font-medium bg-blue-600 text-white rounded-full">
            {pendingCount}
          </span>
        </div>
        <div className="flex gap-2">
          {/* Excel Export Button */}
          <button
            onClick={handleExportToExcel}
            disabled={exporting}
            className="p-1.5 text-green-400 hover:bg-green-900/30 rounded transition-colors disabled:opacity-50"
            title="Export to Excel Online"
          >
            <FileSpreadsheet className="w-4 h-4" />
          </button>
          
          {pendingCount > 0 && (
            <button
              onClick={handleExecuteAll}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
            >
              <Play className="w-3 h-3" />
              Execute All
            </button>
          )}
        </div>
      </div>

      {/* Operations List */}
      <div className="max-h-96 overflow-y-auto scrollbar-hide">
        <AnimatePresence>
          {stagedOperations.map((op) => (
            <motion.div
              key={op.id}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="border-b border-slate-800 last:border-b-0"
            >
              <div className="p-3 hover:bg-slate-800/50 transition-colors">
                {/* Operation Title */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {op.status === 'pending' && (
                        <Clock className="w-4 h-4 text-blue-400 flex-shrink-0" />
                      )}
                      {op.status === 'executing' && (
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        >
                          <Play className="w-4 h-4 text-yellow-400 flex-shrink-0" />
                        </motion.div>
                      )}
                      {op.status === 'completed' && (
                        <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
                      )}
                      {op.status === 'failed' && (
                        <Trash2 className="w-4 h-4 text-red-400 flex-shrink-0" />
                      )}
                      <p className="text-sm font-medium text-white">{op.title}</p>
                    </div>
                    <p className="text-xs text-slate-400">{op.description}</p>
                  </div>

                  {/* Actions */}
                  {op.status === 'pending' && (
                    <button
                      onClick={() => handleRemove(op.id)}
                      className="p-1 hover:bg-slate-700 rounded transition-colors"
                      title="Remove"
                    >
                      <Trash2 className="w-4 h-4 text-slate-400 hover:text-red-400" />
                    </button>
                  )}
                </div>

                {/* Parameters Preview */}
                <div className="mt-2 p-2 bg-slate-950/50 rounded text-xs font-mono text-slate-400 overflow-x-auto">
                  {op.type === 'create_container' && (
                    <div>
                      POST /sessions
                      <br />
                      {JSON.stringify(op.params, null, 2).substring(0, 100)}...
                    </div>
                  )}
                  {op.type === 'batch_export' && (
                    <div>
                      POST /sessions/batch
                      <br />
                      {JSON.stringify(op.params, null, 2).substring(0, 100)}...
                    </div>
                  )}
                  {op.type !== 'create_container' && op.type !== 'batch_export' && (
                    <div>{JSON.stringify(op.params, null, 2).substring(0, 100)}...</div>
                  )}
                </div>

                {/* Timestamp */}
                <div className="mt-2 text-[10px] text-slate-500">
                  {new Date(op.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="p-3 bg-slate-950/50 text-xs text-slate-400 text-center">
        {pendingCount > 0 ? (
          <>
            💡 Operations will execute in order. Review before running.
          </>
        ) : (
          <>✅ All operations completed</>
        )}
      </div>
    </motion.div>
  )
})
