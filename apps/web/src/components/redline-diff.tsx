'use client';

import { motion } from 'framer-motion';
import { useMemo } from 'react';
import { cn } from '@/lib/utils';

interface Props {
  original: string;
  proposed: string;
  className?: string;
}

interface Token {
  text: string;
  kind: 'same' | 'removed' | 'added';
}

/**
 * Word-level Longest-Common-Subsequence diff. Good enough for redline display;
 * not byte-perfect, but easy on the eyes and dependency-free.
 */
function diff(a: string, b: string): Token[] {
  const ax = a.split(/(\s+)/);
  const bx = b.split(/(\s+)/);
  const n = ax.length;
  const m = bx.length;
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i]![j] = ax[i] === bx[j] ? dp[i + 1]![j + 1]! + 1 : Math.max(dp[i + 1]![j]!, dp[i]![j + 1]!);
    }
  }
  const out: Token[] = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (ax[i] === bx[j]) {
      out.push({ text: ax[i]!, kind: 'same' });
      i++;
      j++;
    } else if (dp[i + 1]![j]! >= dp[i]![j + 1]!) {
      out.push({ text: ax[i]!, kind: 'removed' });
      i++;
    } else {
      out.push({ text: bx[j]!, kind: 'added' });
      j++;
    }
  }
  while (i < n) out.push({ text: ax[i++]!, kind: 'removed' });
  while (j < m) out.push({ text: bx[j++]!, kind: 'added' });
  return out;
}

export function RedlineDiff({ original, proposed, className }: Props) {
  const tokens = useMemo(() => diff(original, proposed), [original, proposed]);

  return (
    <div className={cn('grid gap-px bg-rule border border-rule', className)}>
      <div className="bg-surface p-5">
        <p className="label mb-3">Original clause</p>
        <p className="text-[14px] leading-relaxed">
          {tokens.map((t, i) =>
            t.kind === 'added' ? null : (
              <motion.span
                key={i}
                initial={{ backgroundColor: 'transparent' }}
                animate={
                  t.kind === 'removed' ? { backgroundColor: 'hsl(var(--redline) / 0.16)' } : {}
                }
                transition={{ duration: 0.6, delay: 0.05 * i }}
                className={cn(t.kind === 'removed' && 'strike-redline')}
              >
                {t.text}
              </motion.span>
            ),
          )}
        </p>
      </div>

      <div className="bg-surface p-5">
        <p className="label mb-3 text-redline">Proposed redline</p>
        <p className="text-[14px] leading-relaxed">
          {tokens.map((t, i) =>
            t.kind === 'removed' ? null : (
              <motion.span
                key={i}
                initial={{ backgroundColor: 'transparent' }}
                animate={
                  t.kind === 'added'
                    ? { backgroundColor: 'hsl(var(--risk-low) / 0.18)' }
                    : {}
                }
                transition={{ duration: 0.6, delay: 0.05 * i }}
                className={cn(t.kind === 'added' && 'underline decoration-risk-low')}
              >
                {t.text}
              </motion.span>
            ),
          )}
        </p>
      </div>
    </div>
  );
}
