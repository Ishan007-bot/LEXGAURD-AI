'use client';

import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

interface Props {
  score: number; // 0-100
  className?: string;
  size?: number;
}

function scoreColor(s: number): string {
  if (s >= 80) return 'hsl(var(--risk-critical))';
  if (s >= 60) return 'hsl(var(--risk-high))';
  if (s >= 40) return 'hsl(var(--risk-medium))';
  if (s >= 20) return 'hsl(var(--risk-low))';
  return 'hsl(var(--risk-info))';
}

function scoreVerdict(s: number): string {
  if (s >= 80) return 'Do not sign without changes';
  if (s >= 60) return 'Negotiate before signing';
  if (s >= 40) return 'Review carefully';
  if (s >= 20) return 'Standard, but watch the clauses';
  return 'No material risk detected';
}

export function RiskGauge({ score, className, size = 280 }: Props) {
  const clamped = Math.max(0, Math.min(100, score));
  const stroke = 14;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const visibleArc = 0.78; // ~280deg arc
  const arcLength = circumference * visibleArc;

  const motionScore = useMotionValue(0);
  const offset = useTransform(motionScore, (v) => arcLength - (v / 100) * arcLength);
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const controls = animate(motionScore, clamped, {
      duration: 1.4,
      ease: [0.16, 1, 0.3, 1],
    });
    const unsub = motionScore.on('change', (v) => setDisplay(Math.round(v)));
    return () => {
      controls.stop();
      unsub();
    };
  }, [clamped, motionScore]);

  const color = scoreColor(clamped);

  return (
    <div className={cn('relative inline-flex flex-col items-center', className)}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-[126deg]"
        aria-hidden
      >
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="hsl(var(--rule))"
          strokeWidth={stroke}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="butt"
        />
        {/* Progress */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={`${arcLength} ${circumference}`}
          style={{ strokeDashoffset: offset }}
          strokeLinecap="butt"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pt-2">
        <span className="label">Risk score</span>
        <motion.span
          key={clamped}
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.45 }}
          className="display tabular-nums leading-none text-[88px] mt-1"
          style={{ color }}
        >
          {display}
        </motion.span>
        <span className="label mt-2 text-ink">/ 100</span>
      </div>
      <p
        className="absolute -bottom-10 left-1/2 -translate-x-1/2 whitespace-nowrap text-[13px] italic"
        style={{ color }}
      >
        “{scoreVerdict(clamped)}”
      </p>
    </div>
  );
}
