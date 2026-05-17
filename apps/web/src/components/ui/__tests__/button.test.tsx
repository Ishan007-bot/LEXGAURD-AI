import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { Button } from '../button';

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('fires onClick', async () => {
    const handler = vi.fn();
    render(<Button onClick={handler}>Go</Button>);
    await userEvent.click(screen.getByRole('button', { name: /go/i }));
    expect(handler).toHaveBeenCalledOnce();
  });

  it('respects disabled', async () => {
    const handler = vi.fn();
    render(
      <Button onClick={handler} disabled>
        Nope
      </Button>,
    );
    await userEvent.click(screen.getByRole('button', { name: /nope/i }));
    expect(handler).not.toHaveBeenCalled();
  });

  it('has a 44px-min tap target via size=default (h-11)', () => {
    render(<Button>Tap</Button>);
    const btn = screen.getByRole('button', { name: /tap/i });
    expect(btn.className).toContain('h-11');
  });

  it('redline variant uses redline classes', () => {
    render(<Button variant="redline">Sign</Button>);
    const btn = screen.getByRole('button', { name: /sign/i });
    expect(btn.className).toContain('bg-redline');
  });
});
