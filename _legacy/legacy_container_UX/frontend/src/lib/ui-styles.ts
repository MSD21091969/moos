// Unified styling constants for consistent UI across all components
// Single source of truth for transparency, borders, shadows (DRY principle)

export const UI_STYLES = {
  // Transparent overlays (menus, modals, panels)
  overlay: {
    base: 'bg-[rgba(15,23,42,0.50)] backdrop-blur-md border border-slate-700/50',
    shadow: 'shadow-2xl',
    rounded: 'rounded-lg',
    full: 'bg-[rgba(15,23,42,0.50)] backdrop-blur-md border border-slate-700/50 rounded-lg shadow-2xl',
  },
  
  // Chat/panels
  panel: {
    base: 'bg-[rgba(15,23,42,0.50)] backdrop-blur-md border border-slate-700/50',
    shadow: 'shadow-2xl',
    rounded: 'rounded-lg',
    full: 'bg-[rgba(15,23,42,0.50)] backdrop-blur-md border border-slate-700/50 rounded-lg shadow-2xl',
  },
  
  // Context menus
  contextMenu: {
    base: 'bg-[rgba(15,23,42,0.50)] backdrop-blur-md border border-slate-700/50',
    shadow: 'shadow-2xl',
    rounded: 'rounded-lg',
    full: 'bg-[rgba(15,23,42,0.50)] backdrop-blur-md border border-slate-700/50 rounded-lg shadow-2xl',
  },
  
  // Modals
  modal: {
    base: 'bg-[rgba(15,23,42,0.50)] backdrop-blur-md border border-slate-700/50',
    shadow: 'shadow-2xl',
    rounded: 'rounded-lg',
    full: 'bg-[rgba(15,23,42,0.50)] backdrop-blur-md border border-slate-700/50 rounded-lg shadow-2xl',
  },
  
  // Menu items (for context menus and dropdowns)
  menuItem: {
    base: 'w-full text-left px-4 py-2 text-sm font-medium text-white transition-colors',
    hover: 'hover:bg-blue-500/30',
    full: 'w-full text-left px-4 py-2 text-sm font-medium text-white hover:bg-blue-500/30 transition-colors',
  },
  
  // Detailed menu styles (Radix UI compatible)
  menu: {
    container: 'z-[10000] min-w-[12rem] overflow-hidden rounded-lg border border-slate-700/50 bg-[rgba(15,23,42,0.50)] p-1.5 text-slate-100 shadow-xl backdrop-blur-md',
    item: 'relative flex cursor-default select-none items-center rounded-md px-2.5 py-2 text-sm outline-none transition-colors focus:bg-blue-600/30 focus:text-white data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
    submenuTrigger: 'flex cursor-default select-none items-center rounded-md px-2.5 py-2 text-sm outline-none focus:bg-blue-600/30 focus:text-white data-[state=open]:bg-blue-600/30 data-[state=open]:text-white data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
    separator: '-mx-1 my-1.5 h-px bg-slate-700/50',
    icon: 'mr-2.5 h-4 w-4',
    shortcut: 'ml-auto text-xs tracking-widest text-slate-400',
    destructive: 'text-red-400 focus:text-red-400 focus:bg-red-900/20',
  },
  
  // Buttons
  button: {
    primary: 'px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
    secondary: 'px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors disabled:opacity-50',
    danger: 'px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
  },
} as const;
