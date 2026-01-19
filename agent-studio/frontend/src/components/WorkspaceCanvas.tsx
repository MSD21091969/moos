"use client";

/**
 * WorkspaceCanvas - Multi-canvas workspace with tabs
 *
 * Features:
 * - Canvas tabs (add, rename, delete, switch)
 * - Drag-drop files from OS file explorer
 * - File grid with selection
 * - QuickActions row
 */
import { useState, useCallback, useEffect, useMemo } from "react";
import { useDropzone } from "react-dropzone";
import { API_BASE } from "@/config";
import {
  FileText,
  Image,
  Code,
  Database,
  Folder,
  Trash2,
  Zap,
  Plus,
  X,
  Edit2,
  Check,
  PanelLeft,
  ExternalLink,
  CloudUpload,
} from "lucide-react";
import {
  useCanvasStore,
  type CanvasFile,
  type FileType,
  type Canvas,
  getFileType,
  canvasIsDraft,
} from "@/stores/useWorkspaceStore";
import { usePreferencesStore } from "@/stores/usePreferencesStore";
import { QuickActions, QUICK_ACTIONS } from "@/components/QuickActions";

interface WorkspaceCanvasProps {
  token: string | null;
  isConnected: boolean;
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  onUploadFile: (file: File) => void;
  initialCanvasId?: string | null;
}

const FileIcon = ({ type }: { type: FileType }) => {
  const iconClass = "w-8 h-8 text-zinc-400";
  switch (type) {
    case "image":
      return <Image className={`${iconClass} text-blue-400`} />;
    case "document":
      return <FileText className={`${iconClass} text-orange-400`} />;
    case "code":
      return <Code className={`${iconClass} text-green-400`} />;
    case "data":
      return <Database className={`${iconClass} text-purple-400`} />;
    default:
      return <Folder className={iconClass} />;
  }
};

