import { cn } from '@/lib/utils';

/**
 * LexGuard mark. A redacted column of text — four ruled lines with a redline
 * strike across the middle. Reads as both "ledger" and "contract under review."
 */
export function LexMark({ className, size = 28 }: { className?: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      className={cn('inline-block shrink-0', className)}
      aria-hidden
    >
      {/* Outer frame */}
      <rect
        x="2"
        y="2"
        width="36"
        height="36"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      />
      {/* Ruled "text" lines */}
      <rect x="9" y="9" width="22" height="1.6" fill="currentColor" />
      <rect x="9" y="14" width="22" height="1.6" fill="currentColor" />
      <rect x="9" y="19" width="22" height="1.6" fill="currentColor" />
      <rect x="9" y="24" width="22" height="1.6" fill="currentColor" />
      <rect x="9" y="29" width="14" height="1.6" fill="currentColor" />
      {/* Redline */}
      <line
        x1="4"
        y1="19.8"
        x2="36"
        y2="19.8"
        stroke="hsl(var(--redline))"
        strokeWidth="2.5"
      />
    </svg>
  );
}

/**
 * The combined mark + wordmark used in the header.
 */
export function LexLogo({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-3', className)}>
      <LexMark className="text-ink" size={32} />
      <span className="display text-[26px] leading-none tracking-tight">
        Lex<span className="italic text-redline">Guard</span>
      </span>
    </span>
  );
}
