'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Pause, Volume2, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { api, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

interface Props {
  analysisId: string;
  className?: string;
}

type State =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'ready'; src: string }
  | { kind: 'error'; message: string };

export function TtsPlayer({ analysisId, className }: Props) {
  const { getIdToken } = useAuth();
  const [state, setState] = React.useState<State>({ kind: 'idle' });
  const [playing, setPlaying] = React.useState(false);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);

  React.useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    const onEnd = () => setPlaying(false);
    el.addEventListener('ended', onEnd);
    return () => el.removeEventListener('ended', onEnd);
  }, [state]);

  const fetchAudio = async () => {
    setState({ kind: 'loading' });
    try {
      const token = await getIdToken();
      if (!token) throw new Error('Sign-in required.');
      const res = await api.tts(analysisId, token);
      const src = `data:${res.mime_type};base64,${res.audio_base64}`;
      setState({ kind: 'ready', src });
      // Play immediately on first generation
      setTimeout(() => {
        const el = audioRef.current;
        if (el) {
          el.play().catch(() => undefined);
          setPlaying(true);
        }
      }, 50);
    } catch (e) {
      setState({
        kind: 'error',
        message: e instanceof ApiError ? e.message : (e as Error).message,
      });
    }
  };

  const toggle = () => {
    if (state.kind === 'idle' || state.kind === 'error') {
      void fetchAudio();
      return;
    }
    if (state.kind === 'ready') {
      const el = audioRef.current;
      if (!el) return;
      if (playing) {
        el.pause();
        setPlaying(false);
      } else {
        el.play().catch(() => undefined);
        setPlaying(true);
      }
    }
  };

  const labelText =
    state.kind === 'loading'
      ? 'Synthesising voice…'
      : state.kind === 'error'
        ? 'Tap to retry'
        : playing
          ? 'Now playing'
          : state.kind === 'ready'
            ? 'Play again'
            : 'Read it to me';

  return (
    <div className={cn('inline-flex items-center gap-3', className)}>
      <button
        type="button"
        onClick={toggle}
        disabled={state.kind === 'loading'}
        aria-label={labelText}
        className={cn(
          'group inline-flex h-12 w-12 items-center justify-center border-2',
          'transition-colors disabled:opacity-50',
          state.kind === 'error'
            ? 'border-redline text-redline hover:bg-redline hover:text-background'
            : playing
              ? 'border-redline bg-redline text-background'
              : 'border-ink text-ink hover:bg-ink hover:text-background',
        )}
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={state.kind + (playing ? 'p' : 'q')}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.2 }}
          >
            {state.kind === 'loading' ? (
              <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
            ) : playing ? (
              <Pause className="h-5 w-5" aria-hidden />
            ) : state.kind === 'ready' ? (
              <Play className="h-5 w-5" aria-hidden />
            ) : (
              <Volume2 className="h-5 w-5" aria-hidden />
            )}
          </motion.span>
        </AnimatePresence>
      </button>

      <div className="leading-tight">
        <p className="label">Voice walkthrough</p>
        <p
          className={cn(
            'text-[12px] font-mono',
            state.kind === 'error' ? 'text-redline' : 'text-ink-soft',
          )}
        >
          {state.kind === 'error' ? state.message : labelText}
        </p>
      </div>

      {state.kind === 'ready' && (
        <audio ref={audioRef} src={state.src} preload="auto" className="sr-only" />
      )}
    </div>
  );
}
