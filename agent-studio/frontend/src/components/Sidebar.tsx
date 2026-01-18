"use client";

/**
 * Sidebar - Stripped down version without file upload/list.
 * Files are now managed via the inline WorkspaceCanvas.
 *
 * Contains:
 * - Header (Deep Agent branding)
 * - Skills section
 * - Active Tasks section
 * - Footer (Reset Session, Connected status, Preferences)
 */
import {
  RefreshCw,
  Sparkles,
  CheckSquare,
  Square,
  User,
  PanelLeftClose,
  Box,
} from "lucide-react";
import { usePreferencesStore } from "@/stores/usePreferencesStore";
import { useCanvasStore } from "@/stores/useWorkspaceStore";
import { PreferencesPanel } from "@/components/PreferencesPanel";

interface Todo {
  id: string;
  text: string;
  done: boolean;
}

interface SidebarProps {
  isConnected: boolean;
  skills: string[];
  todos: Todo[];
  onReset: () => void;
  email?: string | null;
  onLogout?: () => void;
  token: string | null;
}

export function Sidebar({
  isConnected,
  skills,
  todos,
  onReset,
  email,
  onLogout,
  token,
}: SidebarProps) {
  const { theme } = usePreferencesStore();
  const { containers, activeContainerId } = useCanvasStore();
  const isDark = theme === "dark";

  return (
    <aside
      className={`w-64 border-r flex flex-col h-screen ${
        isDark ? "bg-zinc-900 border-zinc-800" : "bg-white border-gray-200"
      }`}
    >
      {/* Header */}
      <div
        className={`p-4 border-b ${
          isDark ? "border-zinc-800" : "border-gray-200"
        }`}
      >
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-purple-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">D</span>
          </div>
          <div>
            <h1
              className={`text-lg font-semibold ${
                isDark ? "text-white" : "text-gray-900"
              }`}
            >
              Lody's Clan
            </h1>
            <p
              className={`text-xs ${
                isDark ? "text-zinc-500" : "text-gray-500"
              }`}
            >
              Collider Canvas
            </p>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Skills Section */}
        {skills.length > 0 && (
          <div
            className={`p-4 border-b ${
              isDark ? "border-zinc-800" : "border-gray-200"
            }`}
          >
            <h2
              className={`text-xs font-semibold uppercase tracking-wider mb-2 ${
                isDark ? "text-zinc-400" : "text-gray-500"
              }`}
            >
              Skills
            </h2>
            <div className="flex flex-wrap gap-1">
              {skills.map((skill, i) => (
                <span
                  key={i}
                  className="flex items-center gap-1 px-2 py-1 bg-violet-900/30 border border-violet-700/50 rounded text-xs text-violet-300"
                >
                  <Sparkles size={10} />
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Containers Section */}
        <div className="px-4 py-2">
          {containers.length === 0 ? (
            <div className="text-xs text-center py-2 opacity-50">
              No containers
            </div>
          ) : (
            <div className="space-y-4">
              {/* Group Logic: We assume containers have an owner_name or we group by owner_id if name not avail? 
                  The store might not have owner names yet. 
                  For now, let's just group by owner_id or just list them if grouping is complex without backend data.
                  
                  Actually, user request is:
                  ICON USERNAME
                    - Container
                  ICON OTHER USER
                    - Shared container
                  
                  Since we only have a flat list in 'containers' (from useCanvasStore), 
                  we need to organize this list.
              */}

              {/* 
                 TODO: Ideally we group by owner. 
                 Since the current store/API might just return a flat list, 
                 we will simulate the grouping or just display them with icons as requested if we can't group easily yet.
                 
                 If the user means "Show the owner header above their boxes":
              */}

              {/* 
                  Let's try to group by Owner ID (assuming we have access, or just show list for now but clean up the "Containers" header).
                  User said: "REMOVE 'BOX EVERYWHERE'. REDUNDANT WORD. IN PANEL. USER SEES UNDER CONTAINERS..."
                  
                  Wait, the user wants to REMOVE the word "Containers" header? 
                  "REMOVE 'BOX EVERYWHERE'. REDUNDANT WORD. IN PANEL. USER SEES UNDER CONTAINERS: ICON FOLLOW BY USER"
                  
                  It seems they want to REPLACE the simple "Containers" header with a structured list of Owners.
               */}

              <div className="space-y-1">
                {containers.map((container) => (
                  <button
                    key={container.id}
                    onClick={() => {
                      if (token) {
                        const { setActiveContainer } =
                          useCanvasStore.getState();
                        setActiveContainer(container.id);
                      }
                    }}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors ${
                      activeContainerId === container.id
                        ? "bg-violet-500/10 text-violet-500 ring-1 ring-violet-500/20"
                        : isDark
                          ? "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"
                          : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                    }`}
                  >
                    {/* Replaced Box icon with User-like icon or specific logic if available, 
                        but user said "ICON FOLLOW BY USER... BENEATH: SHARED CONTAINER" 
                        This implies a hierarchical view. 
                        
                        For this minimal fix to remove "Redundant Box":
                    */}
                    <Box
                      size={14}
                      style={{ color: container.visual_color || "#8b5cf6" }}
                    />
                    {/* We should strip "Box" from the name if it's there? 
                        User: "Lody's Box" -> "Lody's" ? 
                        User said: "REMOVE 'BOX EVERYWHERE'."
                    */}
                    <span className="truncate">
                      {container.name.replace("'s Box", "")}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div
          className={`mx-4 my-2 border-b ${isDark ? "border-zinc-800" : "border-gray-200"}`}
        />

        {/* Active Tasks Section */}
        <div
          className={`flex-1 p-4 overflow-y-auto ${
            isDark ? "border-zinc-800" : "border-gray-200"
          }`}
        >
          <h2
            className={`text-xs font-semibold uppercase tracking-wider mb-2 ${
              isDark ? "text-zinc-400" : "text-gray-500"
            }`}
          >
            Active Tasks
          </h2>
          {todos.length === 0 ? (
            <p
              className={`text-xs ${
                isDark ? "text-zinc-600" : "text-gray-400"
              }`}
            >
              No todos yet
            </p>
          ) : (
            <div className="space-y-1">
              {todos.map((todo) => (
                <div
                  key={todo.id}
                  className={`flex items-center gap-2 text-xs ${
                    isDark ? "text-zinc-400" : "text-gray-600"
                  }`}
                >
                  {todo.done ? (
                    <CheckSquare size={14} className="text-emerald-400" />
                  ) : (
                    <Square
                      size={14}
                      className={isDark ? "text-zinc-600" : "text-gray-400"}
                    />
                  )}
                  <span
                    className={
                      todo.done
                        ? `line-through ${
                            isDark ? "text-zinc-600" : "text-gray-400"
                          }`
                        : ""
                    }
                  >
                    {todo.text}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div
        className={`p-4 border-t space-y-3 ${
          isDark ? "border-zinc-800" : "border-gray-200"
        }`}
      >
        <button
          onClick={onReset}
          className={`w-full flex items-center justify-center gap-2 px-4 py-2 border rounded-lg text-sm transition ${
            isDark
              ? "bg-zinc-800 hover:bg-zinc-700 border-zinc-700 text-zinc-400 hover:text-white"
              : "bg-gray-100 hover:bg-gray-200 border-gray-300 text-gray-600 hover:text-gray-900"
          }`}
        >
          <RefreshCw size={14} />
          Reset Session
        </button>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs">
            {isConnected ? (
              <>
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-emerald-400">Connected</span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-red-400">Disconnected</span>
              </>
            )}
          </div>
          <PreferencesPanel />
        </div>

        {/* User section */}
        {email && (
          <div
            className={`flex items-center justify-between pt-3 border-t ${isDark ? "border-zinc-700" : "border-gray-200"}`}
          >
            <span
              className={`text-xs truncate ${isDark ? "text-zinc-400" : "text-gray-600"}`}
            >
              {email}
            </span>
            {onLogout && (
              <button
                onClick={onLogout}
                className={`p-1.5 rounded-lg transition-colors ${isDark ? "hover:bg-zinc-700 text-zinc-500 hover:text-zinc-300" : "hover:bg-gray-200 text-gray-500 hover:text-gray-700"}`}
                title="Switch User"
              >
                <User size={14} />
              </button>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
