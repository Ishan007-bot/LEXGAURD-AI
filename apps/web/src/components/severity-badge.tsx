'use client';

import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { stamp } from '@/lib/motion';
import { severityLabel } from '@/lib/format';
import type { Severity } from '@/lib/api';

const variantMap: Record<Severity, 'critical' | 'high' | 'medium' | 'low' | 'info'> = {
  critical: 'critical',
  high: 'high',
  medium: 'medium',
  low: 'low',
  info: 'info',
};

export function SeverityBadge({ severity, animate = false }: { severity: Severity; animate?: boolean }) {
  const variant = variantMap[severity];
  const content = <Badge variant={variant}>{severityLabel[severity]}</Badge>;
  if (!animate) return content;
  return (
    <motion.span variants={stamp} initial="hidden" animate="visible" className="inline-block">
      {content}
    </motion.span>
  );
}
