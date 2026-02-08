"use client";

/**
 * PreferencesPanel - Settings panel for user preferences
 */
import * as Dialog from "@radix-ui/react-dialog";
import * as Switch from "@radix-ui/react-switch";
import { X, Settings, Moon, Sun, CloudUpload, Palette } from "lucide-react";
import { usePreferencesStore } from "@/stores/usePreferencesStore";
import { useState } from "react";

export function PreferencesPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const {
    autoSync,
    theme,
    userColor,
    toggleAutoSync,
    toggleTheme,
    setUserColor,
  } = usePreferencesStore();

  return (
    <Dialog.Root open={isOpen} onOpenChange={setIsOpen}>
      <Dialog.Trigger asChild>
        <button
          className="p-2 rounded-lg hover:bg-zinc-800 transition text-zinc-400 hover:text-white"
          aria-label="Settings"
        >
          <Settings size={18} />
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40" />
        <Dialog.Content
          className={`fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[90vw] max-w-md rounded-xl shadow-2xl z-50 ${
            theme === "dark"
              ? "bg-zinc-900 text-zinc-100"
              : "bg-white text-zinc-900"
          }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-zinc-700">
            <Dialog.Title className="text-lg font-semibold flex items-center gap-2">
              <Settings size={20} />
              Preferences
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                className="p-1 rounded-lg hover:bg-zinc-800 transition"
                aria-label="Close"
              >
                <X size={20} />
              </button>
            </Dialog.Close>
          </div>

          {/* Settings List */}
          <div className="p-4 space-y-6">
            {/* Auto-Sync Setting */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CloudUpload size={20} className="text-zinc-400" />
                <div>
                  <p className="font-medium">Auto-sync to Storage</p>
                  <p className="text-sm text-zinc-500">
                    Automatically save files to I: drive
                  </p>
                </div>
              </div>
              <Switch.Root
                checked={autoSync}
                onCheckedChange={toggleAutoSync}
                className="w-11 h-6 bg-zinc-700 rounded-full relative data-[state=checked]:bg-violet-600 transition"
              >
                <Switch.Thumb className="block w-5 h-5 bg-white rounded-full shadow transition translate-x-0.5 data-[state=checked]:translate-x-[22px]" />
              </Switch.Root>
            </div>

            {/* Theme Setting */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {theme === "dark" ? (
                  <Moon size={20} className="text-zinc-400" />
                ) : (
                  <Sun size={20} className="text-amber-500" />
                )}
                <div>
                  <p className="font-medium">Theme</p>
                  <p className="text-sm text-zinc-500">
                    {theme === "dark" ? "Dark mode" : "Light mode"}
                  </p>
                </div>
              </div>
              <Switch.Root
                checked={theme === "light"}
                onCheckedChange={toggleTheme}
                className="w-11 h-6 bg-zinc-700 rounded-full relative data-[state=checked]:bg-amber-500 transition"
              >
                <Switch.Thumb className="block w-5 h-5 bg-white rounded-full shadow transition translate-x-0.5 data-[state=checked]:translate-x-[22px]" />
              </Switch.Root>
            </div>

            {/* Color Setting */}
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Palette size={20} className="text-zinc-400" />
                <div>
                  <p className="font-medium">Tab Accent Color</p>
                  <p className="text-sm text-zinc-500">
                    Personalized color for your canvas tabs
                  </p>
                </div>
              </div>
              <div className="flex gap-2 pl-[32px]">
                {[
                  "#8b5cf6",
                  "#ec4899",
                  "#ef4444",
                  "#f59e0b",
                  "#10b981",
                  "#3b82f6",
                ].map((color) => (
                  <button
                    key={color}
                    onClick={() => setUserColor(color)}
                    className={`w-6 h-6 rounded-full border-2 transition-transform hover:scale-110 ${
                      userColor === color
                        ? "border-white scale-125 shadow-lg shadow-black/50"
                        : "border-zinc-800"
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-zinc-700">
            <p className="text-xs text-zinc-500 text-center">
              Preferences are saved automatically
            </p>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
