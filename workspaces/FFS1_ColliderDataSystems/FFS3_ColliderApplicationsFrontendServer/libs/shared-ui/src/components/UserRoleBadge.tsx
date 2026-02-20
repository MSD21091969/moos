import { HTMLAttributes } from 'react';

export interface UserRoleBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  role: string;
  type: 'system' | 'app';
}

export function UserRoleBadge({ role, type, style, ...props }: UserRoleBadgeProps) {
  const isSystem = type === 'system';
  
  // Color mapping for roles
  let color = '#6b7280'; // gray-500
  let bg = '#f3f4f6';    // gray-100
  
  const roleLower = role.toLowerCase();
  
  if (roleLower === 'superadmin') {
    color = '#7c3aed'; // violet-600
    bg = '#f5f3ff';    // violet-50
  } else if (roleLower === 'collider_admin') {
    color = '#db2777'; // pink-600
    bg = '#fdf2f8';    // pink-50
  } else if (roleLower === 'app_admin') {
    color = '#059669'; // emerald-600
    bg = '#ecfdf5';    // emerald-50
  } else if (roleLower === 'app_user') {
    color = '#2563eb'; // blue-600
    bg = '#eff6ff';    // blue-50
  }

  const badgeStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 600,
    backgroundColor: bg,
    color: color,
    border: `1px solid ${color}20`, // 20% opacity border
    ...style,
  };

  return (
    <span style={badgeStyle} {...props}>
      {isSystem ? '🔒 ' : '👤 '}
      {role}
    </span>
  );
}
