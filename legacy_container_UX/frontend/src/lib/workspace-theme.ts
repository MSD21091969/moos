/**
 * Workspace Theme Configuration
 *
 * Centralized theme settings for workspace-level and session-level styling
 * Apply consistently across SessionNode, SessionEditModal, SessionContextMenu
 */

export interface WorkspaceTheme {
  // Session Node Colors
  sessionColors: {
    active: string;
    completed: string;
    expired: string;
    archived: string;
  };

  // UI Component Colors
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  error: string;

  // Dark mode support
  dark: {
    background: string;
    surface: string;
    border: string;
    text: string;
    textMuted: string;
  };

  // Light mode
  light: {
    background: string;
    surface: string;
    border: string;
    text: string;
    textMuted: string;
  };
}

export const defaultWorkspaceTheme: WorkspaceTheme = {
  sessionColors: {
    active: '#10b981', // green-500
    completed: '#3b82f6', // blue-500
    expired: '#6b7280', // gray-500
    archived: '#f59e0b', // amber-500
  },

  primary: '#3b82f6', // blue-500
  secondary: '#8b5cf6', // violet-500
  success: '#10b981', // green-500
  warning: '#f59e0b', // amber-500
  error: '#ef4444', // red-500

  dark: {
    background: '#0f172a', // slate-950
    surface: '#1e293b', // slate-800
    border: '#334155', // slate-700
    text: '#f1f5f9', // slate-100
    textMuted: '#94a3b8', // slate-400
  },

  light: {
    background: '#ffffff',
    surface: '#f8fafc', // slate-50
    border: '#e2e8f0', // slate-200
    text: '#0f172a', // slate-950
    textMuted: '#64748b', // slate-500
  },
};

/**
 * Convert hex color to rgba
 */
export function hexToRgba(hex: string, opacity: number): string {
  if (!hex || !hex.startsWith('#') || hex.length !== 7) {
    return `rgba(59, 130, 246, ${opacity})`; // Fallback to blue
  }
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

/**
 * Get status-specific color
 */
export function getStatusColor(
  status: 'active' | 'completed' | 'expired' | 'archived',
  theme: WorkspaceTheme = defaultWorkspaceTheme
): string {
  return theme.sessionColors[status];
}

/**
 * Tailwind classes for status badges (used in UI)
 */
export const statusBadgeClasses = {
  active: 'bg-green-500 text-white',
  completed: 'bg-blue-500 text-white',
  expired: 'bg-gray-500 text-white',
  archived: 'bg-amber-500 text-white',
  idle: 'bg-slate-500 text-white',
  working: 'bg-purple-500 text-white',
  error: 'bg-red-500 text-white',
} as const;

/**
 * Tailwind classes for status buttons (used in modal)
 */
export const statusButtonClasses = {
  active: {
    selected: 'bg-green-500 text-white hover:bg-green-600',
    default:
      'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600',
  },
  completed: {
    selected: 'bg-blue-500 text-white hover:bg-blue-600',
    default:
      'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600',
  },
  expired: {
    selected: 'bg-slate-500 text-white hover:bg-slate-600',
    default:
      'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600',
  },
  archived: {
    selected: 'bg-amber-500 text-white hover:bg-amber-600',
    default:
      'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600',
  },
} as const;

/**
 * Common input field classes for consistent styling
 */
export const inputClasses =
  'w-full px-3 py-2 border rounded-md transition-colors ' +
  'border-slate-300 dark:border-slate-600 ' +
  'bg-white dark:bg-slate-800 ' +
  'text-slate-900 dark:text-white ' +
  'placeholder:text-slate-400 dark:placeholder:text-slate-500 ' +
  'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent';

/**
 * Common button classes
 */
export const buttonClasses = {
  primary:
    'px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
  secondary:
    'px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-md transition-colors disabled:opacity-50',
  danger:
    'px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
} as const;

/**
 * Modal classes for consistent modal styling
 */
export const modalClasses = {
  overlay: 'fixed inset-0 bg-black/50 backdrop-blur-sm z-[9999] flex items-center justify-center p-4',
  backdrop: 'fixed inset-0 bg-black bg-opacity-50 z-[10001]',
  container: 'fixed inset-0 z-[10002] flex items-center justify-center p-4 pointer-events-none',
  content: 'bg-[rgba(15,23,42,0.85)] backdrop-blur-md rounded-lg shadow-2xl border border-slate-700 w-full p-6 relative',
  header: 'flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700',
  headerTitle: 'text-xl font-semibold text-gray-900 dark:text-white',
  body: 'p-6 space-y-4',
  footer: 'flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700',
} as const;

/**
 * Label classes
 */
export const labelClasses = 'block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1';
