import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    container: { center: true, padding: '1.5rem', screens: { '2xl': '1320px' } },
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        background: 'hsl(var(--background))',
        surface: 'hsl(var(--surface))',
        'surface-sunk': 'hsl(var(--surface-sunk))',
        ink: 'hsl(var(--ink))',
        'ink-soft': 'hsl(var(--ink-soft))',
        rule: 'hsl(var(--rule))',
        redline: 'hsl(var(--redline))',
        'redline-deep': 'hsl(var(--redline-deep))',
        verdict: 'hsl(var(--verdict))',
        evidence: 'hsl(var(--evidence))',
        foreground: 'hsl(var(--foreground))',
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        risk: {
          critical: 'hsl(var(--risk-critical))',
          high: 'hsl(var(--risk-high))',
          medium: 'hsl(var(--risk-medium))',
          low: 'hsl(var(--risk-low))',
          info: 'hsl(var(--risk-info))',
        },
      },
      // Editorial aesthetic — sharp corners.
      borderRadius: { lg: '0px', md: '0px', sm: '0px', DEFAULT: '0px' },
      fontFamily: {
        display: ['var(--font-display)', 'Instrument Serif', 'serif'],
        mono: ['var(--font-mono)', 'JetBrains Mono', 'monospace'],
      },
      letterSpacing: {
        widest2: '0.22em',
      },
    },
  },
  plugins: [],
};

export default config;
