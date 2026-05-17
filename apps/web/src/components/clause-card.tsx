'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { categoryLabel } from '@/lib/format';
import type { ClauseAnalysisDTO, ClauseDTO } from '@/lib/api';
import { SeverityBadge } from './severity-badge';
import { AgentTurn } from './agent-turn';
import { RedlineDiff } from './redline-diff';

interface Props {
  index: number;
  clause: ClauseDTO;
  analysis: ClauseAnalysisDTO;
  defaultOpen?: boolean;
  /** When opening for the first time, play the debate sequentially. */
  playOnOpen?: boolean;
}

export function ClauseCard({ index, clause, analysis, defaultOpen = false, playOnOpen = true }: Props) {
  const [open, setOpen] = useState(defaultOpen);
  const [hasOpened, setHasOpened] = useState(defaultOpen);
  const animateDebate = playOnOpen && !hasOpened;

  const handleToggle = () => {
    setOpen((o) => !o);
    if (!open) setHasOpened(true);
  };

  return (
    <motion.section
      id={`clause-${clause.id}`}
      layout
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.45 }}
      className="border-b border-rule"
    >
      <button
        type="button"
        onClick={handleToggle}
        aria-expanded={open}
        aria-controls={`clause-${clause.id}-body`}
        className="w-full text-left grid md:grid-cols-12 gap-4 md:gap-6 py-6 md:py-8 hover:bg-evidence/40 transition-colors px-1"
      >
        <div className="md:col-span-1">
          <span className="label">№ {String(index + 1).padStart(2, '0')}</span>
        </div>
        <div className="md:col-span-2 flex flex-wrap gap-2 items-start">
          <SeverityBadge severity={analysis.severity} />
          <span className="label">{categoryLabel(clause.category)}</span>
        </div>
        <div className="md:col-span-7">
          <p className="display text-2xl md:text-[28px] leading-[1.15]">
            {analysis.plain_english}
          </p>
          <p className="text-[12px] text-ink-soft mt-2 line-clamp-2">{clause.text}</p>
        </div>
        <div className="md:col-span-2 flex md:justify-end items-start gap-3">
          <span className="display text-4xl tabular-nums leading-none">
            {analysis.risk_score}
          </span>
          <ChevronDown
            className={cn('h-5 w-5 transition-transform mt-2', open && 'rotate-180')}
            aria-hidden
          />
        </div>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id={`clause-${clause.id}-body`}
            key="body"
            layout
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <div className="grid md:grid-cols-12 gap-6 px-1 pb-10">
              <aside className="md:col-span-3 md:border-r md:border-rule md:pr-6">
                <p className="label">Original text</p>
                <p className="text-[13px] leading-relaxed mt-2 text-ink-soft">{clause.text}</p>
                {analysis.citations.length > 0 && (
                  <div className="mt-6">
                    <p className="label">Authorities</p>
                    <ul className="mt-2 space-y-1 text-[12px] text-ink-soft">
                      {analysis.citations.map((c) => (
                        <li key={c} className="before:content-['§'] before:mr-1.5">
                          {c}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </aside>

              <div className="md:col-span-9 space-y-2">
                <p className="label">Transcript of debate</p>
                {analysis.debate.map((turn, i) => (
                  <AgentTurn
                    key={`${clause.id}-${i}`}
                    agent={turn.agent}
                    argument={turn.argument}
                    citations={turn.citations}
                    instant={!animateDebate}
                    startDelay={animateDebate ? i * 1200 : 0}
                  />
                ))}

                {analysis.suggested_redline && (
                  <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                      duration: 0.6,
                      delay: animateDebate ? analysis.debate.length * 1.2 + 0.4 : 0,
                    }}
                    className="pt-6 mt-4 border-t border-rule"
                  >
                    <p className="label mb-3">Counsel for revision · proposed redline</p>
                    <RedlineDiff
                      original={clause.text}
                      proposed={analysis.suggested_redline}
                    />
                  </motion.div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
}
