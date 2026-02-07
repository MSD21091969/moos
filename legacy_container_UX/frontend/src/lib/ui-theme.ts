export const MENU_STYLES = {
  // Container
  container: "z-[10000] min-w-[12rem] overflow-hidden rounded-lg border border-slate-700/50 bg-[rgba(15,23,42,0.50)] p-1.5 text-slate-100 shadow-xl backdrop-blur-md animate-in fade-in-80 zoom-in-95",
  
  // Items
  item: "relative flex cursor-default select-none items-center rounded-md px-2.5 py-2 text-sm outline-none transition-colors focus:bg-blue-600/30 focus:text-white data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
  
  // Submenu
  submenuTrigger: "flex cursor-default select-none items-center rounded-md px-2.5 py-2 text-sm outline-none focus:bg-blue-600/30 focus:text-white data-[state=open]:bg-blue-600/30 data-[state=open]:text-white data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
  
  // Separator
  separator: "-mx-1 my-1.5 h-px bg-slate-700/50",
  
  // Icons
  icon: "mr-2.5 h-4 w-4",
  
  // Shortcuts
  shortcut: "ml-auto text-xs tracking-widest text-slate-400",
  
  // Destructive
  destructive: "text-red-400 focus:text-red-400 focus:bg-red-900/20",
};
