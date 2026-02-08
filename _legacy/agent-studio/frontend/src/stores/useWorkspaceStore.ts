/**
 * Canvas Store - Manages user's canvasses (DB-backed multi-canvas)
 *
 * Canvasses = persisted workspaces that reference files.
 * Each user can have multiple canvasses (tabs).
 * Files in canvas reference actual files on disk (I:\users\{email}\)
 */
import { create } from "zustand";

import { API_BASE } from "@/config";

// === Types ===
export type FileType = "image" | "document" | "code" | "data" | "other";

export interface CanvasFile {
  id: string;
  name: string;
  sourcePath: string;
  uri?: string; // Permanent location after commit
  sourceType: "local" | "gdrive" | "url";
  fileType: FileType;
  status?: "staging" | "committed" | "removed" | "modified";
  addedAt: string;
}

export interface Canvas {
  id: string;
  user_id: string;
  container_id?: string | null; // Collider container ID (null = personal)
  name: string;
  files: CanvasFile[];
  created_at: string;
  updated_at: string;
}

export interface Container {
  id: string;
  name: string;
  owner_id: string;
  visual_color: string;
  created_at: string;
}

// Computed: canvas is draft if it has any staging, removed, or modified files
export function canvasIsDraft(canvas: Canvas): boolean {
  return canvas.files.some(
    (f) => f.status === "staging" || f.status === "removed" || f.status === "modified",
  );
}

interface CanvasStoreState {
  // Multi-canvas state
  canvasses: Canvas[];
  containers: Container[];
  activeCanvasId: string | null;
  activeContainerId: string | null;
  
  // Concurrency state
  activeEditors: Record<string, string[]>; // CanvasID -> UserIDs

  // UI state
  selectedIds: Set<string>;
  isLoading: boolean;
  isDragging: boolean;

  // Canvas CRUD
  loadCanvasses: (token: string) => Promise<void>;
  loadContainers: (token: string) => Promise<void>;
  setActiveContainer: (containerId: string | null) => void;
  createCanvas: (token: string, name?: string) => Promise<Canvas | null>;
  updateCanvas: (
    token: string,
    canvasId: string,
    name?: string,
    files?: CanvasFile[],
  ) => Promise<void>;
  deleteCanvas: (token: string, canvasId: string) => Promise<boolean>;
  dismissCanvas: (canvasId: string) => void; // Remove from UI only, no DB delete
  setActiveCanvas: (canvasId: string) => void;
  renameCanvas: (
    token: string,
    canvasId: string,
    name: string,
  ) => Promise<void>;
  fetchCanvasById: (token: string, canvasId: string) => Promise<void>;

  // File operations on active canvas
  addFileToCanvas: (file: CanvasFile) => void;
  softRemoveFile: (fileId: string) => void; // Set status to 'removed' (opaque)
  markFileModified: (fileId: string) => void; // Set status to 'modified'
  restoreFile: (fileId: string) => void; // Restore from 'removed' to 'staging'
  syncCanvasToServer: (token: string) => Promise<void>;
  commitCanvas: (token: string) => Promise<boolean>; // Move staged files to permanent

  // Presence
  setPresence: (editors: Record<string, string[]>) => void;

  // Selection
  toggleSelect: (id: string) => void;
  selectAll: () => void;
  clearSelection: () => void;
  getSelectedFiles: () => CanvasFile[];

  // Helpers
  getActiveCanvas: () => Canvas | null;
  setDragging: (dragging: boolean) => void;
}

// === Helpers ===
export function getFileType(filename: string): FileType {
  const ext = filename.split(".").pop()?.toLowerCase() || "";

  const imageExts = ["jpg", "jpeg", "png", "gif", "webp", "bmp", "svg"];
  const docExts = ["pdf", "doc", "docx", "txt", "rtf", "odt"];
  const codeExts = [
    "js",
    "ts",
    "tsx",
    "jsx",
    "py",
    "json",
    "html",
    "css",
    "md",
    "yaml",
    "yml",
  ];
  const dataExts = ["csv", "xlsx", "xls", "parquet", "xml"];

  if (imageExts.includes(ext)) return "image";
  if (docExts.includes(ext)) return "document";
  if (codeExts.includes(ext)) return "code";
  if (dataExts.includes(ext)) return "data";
  return "other";
}

