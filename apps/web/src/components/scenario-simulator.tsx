'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SeverityBadge } from '@/components/severity-badge';
import { api, ApiError, type SimulateResponse } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

const PRESETS = [
  'What if I miss a payment by 5 days?',
  'What if I quit after 6 months?',
  'What if the company changes the privacy policy?',
  'What if I accept a competing offer next year?',
  'What if I refuse to sign the redlines?',
] as const;

const EASE = [0.16, 1, 0.3, 1] as const;

interface Props {
  analysisId: string;
}

export function ScenarioSimulator({ analysisId }: Props) {
  const { getIdToken } = useAuth();
  const [scenario, setScenario] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<SimulateResponse | null>(null);

  const run = async (text: string) => {
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const token = await getIdToken();
      if (!token) throw new Error('Sign-in required.');
      const res = await api.simulate(analysisId, text, token);
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : (e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="border-t border-rule pt-12 mt-12">
      <div className="grid md:grid-cols-12 gap-6 items-end mb-6">
        <div className="md:col-span-3">
          <p className="label">§ What-if</p>
        </div>
        <div className="md:col-span-9">
          <h2 className="display text-4xl md:text-5xl leading-[0.95]">
            Real-world <span className="italic">consequences.</span>
          </h2>
          <p className="text-[14px] text-ink-soft mt-3 max-w-xl">
            Pick a scenario you&apos;re worried about. The agents will walk through
            exactly what each clause does to you under that situation.
          </p>
        </div>
      </div>

      <div className="grid md:grid-cols-12 gap-6">
        <div className="md:col-span-5">
          <div className="border border-rule bg-surface p-5">
            <p className="label mb-3">Common scenarios</p>
            <ul className="flex flex-col gap-2">
              {PRESETS.map((preset) => (
                <li key={preset}>
                  <button
                    type="button"
                    onClick={() => {
                      setScenario(preset);
                      void run(preset);
                    }}
                    disabled={loading}
                    className="w-full text-left px-3 py-2 border border-rule hover:border-ink hover:bg-evidence transition-colors text-[13px] leading-relaxed group disabled:opacity-50"
                  >
                    <span className="inline-block mr-2 text-ink-soft group-hover:text-redline transition-colors">
                      →
                    </span>
                    {preset}
                  </button>
                </li>
              ))}
            </ul>

            <div className="mt-5 pt-5 border-t border-rule">
              <p className="label mb-2">Custom scenario</p>
              <textarea
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                rows={3}
                maxLength={500}
                placeholder="e.g. What if the company is acquired in two years?"
                className="w-full border border-rule bg-background px-3 py-2 text-[13px] font-mono leading-relaxed focus:border-ink focus:outline-none"
              />
              <div className="flex items-center justify-between mt-2">
                <span className="text-[11px] text-ink-soft tabular-nums">
                  {scenario.length}/500
                </span>
                <Button
                  size="sm"
                  variant="redline"
                  disabled={loading || scenario.trim().length < 4}
                  onClick={() => void run(scenario)}
                >
                  {loading ? 'Simulating…' : '→ Simulate'}
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div className="md:col-span-7">
          <AnimatePresence mode="wait">
            {loading && (
              <motion.div
                key="loading"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="border border-rule bg-surface p-8 min-h-[280px] flex flex-col items-center justify-center gap-3"
              >
                <Sparkles className="h-6 w-6 text-redline animate-pulse" aria-hidden />
                <p className="label">Simulating consequences…</p>
              </motion.div>
            )}

            {!loading && error && (
              <motion.div
                key="error"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="border border-redline bg-surface p-6 flex items-start gap-3"
              >
                <AlertCircle className="h-5 w-5 text-redline mt-0.5 shrink-0" aria-hidden />
                <p className="text-[13px] text-redline">{error}</p>
              </motion.div>
            )}

            {!loading && !error && result && (
              <motion.article
                key={result.headline}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.55, ease: EASE }}
                className="border border-rule bg-surface p-6 md:p-8 min-h-[280px]"
              >
                <div className="flex items-start justify-between gap-3 mb-4">
                  <SeverityBadge severity={result.severity} animate />
                  <p className="label">Hypothetical · not legal advice</p>
                </div>
                <h3 className="display text-3xl md:text-[34px] leading-[1.1]">
                  “{result.headline}”
                </h3>
                <ul className="mt-6 space-y-3 border-l-2 border-rule pl-5">
                  {result.consequences.map((c, i) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.4, delay: i * 0.12, ease: EASE }}
                      className="text-[14px] leading-relaxed"
                    >
                      <span className="label mr-2">№ {i + 1}</span>
                      {c}
                    </motion.li>
                  ))}
                </ul>
                <div className="mt-6 pt-5 border-t border-rule">
                  <p className="label mb-2">Counsel&apos;s advice</p>
                  <p className="display text-xl italic text-redline leading-tight">
                    {result.advice}
                  </p>
                </div>
              </motion.article>
            )}

            {!loading && !error && !result && (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="border border-dashed border-rule p-8 text-center min-h-[280px] flex flex-col items-center justify-center gap-2"
              >
                <p className="display text-2xl italic text-ink-soft">
                  Pick a scenario to begin.
                </p>
                <p className="text-[12px] text-ink-soft">
                  Each simulation costs about $0.005 in Gemini Flash tokens.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
