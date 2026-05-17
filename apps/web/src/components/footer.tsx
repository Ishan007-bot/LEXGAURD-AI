export function Footer() {
  return (
    <footer className="border-t border-rule mt-24">
      <div className="container py-10 grid gap-6 md:grid-cols-3">
        <div>
          <p className="display text-2xl">
            Lex<span className="italic text-redline">Guard</span>
          </p>
          <p className="label mt-2">A clerk for the contracts you don&apos;t read.</p>
        </div>
        <div className="md:text-center">
          <p className="label">No. {new Date().getFullYear().toString().padStart(4, '0')}</p>
          <p className="text-[12px] text-ink-soft mt-1">
            Informational analysis. Not legal advice.
          </p>
        </div>
        <div className="md:text-right">
          <p className="label">Built on</p>
          <p className="text-[12px] text-ink-soft mt-1">
            Vertex AI · Cloud Run · Firestore · Document AI · DLP
          </p>
        </div>
      </div>
    </footer>
  );
}
