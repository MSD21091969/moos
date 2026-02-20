import { HTMLAttributes, forwardRef } from 'react';
import { getContextTheme } from '../utils/theme';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  context?: string;
  title?: string;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, context, title, style, children, ...props }, ref) => {
    const theme = getContextTheme(context);

    const cardStyle = {
      backgroundColor: 'white',
      border: `1px solid ${context ? theme.border : '#e5e7eb'}`,
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      overflow: 'hidden',
      ...style,
    };

    const headerStyle = {
      padding: '12px 16px',
      backgroundColor: context ? theme.bg : '#f9fafb',
      borderBottom: `1px solid ${context ? theme.border : '#e5e7eb'}`,
      fontWeight: 600,
      color: context ? theme.primary : '#374151',
    };

    const bodyStyle = {
      padding: '16px',
    };

    return (
      <div ref={ref} style={cardStyle} {...props}>
        {title && <div style={headerStyle}>{title}</div>}
        <div style={bodyStyle}>{children}</div>
      </div>
    );
  }
);

Card.displayName = 'Card';
