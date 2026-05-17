'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';
import { useAsync } from '@/hooks/use-async';
import { api, type DocumentDTO } from '@/lib/api';
import { formatDate } from '@/lib/format';

async function fetchDocs(token: string | null) {
  if (!token) return { items: [] as DocumentDTO[], next_cursor: null };
  return api.listDocuments(token);
}

export default function DocumentsPage() {
  const { user, getIdToken, loading } = useAuth();
  const { data, error } = useAsync(
    async () => fetchDocs(await getIdToken()),
    [user?.uid ?? null],
    { enabled: !!user },
  );

  if (loading) return <div className="container py-24 label">Loading…</div>;
  if (!user) {
    return (
      <section className="container py-24">
        <h1 className="display text-5xl">Sign in to see your files.</h1>
        <Button asChild className="mt-6">
          <Link href="/signin">→ Sign in</Link>
        </Button>
      </section>
    );
  }

  const items = data?.items ?? [];

  return (
    <section className="container py-12 md:py-20">
      <header className="grid md:grid-cols-12 gap-6 items-end mb-12">
        <div className="md:col-span-2">
          <p className="label">§ Files</p>
        </div>
        <div className="md:col-span-7">
          <h1 className="display text-5xl md:text-7xl">Your case files.</h1>
        </div>
        <div className="md:col-span-3 md:text-right">
          <Button asChild variant="redline" size="lg">
            <Link href="/analyze">→ File a new document</Link>
          </Button>
        </div>
      </header>

      {error && (
        <p role="alert" className="text-redline label mb-6">
          Could not load files: {error.message}
        </p>
      )}

      {items.length === 0 ? (
        <div className="border-t border-b border-rule py-20 text-center">
          <p className="display text-3xl italic text-ink-soft">No files on the docket yet.</p>
          <p className="text-[13px] text-ink-soft mt-2">Start with one of the intake methods.</p>
        </div>
      ) : (
        <ul className="border-t border-rule">
          {items.map((doc, i) => (
            <motion.li
              key={doc.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: i * 0.04, ease: [0.16, 1, 0.3, 1] }}
              className="border-b border-rule group"
            >
              <Link
                href={`/documents/${doc.id}`}
                className="grid md:grid-cols-12 gap-4 items-baseline py-6 px-1 hover:bg-evidence/40 transition-colors"
              >
                <span className="label md:col-span-1 tabular-nums">
                  {String(i + 1).padStart(3, '0')}
                </span>
                <h3 className="display text-2xl md:text-3xl md:col-span-5 group-hover:italic transition-all">
                  {doc.filename ?? doc.source_url ?? 'Untitled document'}
                </h3>
                <span className="label md:col-span-2">{doc.source.replace('_', ' ')}</span>
                <span className="label md:col-span-2 tabular-nums">
                  {doc.clause_count} clauses
                </span>
                <span className="label md:col-span-2 md:text-right">
                  {formatDate(doc.created_at)}
                </span>
              </Link>
            </motion.li>
          ))}
        </ul>
      )}
    </section>
  );
}
