import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 px-2 py-1 border font-mono uppercase tracking-widest2 text-[10px]',
  {
    variants: {
      variant: {
        default: 'border-ink text-ink bg-transparent',
        muted: 'border-rule text-ink-soft bg-transparent',
        inverted: 'border-ink bg-ink text-background',
        redline: 'border-redline bg-redline text-background',
        outline: 'border-rule text-ink bg-transparent',
        critical: 'border-risk-critical bg-risk-critical text-background',
        high: 'border-risk-high bg-risk-high text-background',
        medium: 'border-risk-medium bg-risk-medium text-background',
        low: 'border-risk-low bg-risk-low text-background',
        info: 'border-risk-info bg-risk-info text-background',
      },
    },
    defaultVariants: { variant: 'default' },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { badgeVariants };
