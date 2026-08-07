import { Clock3, Trash2 } from 'lucide-react';
import { motion } from 'framer-motion';
import type { RecentSearch } from '../types';

interface RecentSearchesProps {
  items: RecentSearch[];
  onSelect: (query: string) => void;
  onClear: () => void;
}

export function RecentSearches({ items, onSelect, onClear }: RecentSearchesProps) {
  if (items.length === 0) return null;

  return (
    <section className="mx-auto mt-10 w-full max-w-3xl" aria-labelledby="recent-heading">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 id="recent-heading" className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          <Clock3 className="h-4 w-4" aria-hidden />
          Recent searches
        </h2>
        <button
          type="button"
          onClick={onClear}
          className="focus-ring inline-flex items-center gap-1.5 rounded-xl px-2 py-1 text-xs text-[var(--muted)] hover:text-[var(--fg)]"
        >
          <Trash2 className="h-3.5 w-3.5" aria-hidden />
          Clear history
        </button>
      </div>
      <ul className="flex flex-wrap gap-2">
        {items.map((item, index) => (
          <motion.li
            key={item.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.03 }}
          >
            <button
              type="button"
              onClick={() => onSelect(item.query)}
              className="focus-ring glass rounded-2xl px-3.5 py-2 text-left text-sm transition hover:border-accent/40"
              title={item.title ? `Last result: ${item.title}` : item.query}
            >
              {item.query}
            </button>
          </motion.li>
        ))}
      </ul>
    </section>
  );
}
