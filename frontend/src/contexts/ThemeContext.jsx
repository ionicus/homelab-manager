import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { themes } from '../theme';
import { useAuth } from './AuthContext';
import { updatePreferences } from '../services/api';

const ThemeContext = createContext();

const STORAGE_KEY = 'homelab-theme';
const ACCENTS_STORAGE_KEY = 'homelab-accents';

const DEFAULT_THEME = 'dark';
const DEFAULT_ACCENTS = {
  dashboard: 'violet',
  devices: 'blue',
  services: 'teal',
  automation: 'purple',
};

export function ThemeProvider({ children }) {
  const { user, isAuthenticated } = useAuth();
  const [currentPage, setCurrentPage] = useState('dashboard');
  const location = useLocation();

  // Track if we've synced from user to avoid repeated syncs
  const hasSyncedFromUser = useRef(false);

  // Initialize theme from localStorage (for quick load) or defaults
  const [currentTheme, setCurrentTheme] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved && themes[saved] ? saved : DEFAULT_THEME;
  });

  const [pageAccents, setPageAccents] = useState(() => {
    const saved = localStorage.getItem(ACCENTS_STORAGE_KEY);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return DEFAULT_ACCENTS;
      }
    }
    return DEFAULT_ACCENTS;
  });

  // Sync from user preferences when authenticated
  useEffect(() => {
    if (isAuthenticated && user && !hasSyncedFromUser.current) {
      // Load user's theme preference
      if (user.theme_preference && themes[user.theme_preference]) {
        setCurrentTheme(user.theme_preference);
        localStorage.setItem(STORAGE_KEY, user.theme_preference);
      }

      // Load user's page accents
      if (user.page_accents && typeof user.page_accents === 'object') {
        const mergedAccents = { ...DEFAULT_ACCENTS, ...user.page_accents };
        setPageAccents(mergedAccents);
        localStorage.setItem(ACCENTS_STORAGE_KEY, JSON.stringify(mergedAccents));
      }

      hasSyncedFromUser.current = true;
    }

    // Reset sync flag when user logs out
    if (!isAuthenticated) {
      hasSyncedFromUser.current = false;
    }
  }, [isAuthenticated, user]);

  // Detect current page from route
  useEffect(() => {
    const path = location.pathname;
    if (path.includes('/devices')) {
      setCurrentPage('devices');
    } else if (path.includes('/services')) {
      setCurrentPage('services');
    } else if (path.includes('/automation')) {
      setCurrentPage('automation');
    } else {
      setCurrentPage('dashboard');
    }
  }, [location]);

  // Set theme attributes for CSS customization
  useEffect(() => {
    const themeConfig = themes[currentTheme];
    const colorScheme = themeConfig?.colorScheme || 'dark';

    document.documentElement.setAttribute('data-mantine-color-scheme', colorScheme);

    if (currentTheme === 'midnight') {
      document.body.setAttribute('data-midnight-theme', 'true');
    } else {
      document.body.removeAttribute('data-midnight-theme');
    }
  }, [currentTheme]);

  // Save preferences to backend (debounced)
  const saveToBackend = useCallback(async (themePreference, accents) => {
    if (!isAuthenticated) return;

    try {
      await updatePreferences({
        theme_preference: themePreference,
        page_accents: accents,
      });
    } catch (err) {
      // Silently fail - preferences are still saved to localStorage
      console.warn('Failed to save preferences to backend:', err);
    }
  }, [isAuthenticated]);

  const switchTheme = useCallback((themeName) => {
    if (themes[themeName]) {
      setCurrentTheme(themeName);
      localStorage.setItem(STORAGE_KEY, themeName);

      // Save to backend if authenticated
      if (isAuthenticated) {
        saveToBackend(themeName, pageAccents);
      }
    }
  }, [isAuthenticated, pageAccents, saveToBackend]);

  const updatePageAccent = useCallback((page, color) => {
    setPageAccents(prev => {
      const newAccents = { ...prev, [page]: color };
      localStorage.setItem(ACCENTS_STORAGE_KEY, JSON.stringify(newAccents));

      // Save to backend if authenticated
      if (isAuthenticated) {
        saveToBackend(currentTheme, newAccents);
      }

      return newAccents;
    });
  }, [isAuthenticated, currentTheme, saveToBackend]);

  const resetAccents = useCallback(() => {
    setPageAccents(DEFAULT_ACCENTS);
    localStorage.setItem(ACCENTS_STORAGE_KEY, JSON.stringify(DEFAULT_ACCENTS));

    // Save to backend if authenticated
    if (isAuthenticated) {
      saveToBackend(currentTheme, DEFAULT_ACCENTS);
    }
  }, [isAuthenticated, currentTheme, saveToBackend]);

  const value = {
    currentTheme,
    switchTheme,
    currentPage,
    availableThemes: Object.keys(themes),
    themeConfig: themes[currentTheme],
    pageAccents,
    updatePageAccent,
    resetAccents,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

// Custom hook to access theme context
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
