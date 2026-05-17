import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SeverityBadge } from '../severity-badge';

describe('SeverityBadge', () => {
  it('renders label for each severity', () => {
    (['critical', 'high', 'medium', 'low', 'info'] as const).forEach((s) => {
      const { unmount } = render(<SeverityBadge severity={s} />);
      expect(screen.getAllByText(/risk|critical|informational/i).length).toBeGreaterThan(0);
      unmount();
    });
  });
});
