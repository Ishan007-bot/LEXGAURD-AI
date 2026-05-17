'use client';

import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  [
    'group inline-flex items-center justify-center gap-2 whitespace-nowrap',
    'font-mono uppercase tracking-widest2 text-[11px]',
    'transition-[color,background-color,border-color,transform] duration-200 ease-out',
    'disabled:pointer-events-none disabled:opacity-40',
    'focus-visible:outline-none',
  ].join(' '),
  {
    variants: {
      variant: {
        default:
          'bg-ink text-background border border-ink hover:bg-redline hover:border-redline',
        outline:
          'bg-transparent text-ink border border-ink hover:bg-ink hover:text-background',
        ghost:
          'bg-transparent text-ink hover:bg-evidence',
        redline:
          'bg-redline text-background border border-redline hover:bg-redline-deep hover:border-redline-deep',
        link:
          'bg-transparent text-ink underline underline-offset-[6px] decoration-rule hover:decoration-redline hover:text-redline px-0',
      },
      size: {
        default: 'h-11 px-5',
        sm: 'h-9 px-3 text-[10px]',
        lg: 'h-12 px-7 text-[12px]',
        icon: 'h-11 w-11',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
    );
  },
);
Button.displayName = 'Button';

export { buttonVariants };
