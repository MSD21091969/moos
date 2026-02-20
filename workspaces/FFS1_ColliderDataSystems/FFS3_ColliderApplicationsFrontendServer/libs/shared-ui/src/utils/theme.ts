export const NodeContextThemes = {
  FILESYST: {
    primary: '#10b981', // green-500
    bg: '#ecfdf5',      // green-50
    border: '#34d399',  // green-400
    label: 'Local Filesystem',
    description: 'Safe, local workspace context'
  },
  ADMIN: {
    primary: '#ef4444', // red-500
    bg: '#fef2f2',      // red-50
    border: '#f87171',  // red-400
    label: 'System Admin',
    description: 'High-risk system configuration context'
  },
  CLOUD: {
    primary: '#3b82f6', // blue-500
    bg: '#eff6ff',      // blue-50
    border: '#60a5fa',  // blue-400
    label: 'Cloud Resources',
    description: 'Remote, network-dependent context'
  }
} as const;

export type NodeContextType = keyof typeof NodeContextThemes;

export const getContextTheme = (context?: string) => {
  const key = (context?.toUpperCase() as NodeContextType) || 'FILESYST';
  return NodeContextThemes[key] || NodeContextThemes.FILESYST;
};