// Canvas Tab component
function CanvasTab({
  canvas,
  isActive,
  onSelect,
  onRename,
  onDelete,
}: {
  canvas: Canvas;
  isActive: boolean;
  onSelect: () => void;
  onRename: (name: string) => void;
  onDelete: () => void;
}) {
  const { userColor } = usePreferencesStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(canvas.name);

  const isDraft = canvasIsDraft(canvas);
  const isPersonal = !canvas.container_id;

  const handleSave = () => {
    if (editName.trim()) {
      onRename(editName.trim());
    }
    setIsEditing(false);
  };

  return (
    <div
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-t-lg cursor-pointer transition-colors ${
        isActive
          ? "bg-zinc-800 text-white"
          : "bg-zinc-900/50 text-zinc-400 hover:bg-zinc-800/50"
      }`}
      style={
        isActive
          ? {
              borderBottom: `2px solid ${
                !isPersonal ? "#71717a" : userColor // Force gray (zinc-500) for shared/imported
              }`,
            }
          : {}
      }
      onClick={() => !isEditing && onSelect()}
    >
      {isDraft && (
        <div
          className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0"
          title="Contains unsaved drafts"
        />
      )}
      {isEditing ? (
        <div className="flex items-center gap-1">
          <input
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSave();
              if (e.key === "Escape") setIsEditing(false);
            }}
            className="bg-zinc-700 text-white text-sm px-1 py-0.5 rounded w-32 outline-none"
            autoFocus
            onClick={(e) => e.stopPropagation()}
          />
          <button
            onClick={handleSave}
            className="text-green-400 hover:text-green-300"
          >
            <Check className="w-3 h-3" />
          </button>
        </div>
      ) : (
        <>
          <span
            className={`text-sm select-none ${!isPersonal ? "italic text-zinc-300" : ""}`}
            title={!isPersonal ? "Imported / Shared Canvas" : ""}
          >
            {canvas.name}
          </span>
          {isActive && (
            <div className="flex items-center gap-0.5 ml-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsEditing(true);
                  setEditName(canvas.name);
                }}
                className="text-zinc-500 hover:text-zinc-300 p-0.5"
              >
                <Edit2 className="w-3 h-3" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="text-zinc-500 hover:text-red-400 p-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function WorkspaceCanvas({
  token,
  isConnected,
  isLoading,
  onSendMessage,
  onUploadFile,
  initialCanvasId,
}: WorkspaceCanvasProps) {
  const { theme } = usePreferencesStore();
  const isDark = theme === "dark";

  const {
    canvasses,
    activeCanvasId,
    selectedIds,
    isDragging,
    loadCanvasses,
    loadContainers,
    createCanvas,
    dismissCanvas,
    renameCanvas,
    setActiveCanvas,
    addFileToCanvas,
    softRemoveFile,
    restoreFile,
    syncCanvasToServer,
    commitCanvas,
    toggleSelect,
    selectAll,
    clearSelection,
    setDragging,
    fetchCanvasById,
    getActiveCanvas,
    activeContainerId,
  } = useCanvasStore();

  // Local Toast State
  const [toast, setToast] = useState<{
    message: string;
    action?: () => void;
  } | null>(null);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const handleOpenExternal = async (filename: string) => {
    if (!token) return;
    try {
      await fetch(`${API_BASE}/api/files/${filename}/open`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (e) {
      console.error("Failed to open external:", e);
    }
  };

  const handleRemoveFile = (fileId: string) => {
    softRemoveFile(fileId);
    // No toast - just visual feedback via opacity
  };

  // Load canvasses on mount, then handle deep link
  useEffect(() => {
    if (token) {
      loadCanvasses(token).then(() => {
        if (initialCanvasId) {
          fetchCanvasById(token, initialCanvasId);
        }
      });
      loadContainers(token);
    }
  }, [token, loadCanvasses, loadContainers, fetchCanvasById, initialCanvasId]);

  // Filter canvasses for tabs based on activeContainerId
  const visibleCanvasses = useMemo(() => {
    return canvasses.filter((c) => c.container_id === activeContainerId);
  }, [canvasses, activeContainerId]);

  // Handle drag events
  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragging(true);
    },
    [setDragging],
  );

  const handleDragLeave = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragging(false);
    },
    [setDragging],
  );

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragging(false);

      // Don't accept files if no canvas is active
      if (!activeCanvasId) {
        console.warn("No canvas active - create a canvas first");
        return;
      }

      const droppedFiles = Array.from(e.dataTransfer.files);
      const currentCanvas = getActiveCanvas();
      const existingNames = new Set(
        currentCanvas?.files.map((f: CanvasFile) => f.name) || [],
      );

      for (const file of droppedFiles) {
        // Skip duplicates
        if (existingNames.has(file.name)) {
          console.log(`Skipping duplicate: ${file.name}`);
          continue;
        }
        existingNames.add(file.name); // Track for this batch too

        // Upload file to backend cache
        onUploadFile(file);

        // Add file reference to current canvas (optimistic)
        const canvasFile: CanvasFile = {
          id:
            typeof crypto.randomUUID === "function"
              ? crypto.randomUUID()
              : Math.random().toString(36).substring(2) +
                Date.now().toString(36),
          name: file.name,
          sourcePath: `I:\\system\\.cache\\${file.name}`,
          sourceType: "local",
          fileType: getFileType(file.name),
          status: "staging",
          addedAt: new Date().toISOString(),
        };

        addFileToCanvas(canvasFile);
      }

      // Sync changes to server
      if (token && droppedFiles.length > 0) {
        // Wait a bit for state to update then sync
        setTimeout(() => syncCanvasToServer(token), 1000);
      }
    },
    [
      activeCanvasId,
      onUploadFile,
      addFileToCanvas,
      syncCanvasToServer,
      token,
      setDragging,
    ],
  );

  const activeCanvas = getActiveCanvas();
  const files = activeCanvas?.files || [];
  const { sidebarOpen, toggleSidebar } = usePreferencesStore();

  return (
    <div
      className="flex flex-col h-full bg-zinc-900 overflow-hidden"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Overlay for drag drop */}
      {isDragging && (
        <div className="absolute inset-0 bg-blue-500/20 border-4 border-blue-500/50 z-50 flex items-center justify-center pointer-events-none">
          <div className="bg-zinc-900 p-4 rounded-lg shadow-xl animate-bounce">
            <CloudUpload className="w-8 h-8 text-blue-400 mx-auto mb-2" />
            <p className="text-white font-medium">
              Drop files to add to canvas
            </p>
          </div>
        </div>
      )}

      {/* Tabs Header */}
      <div className="flex items-center bg-zinc-950 border-b border-zinc-800">
        <button
          onClick={toggleSidebar}
          className={`p-1.5 rounded hover:bg-zinc-800 text-zinc-400 mr-2 ${sidebarOpen ? "hidden" : "block"}`}
          title="Open Sidebar"
        >
          <PanelLeft size={16} />
        </button>
        <div className="flex-1 flex items-center overflow-x-auto no-scrollbar">
          {visibleCanvasses.map((canvas) => (
            <CanvasTab
              key={canvas.id}
              canvas={canvas}
              isActive={canvas.id === activeCanvasId}
              onSelect={() => setActiveCanvas(canvas.id)}
              onRename={(name) => renameCanvas(token!, canvas.id, name)}
              onDelete={() => dismissCanvas(canvas.id)}
            />
          ))}
          <button
            onClick={() => createCanvas(token!)}
            className="p-1.5 rounded hover:bg-zinc-800 text-zinc-500 hover:text-white transition-colors ml-1"
            title="New Canvas"
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      <div
        className="flex-1 overflow-auto p-6 relative"
        onClick={() => {
          clearSelection();
          if (sidebarOpen) toggleSidebar();
        }}
      >
        {files.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Zap className="w-12 h-12 text-violet-500/50 mb-4" />
            <h3 className="text-xl font-medium text-white mb-2">
              Empty Canvas
            </h3>
            <p className="text-zinc-500 max-w-sm mb-8">
              Drag and drop files here, or use Quick Actions to get started.
            </p>

            <QuickActions
              actions={QUICK_ACTIONS}
              onSelect={onSendMessage}
              disabled={isLoading}
            />
          </div>
        ) : (
          <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-10 gap-2">
            {files.map((file) => (
              <div
                key={file.id}
                onClick={(e) => {
                  e.stopPropagation();
                  // Click on removed file = restore, else toggle select
                  if (file.status === "removed") {
                    restoreFile(file.id);
                  } else {
                    toggleSelect(file.id);
                  }
                }}
                className={`group relative aspect-square p-2 rounded-lg border transition-all cursor-pointer hover:-translate-y-0.5 ${
                  file.status === "removed" ? "opacity-25 grayscale" : ""
                } ${
                  selectedIds.has(file.id)
                    ? "bg-blue-500/10 border-blue-500/50 ring-1 ring-blue-500/50"
                    : "bg-zinc-800/50 border-zinc-700/50 hover:bg-zinc-800 hover:border-zinc-600 hover:shadow-lg"
                }`}
              >
                {/* File Status Indicator */}
                {file.status === "staging" && (
                  <div
                    className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-amber-500"
                    title="Unsaved"
                  />
                )}
                {file.status === "removed" && (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-full h-0.5 bg-red-500/70 rotate-45" />
                  </div>
                )}

                <div className="flex flex-col items-center justify-center h-full gap-1">
                  <FileIcon type={file.fileType} />
                  <span className="text-xs text-zinc-300 font-medium text-center line-clamp-2 px-0.5">
                    {file.name}
                  </span>
                </div>

                {/* Hover Actions */}
                <div className="absolute inset-x-1 bottom-1 flex justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity translate-y-1 group-hover:translate-y-0">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveFile(file.id);
                    }}
                    className="p-1 bg-zinc-900/90 text-zinc-400 hover:text-red-400 rounded shadow-lg backdrop-blur-sm"
                    title="Remove"
                  >
                    <Trash2 size={12} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenExternal(file.name);
                    }}
                    className="p-1 bg-zinc-900/90 text-zinc-400 hover:text-blue-400 rounded shadow-lg backdrop-blur-sm"
                    title="Open External"
                  >
                    <ExternalLink size={12} />
                  </button>
                </div>
              </div>
            ))}

            {/* Add Button in Grid */}
            <div className="flex flex-col items-center justify-center aspect-square rounded-lg border-2 border-dashed border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900/50 transition-colors cursor-default text-zinc-600">
              <Plus size={16} className="mb-1 opacity-50" />
              <span className="text-[10px] font-medium uppercase tracking-wider opacity-50">
                Drop
              </span>
            </div>
          </div>
        )}

        {/* Toast Notification */}
        {toast && (
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-3 px-4 py-2 bg-zinc-800 text-white rounded-lg shadow-xl border border-zinc-700 animate-in fade-in slide-in-from-bottom-2">
            <span className="text-sm">{toast.message}</span>
            {toast.action && (
              <button
                onClick={toast.action}
                className="text-sm font-medium text-violet-400 hover:text-violet-300"
              >
                Undo
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
