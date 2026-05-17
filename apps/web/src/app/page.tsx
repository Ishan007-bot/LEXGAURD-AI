'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Gavel, Scale, ShieldAlert, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

const EASE = [0.16, 1, 0.3, 1] as const;

const agents = [
  {
    name: 'Prosecutor',
    role: 'Assumes the counterparty is hostile.',
    icon: ShieldAlert,
  },
  {
    name: 'Defender',
    role: 'Argues the clause is standard practice.',
    icon: Scale,
  },
  {
    name: 'Judge',
    role: 'Weighs both sides. Issues a verdict.',
    icon: Gavel,
  },
  {
    name: 'Negotiator',
    role: 'Drafts the exact redline you should propose.',
    icon: Sparkles,
  },
] as const;

const exhibits = [
  ['Exhibit A', 'Offer letters', 'Non-competes, IP assignment, hidden clawbacks.'],
  ['Exhibit B', 'Terms of service', 'Auto-renewals, arbitration clauses, data resale.'],
  ['Exhibit C', 'Tickets & policies', 'Liability waivers, refund traps, jurisdiction tricks.'],
] as const;

export default function Home() {
  return (
    <>
      {/* ───────────────── HERO ───────────────── */}
      <section className="container relative pt-16 pb-24 md:pt-24 md:pb-32">
        <div className="grid md:grid-cols-12 gap-y-8 items-end">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: EASE }}
            className="md:col-span-2"
          >
            <p className="label">No. 001 / Adversarial intelligence</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: EASE, delay: 0.1 }}
            className="md:col-span-7"
          >
            <h1 className="display text-[clamp(64px,11vw,168px)] tracking-tight leading-[0.92]">
              Read the
              <br />
              <span className="italic">fine</span>{' '}
              <span className="relative inline-block">
                print
                <motion.span
                  aria-hidden
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ duration: 0.6, ease: EASE, delay: 1.0 }}
                  style={{ transformOrigin: 'left center' }}
                  className="absolute left-0 right-0 top-1/2 h-[6px] bg-redline -rotate-2"
                />
              </span>
              ,
              <br />
              before it reads <span className="italic">you</span>.
            </h1>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: EASE, delay: 0.25 }}
            className="md:col-span-3 md:pl-8 md:border-l md:border-rule"
          >
            <p className="text-[13px] leading-relaxed text-ink-soft">
              LexGuard convenes a private court of four AI agents inside Vertex&nbsp;AI. They
              <em> prosecute</em>, <em>defend</em>, <em>judge</em>, and <em>negotiate</em>
              every clause in your contract — before you sign anything.
            </p>
            <div className="mt-6 flex flex-col gap-2">
              <Button asChild size="lg">
                <Link href="/analyze">→ File a document</Link>
              </Button>
              <Button asChild variant="link" size="sm">
                <Link href="#how-it-works">See the procedure</Link>
              </Button>
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.9, ease: EASE, delay: 0.3 }}
          style={{ transformOrigin: 'left center' }}
          className="mt-16 md:mt-24 h-px bg-ink"
        />

        <div className="mt-6 grid md:grid-cols-12 gap-x-6 gap-y-3 text-[12px] text-ink-soft">
          {[
            ['Filed at', 'asia-south1 · Cloud Run'],
            ['Counsel', 'Gemini 2.5 Pro · Flash'],
            ['Evidence', 'Document AI · DLP redacted'],
            ['Ledger', 'Firestore · GCS'],
          ].map(([label, value], i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, ease: EASE, delay: 0.5 + i * 0.07 }}
              className="md:col-span-3"
            >
              <p className="label">{label}</p>
              <p className="font-mono">{value}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ───────────────── THE BENCH ───────────────── */}
      <section id="how-it-works" className="container py-16 md:py-24 border-t border-rule">
        <div className="grid md:grid-cols-12 gap-8 mb-12">
          <div className="md:col-span-3">
            <p className="label">§ 02 · The bench</p>
          </div>
          <div className="md:col-span-9">
            <h2 className="display text-5xl md:text-6xl leading-[0.95]">
              Four agents. <br className="hidden md:block" />
              <span className="italic">One verdict.</span>
            </h2>
            <p className="mt-4 max-w-2xl text-[14px] text-ink-soft leading-relaxed">
              Most tools summarise. LexGuard <em>argues</em>. Each agent has a job, a model
              budget, and a position. Their conflict is the feature.
            </p>
          </div>
        </div>

        <ol className="grid md:grid-cols-4 gap-px bg-rule border border-rule">
          {agents.map((agent, i) => {
            const Icon = agent.icon;
            return (
              <motion.li
                key={agent.name}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.65, ease: EASE, delay: i * 0.08 }}
                className="bg-surface p-6 md:p-8 flex flex-col gap-4 min-h-[260px] relative group hover:bg-evidence transition-colors"
              >
                <div className="flex items-baseline justify-between">
                  <span className="label">{`0${i + 1}`}</span>
                  <Icon className="h-5 w-5 text-ink-soft group-hover:text-redline transition-colors" aria-hidden />
                </div>
                <h3 className="display text-4xl mt-auto">{agent.name}</h3>
                <p className="text-[13px] text-ink-soft leading-relaxed">{agent.role}</p>
              </motion.li>
            );
          })}
        </ol>
      </section>

      {/* ───────────────── THE DOCKET ───────────────── */}
      <section className="container py-16 md:py-24 border-t border-rule">
        <div className="grid md:grid-cols-12 gap-8 mb-12">
          <div className="md:col-span-3">
            <p className="label">§ 03 · The docket</p>
          </div>
          <div className="md:col-span-9">
            <h2 className="display text-5xl md:text-6xl leading-[0.95]">
              Everything you&apos;d normally <br className="hidden md:block" />
              <span className="italic text-redline">just sign.</span>
            </h2>
          </div>
        </div>

        <ul className="divide-y divide-rule border-t border-b border-rule">
          {exhibits.map(([id, name, blurb], i) => (
            <motion.li
              key={id}
              initial={{ opacity: 0, x: -24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.7, ease: EASE, delay: i * 0.1 }}
              className="grid md:grid-cols-12 items-baseline gap-4 py-6 group"
            >
              <span className="label md:col-span-2">{id}</span>
              <h3 className="display text-3xl md:text-4xl md:col-span-4 group-hover:italic transition-all duration-300">
                {name}
              </h3>
              <p className="text-[13px] md:text-[14px] text-ink-soft md:col-span-5 leading-relaxed">
                {blurb}
              </p>
              <span
                aria-hidden
                className="hidden md:inline-block md:col-span-1 text-right text-ink-soft group-hover:text-redline group-hover:translate-x-1 transition-all"
              >
                →
              </span>
            </motion.li>
          ))}
        </ul>
      </section>

      {/* ───────────────── CTA ───────────────── */}
      <section className="container py-20 md:py-28 border-t border-rule">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.4 }}
          transition={{ duration: 0.7, ease: EASE }}
          className="grid md:grid-cols-12 gap-6 items-end"
        >
          <div className="md:col-span-8">
            <p className="label">§ 04 · Motion to proceed</p>
            <h2 className="display text-5xl md:text-7xl mt-4">
              Stop signing things you <span className="italic">haven&apos;t read.</span>
            </h2>
          </div>
          <div className="md:col-span-4 md:text-right">
            <Button asChild size="lg" variant="redline">
              <Link href="/analyze">→ File a document</Link>
            </Button>
            <p className="label mt-3">Free during the trial. No card required.</p>
          </div>
        </motion.div>
      </section>
    </>
  );
}
