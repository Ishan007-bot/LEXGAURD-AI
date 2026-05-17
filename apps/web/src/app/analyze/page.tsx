'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, Globe } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ApiError, api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { fadeUp, stagger } from '@/lib/motion';

type Tab = 'upload' | 'text' | 'url';

const TABS: { id: Tab; label: string; icon: typeof Upload; subtitle: string }[] = [
  { id: 'upload', label: 'File', icon: Upload, subtitle: 'PDF · DOCX · 25 MiB' },
  { id: 'text', label: 'Paste', icon: FileText, subtitle: 'Online terms · plain text' },
  { id: 'url', label: 'URL', icon: Globe, subtitle: 'Live T&C scrape' },
];

interface State {
  kind: 'idle' | 'working' | 'done' | 'error';
  message?: string;
}

export default function AnalyzePage() {
  const router = useRouter();
  const { user, getIdToken, configured, loading } = useAuth();
  const [tab, setTab] = React.useState<Tab>('upload');
  const [file, setFile] = React.useState<File | null>(null);
  const [text, setText] = React.useState('');
  const [url, setUrl] = React.useState('');
  const [state, setState] = React.useState<State>({ kind: 'idle' });

  if (loading) {
    return <div aria-busy="true" className="container py-24 label">Convening the court…</div>;
  }
  if (!configured || !user) {
    return (
      <section className="container py-24">
        <Card className="max-w-xl mx-auto">
          <CardContent className="space-y-4">
            <p className="label">§ Authentication</p>
            <h2 className="display text-4xl">A clerk must verify your identity first.</h2>
            <p className="text-[13px] text-ink-soft">
              Sign in to file a document. Your contracts never leave Google Cloud.
            </p>
            <Button asChild>
              <Link href="/signin">→ Sign in</Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    );
  }

  const submit = async () => {
    setState({ kind: 'working' });
    try {
      const token = await getIdToken();
      if (!token) throw new Error('Auth token unavailable.');

      if (tab === 'upload') {
        if (!file) return;
        const doc = await api.uploadFile(file, token);
        router.push(`/documents/${doc.id}`);
        return;
      }

      if (tab === 'text') {
        const doc = await api.createFromText({ text }, token);
        router.push(`/documents/${doc.id}`);
        return;
      }

      const doc = await api.createFromUrl({ url }, token);
      router.push(`/documents/${doc.id}`);
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : e instanceof Error ? e.message : 'Failed.';
      setState({ kind: 'error', message: msg });
    }
  };

  const ready =
    (tab === 'upload' && !!file) ||
    (tab === 'text' && text.trim().length >= 20) ||
    (tab === 'url' && url.trim().length > 8);

  return (
    <section className="container py-12 md:py-20">
      <motion.header
        variants={stagger(0, 0.06)}
        initial="hidden"
        animate="visible"
        className="grid md:grid-cols-12 gap-6 items-end mb-12 md:mb-16"
      >
        <motion.div variants={fadeUp} className="md:col-span-2">
          <p className="label">§ 01 · Intake</p>
        </motion.div>
        <motion.div variants={fadeUp} className="md:col-span-7">
          <h1 className="display text-5xl md:text-7xl leading-[0.95]">
            File a document <span className="italic">for review.</span>
          </h1>
        </motion.div>
        <motion.p variants={fadeUp} className="md:col-span-3 text-[13px] text-ink-soft md:pl-6 md:border-l md:border-rule">
          Three intake paths. Pick whatever&apos;s closest to where the contract lives right now.
        </motion.p>
      </motion.header>

      <div className="grid md:grid-cols-12 gap-8 items-start">
        {/* Tabs */}
        <nav aria-label="Intake method" className="md:col-span-3">
          <ul className="border-y border-rule divide-y divide-rule">
            {TABS.map((t) => {
              const Icon = t.icon;
              const active = tab === t.id;
              return (
                <li key={t.id}>
                  <button
                    type="button"
                    onClick={() => setTab(t.id)}
                    className={`group w-full flex items-start gap-3 px-3 py-5 text-left transition-colors ${
                      active ? 'bg-ink text-background' : 'hover:bg-evidence'
                    }`}
                  >
                    <Icon className="h-5 w-5 mt-1" aria-hidden />
                    <span className="flex-1">
                      <span className="display text-2xl block leading-none">{t.label}</span>
                      <span
                        className={`label block mt-2 ${
                          active ? 'text-background/70' : 'text-ink-soft'
                        }`}
                      >
                        {t.subtitle}
                      </span>
                    </span>
                    {active && <span aria-hidden>→</span>}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Panel */}
        <div className="md:col-span-9">
          <Card>
            <CardContent className="p-8 md:p-12 min-h-[420px]">
              <AnimatePresence mode="wait">
                <motion.div
                  key={tab}
                  initial={{ opacity: 0, x: 16 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -16 }}
                  transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                >
                  {tab === 'upload' && (
                    <div className="space-y-5">
                      <Label htmlFor="file">Document</Label>
                      <Input
                        id="file"
                        type="file"
                        accept=".pdf,.docx,.doc,.txt,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                      />
                      {file && (
                        <p className="text-[13px] text-ink-soft border-l-2 border-rule pl-3">
                          Filed: <span className="text-ink">{file.name}</span> ·{' '}
                          <span className="tabular-nums">{Math.ceil(file.size / 1024)} KB</span>
                        </p>
                      )}
                      <p className="text-[12px] text-ink-soft">
                        Files are PII-redacted before any AI sees them. Originals stay in your
                        Cloud Storage bucket.
                      </p>
                    </div>
                  )}

                  {tab === 'text' && (
                    <div className="space-y-3">
                      <Label htmlFor="text">Document text</Label>
                      <Textarea
                        id="text"
                        rows={14}
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Paste the contract, offer letter, or terms of service…"
                      />
                      <p className="text-[12px] text-ink-soft tabular-nums">
                        {text.length.toLocaleString()} chars · 100,000 max
                      </p>
                    </div>
                  )}

                  {tab === 'url' && (
                    <div className="space-y-3">
                      <Label htmlFor="url">Page URL</Label>
                      <Input
                        id="url"
                        type="url"
                        placeholder="https://example.com/terms"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                      />
                      <p className="text-[12px] text-ink-soft">
                        We fetch and clean the page once. Only public, HTTPS URLs.
                      </p>
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            </CardContent>
            <div className="border-t border-rule p-6 md:p-8 flex items-center justify-between gap-4">
              <p className="label">{state.kind === 'error' ? <span className="text-redline">{state.message}</span> : 'Step 1 of 2'}</p>
              <Button
                disabled={!ready || state.kind === 'working'}
                onClick={() => void submit()}
                size="lg"
                variant="redline"
              >
                {state.kind === 'working' ? 'Filing…' : '→ Submit to clerk'}
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
