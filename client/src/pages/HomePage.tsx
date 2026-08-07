import { useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { ErrorState } from '../components/ErrorState';
import { RecentSearches } from '../components/RecentSearches';
import { SearchBox } from '../components/SearchBox';
import { SearchProgress } from '../components/SearchProgress';
import { ThemeToggle } from '../components/ThemeToggle';
import { ToastViewport } from '../components/Toast';
import { VideoPlayer } from '../components/VideoPlayer';
import { VideoSkeleton } from '../components/VideoSkeleton';
import { useRecentSearches } from '../hooks/useRecentSearches';
import { useTheme } from '../hooks/useTheme';
import { useToast } from '../hooks/useToast';
import { searchVideos } from '../services/api';
import type { SearchProgressStep, SearchVideoResult } from '../types';

const PROGRESS_SEQUENCE: SearchProgressStep[] = [
  'understanding',
  'optimizing',
  'searching',
  'ranking',
  'preparing',
];

export function HomePage() {
  const [query, setQuery] = useState('');
  const [video, setVideo] = useState<SearchVideoResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [progressStep, setProgressStep] = useState<SearchProgressStep>('understanding');
  const inputFocusRef = useRef<HTMLDivElement>(null);
  const { theme, toggleTheme } = useTheme();
  const { recent, addRecent, clearRecent } = useRecentSearches();
  const { toasts, push, dismiss } = useToast();

  const mutation = useMutation({
    mutationFn: searchVideos,
    onMutate: () => {
      setErrorMessage(null);
      setVideo(null);
      setProgressStep('understanding');
    },
    onSuccess: (data, variables) => {
      setVideo(data);
      setProgressStep('done');
      addRecent({
        query: variables,
        videoId: data.videoId,
        title: data.title,
      });
      push('Perfect match found', 'success');
    },
    onError: (error: Error) => {
      setErrorMessage(error.message || 'Something went wrong. Please try again.');
      push('Search failed', 'error');
    },
  });

  useEffect(() => {
    if (!mutation.isPending) return;

    let index = 0;
    setProgressStep(PROGRESS_SEQUENCE[0]);
    const timer = window.setInterval(() => {
      index = Math.min(index + 1, PROGRESS_SEQUENCE.length - 1);
      setProgressStep(PROGRESS_SEQUENCE[index]);
      if (index >= PROGRESS_SEQUENCE.length - 1) {
        window.clearInterval(timer);
      }
    }, 1600);

    return () => window.clearInterval(timer);
  }, [mutation.isPending]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const typing =
        target?.tagName === 'INPUT' ||
        target?.tagName === 'TEXTAREA' ||
        target?.isContentEditable;

      if (event.key === '/' && !typing) {
        event.preventDefault();
        const input = inputFocusRef.current?.querySelector('input');
        input?.focus();
      }

      if ((event.key === 't' || event.key === 'T') && !typing) {
        event.preventDefault();
        toggleTheme();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [toggleTheme]);

  const runSearch = (value = query) => {
    const trimmed = value.trim();
    if (trimmed.length < 3) {
      push('Please enter at least 3 characters', 'info');
      return;
    }
    setQuery(trimmed);
    mutation.mutate(trimmed);
  };

  return (
    <div
      className={`min-h-screen ${theme === 'dark' ? 'bg-aurora' : 'bg-auroraLight'} transition-colors`}
    >
      <div className="mx-auto max-w-6xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
        <header className="mb-10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-accent text-ink-950 shadow-glow">
              <span className="font-display text-lg font-extrabold" aria-hidden>
                AI
              </span>
            </div>
            <p className="text-sm font-medium text-[var(--muted)]">Semantic YouTube</p>
          </div>
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
        </header>

        <main>
          <motion.section
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <h1 className="font-display text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
              AI YouTube Search
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-base text-[var(--muted)] sm:text-lg">
              Describe any video and let AI find the perfect match.
            </p>
          </motion.section>

          <motion.div
            ref={inputFocusRef}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12, duration: 0.45 }}
            className="mt-10"
          >
            <SearchBox
              value={query}
              loading={mutation.isPending}
              onChange={setQuery}
              onSubmit={() => runSearch()}
            />
          </motion.div>

          {mutation.isPending && <SearchProgress activeStep={progressStep} />}
          {mutation.isPending && <VideoSkeleton />}

          {errorMessage && !mutation.isPending && (
            <ErrorState message={errorMessage} onRetry={() => runSearch()} />
          )}

          {video && !mutation.isPending && (
            <VideoPlayer video={video} onNotify={push} />
          )}

          <RecentSearches
            items={recent}
            onSelect={(value) => runSearch(value)}
            onClear={() => {
              clearRecent();
              push('Search history cleared', 'info');
            }}
          />
        </main>
      </div>

      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </div>
  );
}
