'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { severityLabel } from '@/lib/format';
import type { Severity } from '@/lib/api';

const bg: Record<Severity, string> = {
  critical: 'bg-risk-critical',
  high: 'bg-risk-high',
  medium: 'bg-risk-medium',
  low: 'bg-risk-low',
  info: 'bg-risk-info',
};

interface Props {
  items: { id: string; severity: Severity; label?: string }[];
  onSelect?: (id: string) => void;
  selectedId?: string | null;
}

export function SeverityHeatmap({ items, onSelect, selectedId }: Props) {
  if (items.length === 0) return null;
  return (
    <div>
      <div className="label mb-2 flex items-center justify-between">
        <span>Severity ledger · {items.length} clauses</span>
        <span className="text-ink-soft normal-case tracking-normal text-[10px]">click a cell</span>
      </div>
      <ol className="flex flex-wrap gap-1.5">
        {items.map((item, i) => (
          <motion.li
            key={item.id}
            initial={{ opacity: 0, scale: 0.85, y: 6 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.35, delay: i * 0.015, ease: [0.16, 1, 0.3, 1] }}
          >
            <button
              type="button"
              onClick={() => onSelect?.(item.id)}
              aria-label={`Clause ${i + 1}: ${severityLabel[item.severity]}`}
              className={cn(
                'h-8 w-8 border border-ink/10 hover:scale-110 hover:border-ink transition-transform',
                bg[item.severity],
                selectedId === item.id && 'ring-2 ring-ink ring-offset-2 ring-offset-background',
              )}
            >
              <span className="sr-only">
                Clause {i + 1}: {severityLabel[item.severity]}
              </span>
              <span className="block text-[10px] text-background/80 font-mono leading-8">
                {i + 1}
              </span>
            </button>
          </motion.li>
        ))}
      </ol>
      <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 label">
        {(['critical', 'high', 'medium', 'low', 'info'] as Severity[]).map((s) => (
          <span key={s} className="inline-flex items-center gap-2">
            <span className={cn('inline-block h-2.5 w-2.5', bg[s])} aria-hidden />
            {severityLabel[s]}
          </span>
        ))}
      </div>
    </div>
  );
}
