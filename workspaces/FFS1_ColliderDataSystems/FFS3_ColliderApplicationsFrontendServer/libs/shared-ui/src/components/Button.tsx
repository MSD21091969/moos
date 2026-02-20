import { ButtonHTMLAttributes, forwardRef } from 'react';
import { getContextTheme } from '../utils/theme';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  context?: string; // FILESYST | ADMIN | CLOUD
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', context, style, children, ...props }, ref) => {
    const theme = getContextTheme(context);
    
    const baseStyle = {
      padding: '8px 16px',
      borderRadius: '4px',
      border: 'none',
      cursor: 'pointer',
      fontWeight: 500,
      transition: 'all 0.2s',
      ...style,
    };

    let variantStyle = {};
    if (variant === 'primary') {
      variantStyle = {
        backgroundColor: theme.primary,
        color: 'white',
      };
    } else if (variant === 'secondary') {
      variantStyle = {
        backgroundColor: 'transparent',
        border: `1px solid ${theme.border}`,
        color: theme.primary,
      };
    } else if (variant === 'danger') {
      variantStyle = {
        backgroundColor: '#ef4444',
        color: 'white',
      };
    }

    return (
      <button
        ref={ref}
        style={{ ...baseStyle, ...variantStyle }}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
