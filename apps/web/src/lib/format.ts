import type { AgentName, Severity, ClauseCategory } from './api';

export const severityLabel: Record<Severity, string> = {
  critical: 'Critical',
  high: 'High risk',
  medium: 'Medium risk',
  low: 'Low risk',
  info: 'Informational',
};

export const severityTone: Record<Severity, string> = {
  critical: 'redline',
  high: 'redline',
  medium: 'verdict',
  low: 'ink-soft',
  info: 'ink-soft',
};

export const severityVerdict: Record<Severity, string> = {
  critical: 'Do not sign without changes.',
  high: 'Negotiate before signing.',
  medium: 'Review carefully.',
  low: 'Standard, but watch.',
  info: 'No material risk.',
};

export const agentRole: Record<AgentName, string> = {
  extractor: 'Court reporter',
  prosecutor: 'For the people',
  defender: 'For the drafter',
  judge: 'Bench',
  negotiator: 'Counsel for revision',
};

export const agentNumeral: Record<AgentName, string> = {
  extractor: 'I.',
  prosecutor: 'II.',
  defender: 'III.',
  judge: 'IV.',
  negotiator: 'V.',
};

export function categoryLabel(c: ClauseCategory): string {
  return c
    .split('_')
    .map((w) => w[0]!.toUpperCase() + w.slice(1))
    .join(' ');
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' });
}

export function severityWeight(s: Severity): number {
  return { critical: 5, high: 4, medium: 3, low: 2, info: 1 }[s];
}
