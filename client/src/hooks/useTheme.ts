import { useEffect, useState } from 'react';
import type { ThemeMode } from '../types';
import { loadTheme, saveTheme } from '../utils/storage';

export function useTheme() {
  const [theme, setTheme] = useState<ThemeMode>(() => loadTheme());

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', theme === 'dark');
    root.classList.toggle('light', theme === 'light');
    saveTheme(theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  return { theme, setTheme, toggleTheme };
}
