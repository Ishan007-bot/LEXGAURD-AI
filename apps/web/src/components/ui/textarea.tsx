import * as React from 'react';
import { cn } from '@/lib/utils';

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        'flex min-h-[200px] w-full border border-rule bg-surface px-4 py-3 text-[14px] text-ink font-mono leading-relaxed',
        'placeholder:text-ink-soft',
        'focus:border-ink focus:outline-none',
        'disabled:cursor-not-allowed disabled:opacity-40',
        className,
      )}
      {...props}
    />
  ),
);
Textarea.displayName = 'Textarea';
