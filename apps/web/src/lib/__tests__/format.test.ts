import { describe, expect, it } from 'vitest';
import { categoryLabel, severityWeight, severityLabel } from '../format';

describe('format', () => {
  it('categoryLabel title-cases underscored values', () => {
    expect(categoryLabel('non_compete')).toBe('Non Compete');
    expect(categoryLabel('limitation_of_liability')).toBe('Limitation Of Liability');
    expect(categoryLabel('other')).toBe('Other');
  });

  it('severityWeight orders worst → best', () => {
    expect(severityWeight('critical')).toBeGreaterThan(severityWeight('high'));
    expect(severityWeight('high')).toBeGreaterThan(severityWeight('medium'));
    expect(severityWeight('medium')).toBeGreaterThan(severityWeight('low'));
    expect(severityWeight('low')).toBeGreaterThan(severityWeight('info'));
  });

  it('severityLabel covers every severity', () => {
    (['critical', 'high', 'medium', 'low', 'info'] as const).forEach((s) => {
      expect(typeof severityLabel[s]).toBe('string');
      expect(severityLabel[s].length).toBeGreaterThan(0);
    });
  });
});
