import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, request } from '../api';

describe('api.request', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    global.fetch = originalFetch;
  });

  it('returns parsed JSON on 2xx', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ ok: 1 }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      }),
    );
    await expect(request<{ ok: number }>('/x')).resolves.toEqual({ ok: 1 });
  });

  it('attaches bearer token when supplied', async () => {
    const spy = vi
      .mocked(global.fetch as typeof fetch)
      .mockResolvedValue(
        new Response('null', { status: 200, headers: { 'content-type': 'application/json' } }),
      );
    await request('/x', { token: 'tok' });
    const init = spy.mock.calls[0]?.[1];
    expect((init?.headers as Record<string, string>).Authorization).toBe('Bearer tok');
  });

  it('throws ApiError on 4xx with envelope', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({ error: { code: 'unauthenticated', message: 'no', requestId: 'r1' } }),
        { status: 401, headers: { 'content-type': 'application/json' } },
      ),
    );
    await expect(request('/x')).rejects.toMatchObject({
      status: 401,
      code: 'unauthenticated',
      requestId: 'r1',
    } satisfies Partial<ApiError>);
  });
});
