import { Search, Sparkles } from 'lucide-react';
import { type FormEvent, type KeyboardEvent, useId } from 'react';

interface SearchBoxProps {
  value: string;
  loading: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function SearchBox({ value, loading, onChange, onSubmit }: SearchBoxProps) {
  const inputId = useId();

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!loading) onSubmit();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (!loading) onSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mx-auto w-full max-w-3xl" role="search">
      <label htmlFor={inputId} className="sr-only">
        What would you like to watch?
      </label>
      <div className="glass group relative flex items-center gap-2 rounded-[1.75rem] p-2 shadow-glass transition focus-within:shadow-glow focus-within:border-accent/40">
        <div className="hidden pl-3 text-accent sm:block" aria-hidden>
          <Sparkles className="h-5 w-5" />
        </div>
        <input
          id={inputId}
          type="search"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="What would you like to watch?"
          disabled={loading}
          autoComplete="off"
          className="focus-ring min-w-0 flex-1 rounded-2xl bg-transparent px-3 py-4 text-base outline-none placeholder:text-[var(--muted)] disabled:opacity-60 sm:text-lg"
          aria-describedby={`${inputId}-hint`}
        />
        <button
          type="submit"
          disabled={loading || value.trim().length < 3}
          className="focus-ring inline-flex items-center gap-2 rounded-2xl bg-accent px-5 py-3.5 text-sm font-semibold text-ink-950 transition hover:bg-accent-soft disabled:cursor-not-allowed disabled:opacity-50"
          aria-busy={loading}
        >
          {loading ? (
            <span
              className="h-4 w-4 animate-spin rounded-full border-2 border-ink-950/30 border-t-ink-950"
              aria-hidden
            />
          ) : (
            <Search className="h-4 w-4" aria-hidden />
          )}
          <span>{loading ? 'Searching' : 'Search'}</span>
        </button>
      </div>
      <p id={`${inputId}-hint`} className="mt-3 text-center text-xs text-[var(--muted)]">
        Press Enter to search · Shortcut: <kbd className="rounded bg-black/20 px-1.5 py-0.5">/</kbd>{' '}
        focuses search
      </p>
    </form>
  );
}
