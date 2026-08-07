import { useCallback, useState } from 'react';
import type { RecentSearch } from '../types';
import {
  clearRecentSearches,
  loadRecentSearches,
  saveRecentSearch,
} from '../utils/storage';

export function useRecentSearches() {
  const [recent, setRecent] = useState<RecentSearch[]>(() => loadRecentSearches());

  const addRecent = useCallback(
    (entry: Omit<RecentSearch, 'id' | 'timestamp'>) => {
      setRecent(saveRecentSearch(entry));
    },
    [],
  );

  const clearRecent = useCallback(() => {
    clearRecentSearches();
    setRecent([]);
  }, []);

  return { recent, addRecent, clearRecent };
}
