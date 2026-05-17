'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

interface AsyncState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
}

/** A small async-state hook used across pages — easier than wiring SWR for a hackathon. */
export function useAsync<T, A extends unknown[]>(
  fn: (...args: A) => Promise<T>,
  args: A,
  options: { enabled?: boolean } = {},
): AsyncState<T> & { reload: () => void } {
  const { enabled = true } = options;
  const [state, setState] = useState<AsyncState<T>>({ data: null, error: null, loading: enabled });
  const counter = useRef(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;
  const serializedArgs = JSON.stringify(args);

  const run = useCallback(() => {
    if (!enabled) return;
    const current = ++counter.current;
    setState((s) => ({ ...s, loading: true, error: null }));
    void fnRef
      .current(...args)
      .then((data) => {
        if (current === counter.current) setState({ data, error: null, loading: false });
      })
      .catch((error: Error) => {
        if (current === counter.current) setState({ data: null, error, loading: false });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, serializedArgs]);

  useEffect(run, [run]);

  return { ...state, reload: run };
}
