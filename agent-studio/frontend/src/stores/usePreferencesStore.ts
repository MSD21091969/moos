/**
 * Preferences Store - User preferences persisted to localStorage
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "dark" | "light";

interface PreferencesState {
  autoSync: boolean;
  theme: Theme;
  userColor: string; // Hex color for personal tabs
  sidebarOpen: boolean;

  // Actions
  toggleAutoSync: () => void;
  setAutoSync: (value: boolean) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (value: boolean) => void;
  setUserColor: (color: string) => void;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      autoSync: false,
      theme: "dark",
      userColor: "#8b5cf6", // Default violet-500
      sidebarOpen: true,

      toggleAutoSync: () => set((state) => ({ autoSync: !state.autoSync })),
      setAutoSync: (value) => set({ autoSync: value }),
      toggleSidebar: () =>
        set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (value) => set({ sidebarOpen: value }),
      setUserColor: (color) => set({ userColor: color }),

      setTheme: (theme) => set({ theme }),
      toggleTheme: () =>
        set((state) => ({
          theme: state.theme === "dark" ? "light" : "dark",
        })),
    }),
    {
      name: "agent-studio-preferences",
    },
  ),
);
