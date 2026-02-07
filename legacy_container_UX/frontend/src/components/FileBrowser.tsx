import { useState, useEffect, useCallback } from 'react'
import { FileText, Upload, Trash2, ExternalLink, RefreshCw, FileSpreadsheet, File as FileIcon, Loader2 } from 'lucide-react'
// LEGACY: api-backend.ts deleted - using stubs (V4.1 will use Source containers)
interface GCSFile { path: string; name: string; size: number; updated: string; content_type: string; }
const listGCSFiles = async () => ({ files: [] as GCSFile[] });
const uploadToGCS = async (_file: File) => ({ path: '', name: '' });
const deleteGCSFile = async (_path: string) => {};
const getGCSSignedUrl = async (_path: string, _method: string) => ({ signed_url: '' });

import { openInOfficeOnline, isOfficeFileType } from '../lib/office-viewer'
import { toast } from '../lib/toast-store'

export function FileBrowser() {
  const [files, setFiles] = useState<GCSFile[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [processingPath, setProcessingPath] = useState<string | null>(null)

  const loadFiles = useCallback(async () => {
    try {
      setLoading(true)
      const response = await listGCSFiles()
      setFiles(response.files)
    } catch (error) {
      console.error('Failed to load files:', error)
      toast.error('Failed to load files')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadFiles()
  }, [loadFiles])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      setUploading(true)
      await uploadToGCS(file)
      toast.success('File uploaded successfully')
      loadFiles()
    } catch (error) {
      console.error('Upload failed:', error)
      toast.error('Upload failed')
    } finally {
      setUploading(false)
      // Reset input
      e.target.value = ''
    }
  }

  const handleDelete = async (filePath: string) => {
    if (!confirm('Are you sure you want to delete this file?')) return

    try {
      await deleteGCSFile(filePath)
      toast.success('File deleted')
      setFiles(prev => prev.filter(f => f.path !== filePath))
    } catch (error) {
      console.error('Delete failed:', error)
      toast.error('Failed to delete file')
    }
  }

  const handleViewInOffice = async (file: GCSFile) => {
    try {
      setProcessingPath(file.path)
      toast.info('Opening in Office Online...')

      // 1. Get Signed URL (Read-only, 1 hour)
      const { signed_url } = await getGCSSignedUrl(file.path, 'GET')

      // 2. Open via Office Online helper
      const viewerWindow = openInOfficeOnline({ fileUrl: signed_url, mode: 'view' })

      if (!viewerWindow) {
        toast.error('Popup blocked. Please allow popups and try again.')
        return
      }

      toast.success('Opened in new tab')
    } catch (error) {
      console.error('View failed:', error)
      toast.error('Failed to open file')
    } finally {
      setProcessingPath(null)
    }
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-700 flex items-center justify-between bg-slate-800/50">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-400" />
          Cloud Files
        </h3>
        <div className="flex items-center gap-2">
          <label className="cursor-pointer p-1.5 hover:bg-slate-700 rounded text-blue-400 transition-colors">
            <Upload className="w-4 h-4" />
            <input 
              type="file" 
              className="hidden" 
              onChange={handleUpload} 
              disabled={uploading}
              aria-label="Upload file"
            />
          </label>
          <button 
            onClick={loadFiles}
            className="p-1.5 hover:bg-slate-700 rounded text-slate-400 transition-colors"
            title="Refresh files"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {files.length === 0 && !loading && (
          <div className="text-center py-8 text-slate-500 text-sm">
            No files uploaded yet.
          </div>
        )}

        {files.map(file => (
          <div 
            key={file.path}
            className="flex items-center justify-between p-2 hover:bg-slate-800 rounded group transition-colors border border-transparent hover:border-slate-700"
          >
            <div className="flex items-center gap-3 overflow-hidden">
              {file.name.endsWith('xlsx') || file.name.endsWith('csv') ? (
                <FileSpreadsheet className="w-8 h-8 text-green-500 flex-shrink-0" />
              ) : (
                <FileIcon className="w-8 h-8 text-slate-400 flex-shrink-0" />
              )}
              <div className="min-w-0">
                <p className="text-sm text-slate-200 font-medium truncate" title={file.name}>
                  {file.name}
                </p>
                <p className="text-xs text-slate-500">
                  {(file.size / 1024).toFixed(1)} KB • {new Date(file.updated).toLocaleDateString()}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {isOfficeFileType(file.name) && (
                <button
                  onClick={() => handleViewInOffice(file)}
                  disabled={!!processingPath}
                  className="p-1.5 text-blue-400 hover:bg-blue-900/30 rounded transition-colors"
                  title="View in Office Online"
                >
                  {processingPath === file.path ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <ExternalLink className="w-4 h-4" />
                  )}
                </button>
              )}
              
              <button
                onClick={() => handleDelete(file.path)}
                disabled={!!processingPath}
                className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-900/20 rounded transition-colors"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
