'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { Button } from './ui/button';
import { ThemeToggle } from './theme-toggle';
import { LexLogo } from './lex-mark';
import { useAuth } from '@/lib/auth-context';
import { cn } from '@/lib/utils';

const NAV = [
  { href: '/analyze', label: 'Analyze' },
  { href: '/documents', label: 'Files' },
  { href: '/#how-it-works', label: 'How it works' },
] as const;

const EASE = [0.16, 1, 0.3, 1] as const;

export function Header() {
  const pathname = usePathname();
  const { user, loading, configured, signInWithGoogle, signOut } = useAuth();

  return (
    <motion.header
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: EASE }}
      className="sticky top-0 z-40 border-b border-rule bg-background/85 backdrop-blur-md"
    >
      <div className="container flex h-[72px] items-center justify-between gap-6">
        <Link href="/" aria-label="LexGuard home" className="group inline-flex items-center gap-4">
          <LexLogo />
          <span className="label hidden lg:inline border-l border-rule pl-3 ml-1">
            Est. 2026 · Adversarial AI
          </span>
        </Link>

        <nav aria-label="Primary" className="hidden md:flex items-center gap-1">
          {NAV.map((item) => {
            const active =
              item.href === pathname ||
              (item.href !== '/' && pathname?.startsWith(item.href.replace('/#', '/')));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'label relative px-3 py-2 transition-colors hover:text-ink',
                  active ? 'text-ink' : 'text-ink-soft',
                )}
              >
                {item.label}
                {active && (
                  <motion.span
                    layoutId="nav-underline"
                    className="absolute left-3 right-3 -bottom-1 h-px bg-redline"
                    transition={{ duration: 0.4, ease: EASE }}
                  />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          {loading ? (
            <span aria-live="polite" className="label">…</span>
          ) : user ? (
            <Button variant="outline" size="sm" onClick={() => void signOut()}>
              Sign out
            </Button>
          ) : (
            <Button
              variant="redline"
              size="sm"
              onClick={() => void signInWithGoogle()}
              disabled={!configured}
              aria-disabled={!configured}
              title={configured ? undefined : 'Firebase is not configured'}
            >
              Sign in
            </Button>
          )}
        </div>
      </div>
    </motion.header>
  );
}
