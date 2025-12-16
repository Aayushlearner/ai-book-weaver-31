import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

interface MaterialButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const MaterialButton = forwardRef<HTMLButtonElement, MaterialButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-smooth focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 relative overflow-hidden group';
    
    const variantStyles = {
      primary: 'bg-primary text-primary-foreground material-shadow-md hover:material-shadow-lg hover:bg-primary-light active:material-shadow-sm',
      secondary: 'bg-secondary text-secondary-foreground material-shadow-sm hover:material-shadow-md hover:bg-secondary/80',
      accent: 'gradient-accent text-accent-foreground material-shadow-md hover:material-shadow-lg hover:scale-[1.02]',
      outline: 'border-2 border-primary text-primary hover:bg-primary/10 material-shadow-sm',
      ghost: 'hover:bg-secondary/80 text-foreground',
    };

    const sizeStyles = {
      sm: 'h-9 px-4 text-sm',
      md: 'h-11 px-6 text-base',
      lg: 'h-14 px-8 text-lg',
    };

    return (
      <button
        ref={ref}
        className={cn(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        <span className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity bg-white/10" />
        {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
        {children}
      </button>
    );
  }
);

MaterialButton.displayName = 'MaterialButton';