export function getFileIcon(type: FileType): string {
  switch (type) {
    case "image":
      return "🖼️";
    case "document":
      return "📄";
    case "code":
      return "📝";
    case "data":
      return "📊";
    default:
      return "📁";
  }
}

// === Store ===
export const useCanvasStore = create<CanvasStoreState>((set, get) => ({
  canvasses: [],
  containers: [],
  activeCanvasId: null,
  activeContainerId: null,
  activeEditors: {}, 
  selectedIds: new Set(),
  isLoading: false,
  isDragging: false,

  loadCanvasses: async (token: string) => {
    set({ isLoading: true });
    try {
      const res = await fetch(`${API_BASE}/api/canvasses`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const canvasses: Canvas[] = await res.json();
        // Set first canvas as active if none selected
        const activeId =
          get().activeCanvasId ||
          (canvasses.length > 0 ? canvasses[0].id : null);
        set({ canvasses, activeCanvasId: activeId, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    } catch (e) {
      console.error("Failed to load canvasses:", e);
      set({ isLoading: false });
    }
  },

  loadContainers: async (token: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/containers`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const containers: Container[] = await res.json();
        set({
          containers,
          activeContainerId: containers.length > 0 ? containers[0].id : null,
        });
      }
    } catch (e) {
      console.error("Failed to load containers:", e);
    }
  },

  setActiveContainer: (containerId: string | null) => {
    set({ activeContainerId: containerId });
    // Auto-select the first canvas in the new container
    const canvasses = get().canvasses;
    const firstCanvas = canvasses.find((c) => c.container_id === containerId);
    set({ activeCanvasId: firstCanvas?.id || null });
  },

  fetchCanvasById: async (token: string, canvasId: string) => {
    try {
      // Check if already loaded
      const existing = get().canvasses.find((c) => c.id === canvasId);
      if (existing) {
        set({ activeCanvasId: canvasId });
        return;
      }

      set({ isLoading: true });
      const res = await fetch(`${API_BASE}/api/canvasses/${canvasId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        const canvas: Canvas = await res.json();
        // Add to list and activate
        set((state) => ({
          canvasses: [...state.canvasses, canvas],
          activeCanvasId: canvas.id,
          isLoading: false,
        }));
      } else {
        console.error("Failed to fetch specific canvas:", res.status);
        set({ isLoading: false });
      }
    } catch (e) {
      console.error("Error fetching canvas by ID:", e);
      set({ isLoading: false });
    }
  },

  createCanvas: async (token: string, name: string = "New Canvas") => {
    try {
      set({ isLoading: true });
      const activeContainerId = get().activeContainerId;
      const res = await fetch(
        `${API_BASE}/api/canvasses?container_id=${activeContainerId || ""}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ name }), // container_id handled by query param for now, or body
        },
      );
      if (res.ok) {
        const newCanvas: Canvas = await res.json();
        set((state) => ({
          canvasses: [...state.canvasses, newCanvas],
          activeCanvasId: newCanvas.id,
        }));
        return newCanvas;
      }
    } catch (e) {
      console.error("Failed to create canvas:", e);
    }
    return null;
  },

  updateCanvas: async (
    token: string,
    canvasId: string,
    name?: string,
    files?: CanvasFile[],
  ) => {
    try {
      const body: { name?: string; files?: CanvasFile[] } = {};
      if (name !== undefined) body.name = name;
      if (files !== undefined) body.files = files;

      const res = await fetch(`${API_BASE}/api/canvasses/${canvasId}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const updated: Canvas = await res.json();
        set((state) => ({
          canvasses: state.canvasses.map((c) =>
            c.id === canvasId ? updated : c,
          ),
        }));
      }
    } catch (e) {
      console.error("Failed to update canvas:", e);
    }
  },

  deleteCanvas: async (token: string, canvasId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/canvasses/${canvasId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        set((state) => {
          const remaining = state.canvasses.filter((c) => c.id !== canvasId);
          const newActiveId =
            state.activeCanvasId === canvasId
              ? remaining.length > 0
                ? remaining[0].id
                : null
              : state.activeCanvasId;
          return { canvasses: remaining, activeCanvasId: newActiveId };
        });
        return true;
      }
    } catch (e) {
      console.error("Failed to delete canvas:", e);
    }
    return false;
  },

  dismissCanvas: (canvasId: string) => {
    // Remove from local state only - canvas stays in DB
    set((state) => {
      const remaining = state.canvasses.filter((c) => c.id !== canvasId);
      const newActiveId =
        state.activeCanvasId === canvasId
          ? remaining.length > 0
            ? remaining[0].id
            : null
          : state.activeCanvasId;
      return { canvasses: remaining, activeCanvasId: newActiveId };
    });
  },

  setActiveCanvas: (canvasId: string) => {
    set({ activeCanvasId: canvasId, selectedIds: new Set() });
  },

  renameCanvas: async (token: string, canvasId: string, name: string) => {
    await get().updateCanvas(token, canvasId, name);
  },

  // Local file operations (optimistic updates, then sync)
  addFileToCanvas: (file: CanvasFile) => {
    set((state) => {
      const canvas = state.canvasses.find((c) => c.id === state.activeCanvasId);
      if (!canvas) return state;

      const updatedCanvas = { ...canvas, files: [...canvas.files, file] };
      return {
        canvasses: state.canvasses.map((c) =>
          c.id === canvas.id ? updatedCanvas : c,
        ),
      };
    });
  },

  softRemoveFile: (fileId: string) => {
    set((state) => {
      const canvas = state.canvasses.find((c) => c.id === state.activeCanvasId);
      if (!canvas) return state;

      const updatedCanvas = {
        ...canvas,
        files: canvas.files.map((f) =>
          f.id === fileId ? { ...f, status: "removed" as const } : f,
        ),
      };
      return {
        canvasses: state.canvasses.map((c) =>
          c.id === canvas.id ? updatedCanvas : c,
        ),
      };
    });
  },
  
  markFileModified: (fileId: string) => {
    set((state) => {
      const canvas = state.canvasses.find((c) => c.id === state.activeCanvasId);
      if (!canvas) return state;

      const updatedCanvas = {
        ...canvas,
        files: canvas.files.map((f) =>
          f.id === fileId ? { ...f, status: "modified" as const } : f,
        ),
      };
      return {
        canvasses: state.canvasses.map((c) =>
          c.id === canvas.id ? updatedCanvas : c,
        ),
      };
    });
  },

  restoreFile: (fileId: string) => {
    set((state) => {
      const canvas = state.canvasses.find((c) => c.id === state.activeCanvasId);
      if (!canvas) return state;

      const updatedCanvas = {
        ...canvas,
        files: canvas.files.map((f) =>
          f.id === fileId ? { ...f, status: "staging" as const } : f,
        ),
      };
      return {
        canvasses: state.canvasses.map((c) =>
          c.id === canvas.id ? updatedCanvas : c,
        ),
      };
    });
  },

  syncCanvasToServer: async (token: string) => {
    const canvas = get().getActiveCanvas();
    if (!canvas) return;
    await get().updateCanvas(token, canvas.id, undefined, canvas.files);
  },

  commitCanvas: async (token: string) => {
    const canvas = get().getActiveCanvas();
    if (!canvas) return false;
    try {
      const res = await fetch(`${API_BASE}/api/canvasses/${canvas.id}/commit`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        // Reload canvasses to get updated file URIs
        await get().loadCanvasses(token);
        return true;
      }
    } catch (e) {
      console.error("Failed to commit canvas:", e);
    }
    return false;
  },

  setPresence: (editors: Record<string, string[]>) => {
      set({ activeEditors: editors });
  },

  // Selection
  toggleSelect: (id: string) =>
    set((state) => {
      const newSelected = new Set(state.selectedIds);
      if (newSelected.has(id)) {
        newSelected.delete(id);
      } else {
        newSelected.add(id);
      }
      return { selectedIds: newSelected };
    }),

  selectAll: () =>
    set((state) => {
      const canvas = state.canvasses.find((c) => c.id === state.activeCanvasId);
      return { selectedIds: new Set(canvas?.files.map((f) => f.id) || []) };
    }),

  clearSelection: () => set({ selectedIds: new Set() }),

  getSelectedFiles: () => {
    const state = get();
    const canvas = state.canvasses.find((c) => c.id === state.activeCanvasId);
    return canvas?.files.filter((f) => state.selectedIds.has(f.id)) || [];
  },

  getActiveCanvas: () => {
    const state = get();
    return state.canvasses.find((c) => c.id === state.activeCanvasId) || null;
  },

  setDragging: (isDragging: boolean) => set({ isDragging }),
}));

// Backward compatibility exports
export const useWorkspaceStore = useCanvasStore;
export type { CanvasFile as WorkspaceFile };
export type { Canvas as CanvasState };
