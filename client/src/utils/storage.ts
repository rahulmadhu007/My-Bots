import type { RecentSearch, ThemeMode } from '../types';

const RECENT_KEY = 'ai-yt-recent-searches';
const THEME_KEY = 'ai-yt-theme';
const MAX_RECENT = 12;

export function loadRecentSearches(): RecentSearch[] {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as RecentSearch[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveRecentSearch(entry: Omit<RecentSearch, 'id' | 'timestamp'>): RecentSearch[] {
  const current = loadRecentSearches().filter(
    (item) => item.query.toLowerCase() !== entry.query.toLowerCase(),
  );
  const next: RecentSearch[] = [
    {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      ...entry,
    },
    ...current,
  ].slice(0, MAX_RECENT);

  localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  return next;
}

export function clearRecentSearches(): void {
  localStorage.removeItem(RECENT_KEY);
}

export function loadTheme(): ThemeMode {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === 'light' || stored === 'dark') return stored;
  return 'dark';
}

export function saveTheme(theme: ThemeMode): void {
  localStorage.setItem(THEME_KEY, theme);
}

export function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

export async function shareContent(data: ShareData): Promise<'shared' | 'copied' | 'failed'> {
  if (navigator.share) {
    try {
      await navigator.share(data);
      return 'shared';
    } catch {
      // fall through to clipboard
    }
  }
  if (data.url && (await copyToClipboard(data.url))) {
    return 'copied';
  }
  return 'failed';
}
