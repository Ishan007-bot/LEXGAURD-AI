import * as React from 'react';
import { cn } from '@/lib/utils';

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(
        'flex h-12 w-full border border-rule bg-surface px-4 py-2 text-[14px] text-ink font-mono',
        'placeholder:text-ink-soft placeholder:font-mono',
        'focus:border-ink focus:outline-none',
        'disabled:cursor-not-allowed disabled:opacity-40',
        'file:mr-3 file:border-0 file:bg-transparent file:text-[11px] file:uppercase file:tracking-widest2 file:text-ink-soft',
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = 'Input';
