'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';
import { Gavel, Scale, ShieldAlert, Sparkles, Quote } from 'lucide-react';
import { cn } from '@/lib/utils';
import { agentRole, agentNumeral } from '@/lib/format';
import type { AgentName } from '@/lib/api';

const icons: Record<AgentName, typeof Gavel> = {
  prosecutor: ShieldAlert,
  defender: Scale,
  judge: Gavel,
  negotiator: Sparkles,
  extractor: Quote,
};

const accent: Record<AgentName, string> = {
  prosecutor: 'text-redline border-redline',
  defender: 'text-ink border-ink',
  judge: 'text-verdict border-verdict',
  negotiator: 'text-ink border-ink',
  extractor: 'text-ink-soft border-rule',
};

interface Props {
  agent: AgentName;
  argument: string;
  citations?: string[];
  /** ms before this turn starts revealing */
  startDelay?: number;
  /** chars-per-second for the type-on effect */
  speed?: number;
  /** Render fully immediately (skip typing) */
  instant?: boolean;
}

export function AgentTurn({
  agent,
  argument,
  citations = [],
  startDelay = 0,
  speed = 80,
  instant = false,
}: Props) {
  const Icon = icons[agent];
  const [typed, setTyped] = useState(instant ? argument : '');
  const [revealed, setRevealed] = useState(instant);

  useEffect(() => {
    if (instant) return;
    const startTimer = setTimeout(() => {
      setRevealed(true);
      let i = 0;
      const interval = setInterval(() => {
        i += Math.max(1, Math.round(speed / 30)); // chars added per tick
        if (i >= argument.length) {
          setTyped(argument);
          clearInterval(interval);
        } else {
          setTyped(argument.slice(0, i));
        }
      }, 33);
    }, startDelay);
    return () => clearTimeout(startTimer);
  }, [argument, startDelay, speed, instant]);

  return (
    <AnimatePresence>
      {revealed && (
        <motion.article
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
          className={cn(
            'grid md:grid-cols-12 gap-4 md:gap-6 border-l-2 pl-5 md:pl-6 py-4',
            accent[agent],
          )}
        >
          <header className="md:col-span-3 flex md:block items-center gap-3">
            <Icon className="h-5 w-5" aria-hidden />
            <div>
              <p className="label">
                {agentNumeral[agent]} · {agent}
              </p>
              <p className="text-[11px] text-ink-soft mt-1">{agentRole[agent]}</p>
            </div>
          </header>
          <div className="md:col-span-9">
            <p className="display text-[26px] md:text-[30px] leading-[1.1]">
              <span>“{typed}</span>
              <motion.span
                aria-hidden
                className="inline-block w-[0.5ch] h-[0.9em] -mb-1 ml-0.5 bg-current align-middle"
                animate={{ opacity: typed === argument ? 0 : [1, 0, 1] }}
                transition={{
                  duration: 0.7,
                  repeat: typed === argument ? 0 : Infinity,
                  ease: 'linear',
                }}
              />
              <span>”</span>
            </p>
            {citations.length > 0 && typed === argument && (
              <motion.ul
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.15 }}
                className="mt-4 flex flex-wrap gap-x-4 gap-y-1 label"
              >
                {citations.map((c) => (
                  <li key={c} className="before:content-['§'] before:mr-1.5 before:text-ink-soft">
                    {c}
                  </li>
                ))}
              </motion.ul>
            )}
          </div>
        </motion.article>
      )}
    </AnimatePresence>
  );
}
