/**
 * Centralized Form Styling System
 * 
 * Provides consistent styling for all forms, modals, and inline editors.
 * Ensures AI agent can interact with predictable DOM structure.
 * 
 * Usage:
 *   import { FORM_STYLES } from '@/lib/form-system';
 *   <label className={FORM_STYLES.label}>Title</label>
 *   <input className={FORM_STYLES.input} />
 */

export const FORM_STYLES = {
  // Labels
  label: "text-slate-100 text-sm",
  
  // Inputs
  input: "w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-white focus:outline-none focus:border-blue-500 focus:bg-slate-800 transition-colors",
  
  // Textareas
  textarea: "w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-white focus:outline-none focus:border-blue-500 focus:bg-slate-800 resize-none transition-colors",
  
  // Selects
  select: "w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white appearance-none focus:outline-none focus:border-blue-500",
  selectIcon: "absolute right-2 top-1.5 w-3 h-3 text-slate-500 rotate-90 pointer-events-none",
  
  // Tag container
  tagContainer: "min-h-[28px] bg-slate-800 border border-slate-700 rounded px-1.5 py-1 flex flex-wrap gap-1 focus-within:border-blue-500 focus-within:bg-slate-800 transition-colors",
  
  // Individual tag
  tag: "bg-blue-900/30 text-blue-200 px-1.5 py-0.5 rounded text-[10px] flex items-center gap-1 border border-blue-800/50",
  
  // Tag input
  tagInput: "bg-transparent text-white focus:outline-none min-w-[60px] flex-1 h-5",
  
  // Color picker button
  colorButton: "w-5 h-5 rounded-full border border-slate-600 hover:scale-110 transition-transform",
  
  // Color display
  colorDisplay: "flex items-center justify-between bg-slate-800 border border-slate-700 rounded px-2 py-1.5",
  colorHex: "text-slate-400 font-mono",
  
  // Form actions
  actionContainer: "pt-2 flex justify-end gap-2 mt-1",
  saveButton: "bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded text-xs font-medium flex items-center gap-1.5 transition-colors shadow-sm",
  cancelButton: "text-slate-400 hover:text-white px-4 py-1.5 rounded text-xs font-medium transition-colors",
  
  // Field containers
  fieldContainer: "space-y-1",
  fieldGrid: "grid grid-cols-2 gap-2",
};

/**
 * Form field wrapper component styles
 * Consistent spacing and structure for all form fields
 */
export const FORM_LAYOUT = {
  container: "w-64 space-y-2 text-xs text-slate-200",
  section: "space-y-2",
  divider: "border-t border-slate-700/50 my-3",
};

/**
 * Z-index layers for modals, menus, and overlays
 * Ensures consistent stacking order
 */
export const Z_LAYERS = {
  contextMenu: "z-[10000]",
  contextMenuBackdrop: "z-[10001]",
  colorPicker: "z-[10002]",
  modal: "z-[10010]",
  modalBackdrop: "z-[10009]",
  toast: "z-[10020]",
};
