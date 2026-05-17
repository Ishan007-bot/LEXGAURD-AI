'use client';

import * as React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { RiskGauge } from '@/components/risk-gauge';
import { SeverityHeatmap } from '@/components/severity-heatmap';
import { ClauseCard } from '@/components/clause-card';
import { ScenarioSimulator } from '@/components/scenario-simulator';
import { TtsPlayer } from '@/components/tts-player';
import { useAuth } from '@/lib/auth-context';
import { useAsync } from '@/hooks/use-async';
import {
  ApiError,
  api,
  type DocumentAnalysisDTO,
  type DocumentWithClausesDTO,
} from '@/lib/api';
import { categoryLabel, formatDate, severityWeight } from '@/lib/format';
import { fadeUp, ruleSweep, stagger } from '@/lib/motion';

export default function DocumentPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id ?? '';
  const { user, getIdToken, loading } = useAuth();

  const docState = useAsync(
    async (): Promise<DocumentWithClausesDTO | null> => {
      const token = await getIdToken();
      if (!token) return null;
      return api.getDocument(id, token);
    },
    [id, user?.uid ?? null],
    { enabled: !!user && !!id },
  );

  const [analysis, setAnalysis] = React.useState<DocumentAnalysisDTO | null>(null);
  const [running, setRunning] = React.useState(false);
  const [runError, setRunError] = React.useState<string | null>(null);
  const [selectedClauseId, setSelectedClauseId] = React.useState<string | null>(null);

  const runAnalysis = async () => {
    setRunError(null);
    setRunning(true);
    try {
      const token = await getIdToken();
      if (!token) throw new Error('Auth token unavailable.');
      const result = await api.createAnalysis(id, token);
      setAnalysis(result);
    } catch (e) {
      setRunError(e instanceof ApiError ? e.message : (e as Error).message);
    } finally {
      setRunning(false);
    }
  };

  if (loading || docState.loading) {
    return <div aria-busy="true" className="container py-24 label">Pulling the file from the registry…</div>;
  }
  if (!user) {
    return (
      <section className="container py-24">
        <h1 className="display text-5xl">Please sign in.</h1>
        <Button asChild className="mt-6">
          <Link href="/signin">→ Sign in</Link>
        </Button>
      </section>
    );
  }
  if (docState.error || !docState.data) {
    return (
      <section className="container py-24">
        <p className="label">Error</p>
        <h1 className="display text-4xl mt-2">
          {docState.error?.message ?? 'Document not found.'}
        </h1>
      </section>
    );
  }

  const doc = docState.data;
  const analysisByClause = new Map(
    (analysis?.clauses ?? []).map((c) => [c.clause_id, c] as const),
  );
  const heatmapItems =
    analysis?.clauses
      .slice()
      .sort((a, b) => severityWeight(b.severity) - severityWeight(a.severity))
      .map((c) => ({ id: c.clause_id, severity: c.severity })) ?? [];

  return (
    <section className="container py-12 md:py-20">
      {/* Masthead */}
      <motion.header
        variants={stagger(0, 0.07)}
        initial="hidden"
        animate="visible"
        className="grid md:grid-cols-12 gap-6 items-end mb-10"
      >
        <motion.div variants={fadeUp} className="md:col-span-2">
          <Link href="/documents" className="label hover:text-redline">
            ← All files
          </Link>
        </motion.div>
        <motion.div variants={fadeUp} className="md:col-span-7">
          <p className="label">{doc.source.replace('_', ' ')} · {categoryLabel(doc.document_type)}</p>
          <h1 className="display text-5xl md:text-7xl leading-[0.95] mt-2 break-words">
            {doc.filename ?? doc.source_url ?? 'Untitled document'}
          </h1>
        </motion.div>
        <motion.dl variants={fadeUp} className="md:col-span-3 grid grid-cols-2 gap-4 text-[12px]">
          <div>
            <dt className="label">Clauses</dt>
            <dd className="display text-3xl tabular-nums">{doc.clauses.length}</dd>
          </div>
          <div>
            <dt className="label">Filed</dt>
            <dd className="text-ink mt-1">{formatDate(doc.created_at)}</dd>
          </div>
        </motion.dl>
      </motion.header>

      <motion.div variants={ruleSweep} initial="hidden" animate="visible" className="h-px bg-ink mb-12" />

      {/* Pre-analysis CTA */}
      {!analysis && (
        <div className="grid md:grid-cols-12 gap-8 items-start mb-16">
          <div className="md:col-span-6">
            <p className="label">§ Hearing not yet convened</p>
            <h2 className="display text-4xl md:text-5xl mt-3 leading-[1.05]">
              Convene the court to begin <span className="italic">adversarial review.</span>
            </h2>
            <p className="text-[13px] text-ink-soft mt-4 max-w-md leading-relaxed">
              The Prosecutor, Defender, Judge, and Negotiator will work through {doc.clauses.length}{' '}
              clauses. Expected duration: 30–90 seconds. Cost on Gemini routing: ~${(
                doc.clauses.length * 0.006
              ).toFixed(2)}.
            </p>
            <Button
              size="lg"
              variant="redline"
              onClick={() => void runAnalysis()}
              disabled={running}
              className="mt-6"
            >
              {running ? 'In session…' : '→ Convene the court'}
            </Button>
            {runError && (
              <p role="alert" className="label text-redline mt-3">
                {runError}
              </p>
            )}
          </div>

          {/* Pre-analysis clause list */}
          <Card className="md:col-span-6">
            <CardContent className="p-0 max-h-[480px] overflow-y-auto">
              <ul className="divide-y divide-rule">
                {doc.clauses.map((c, i) => (
                  <li key={c.id} className="p-4">
                    <div className="flex items-baseline gap-3 mb-1">
                      <span className="label tabular-nums">№ {String(i + 1).padStart(2, '0')}</span>
                      <span className="label text-ink">{categoryLabel(c.category)}</span>
                    </div>
                    <p className="text-[13px] text-ink-soft line-clamp-3">{c.text}</p>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Post-analysis dashboard */}
      {analysis && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6 }}
            className="grid md:grid-cols-12 gap-x-8 gap-y-12 items-start mb-20"
          >
            <div className="md:col-span-5 flex flex-col items-center md:items-start gap-8 md:pl-4">
              <RiskGauge score={analysis.overall_risk_score} />
              <div className="mt-12 w-full flex justify-center md:justify-start">
                <TtsPlayer analysisId={analysis.id} />
              </div>
            </div>
            <div className="md:col-span-7 md:pl-8 md:border-l md:border-rule">
              <p className="label">Bench summary · case no. {analysis.id.slice(0, 8)}</p>
              <p className="display text-3xl md:text-4xl leading-[1.1] mt-3 italic">
                “{analysis.summary}”
              </p>
              <div className="mt-8">
                <SeverityHeatmap
                  items={heatmapItems}
                  selectedId={selectedClauseId}
                  onSelect={(cid) => {
                    setSelectedClauseId(cid);
                    document.getElementById(`clause-${cid}`)?.scrollIntoView({
                      behavior: 'smooth',
                      block: 'start',
                    });
                  }}
                />
              </div>
            </div>
          </motion.div>

          <div>
            <div className="grid md:grid-cols-12 gap-6 items-end mb-6">
              <div className="md:col-span-3">
                <p className="label">§ Transcript</p>
              </div>
              <div className="md:col-span-9">
                <h2 className="display text-4xl md:text-5xl">
                  Per-clause <span className="italic">debate.</span>
                </h2>
              </div>
            </div>
            <ol className="border-t border-rule">
              {doc.clauses.map((clause, i) => {
                const ca = analysisByClause.get(clause.id);
                if (!ca) return null;
                return (
                  <ClauseCard
                    key={clause.id}
                    index={i}
                    clause={clause}
                    analysis={ca}
                    defaultOpen={i === 0}
                    playOnOpen={true}
                  />
                );
              })}
            </ol>
          </div>

          <ScenarioSimulator analysisId={analysis.id} />
        </>
      )}
    </section>
  );
}
