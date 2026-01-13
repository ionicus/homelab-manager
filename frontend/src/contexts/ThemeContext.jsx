import { createContext, useContext, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { themes, defaultTheme } from '../theme';

const ThemeContext = createContext();

const STORAGE_KEY = 'homelab-theme';
const ACCENTS_STORAGE_KEY = 'homelab-accents';

const DEFAULT_ACCENTS = {
  dashboard: 'violet',
  devices: 'blue',
  services: 'teal',
  automation: 'purple',
};

export function ThemeProvider({ children }) {
  const [currentTheme, setCurrentTheme] = useState(() => {
    // Load theme from localStorage or use default
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved && themes[saved] ? saved : defaultTheme;
  });

  const [pageAccents, setPageAccents] = useState(() => {
    // Load custom accents from localStorage or use defaults
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

  const [currentPage, setCurrentPage] = useState('dashboard');
  const location = useLocation();

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

  // Set theme attributes for CSS customization when theme changes
  useEffect(() => {
    const themeConfig = themes[currentTheme];
    const colorScheme = themeConfig?.colorScheme || 'dark';

    // Set Mantine's color scheme attribute on the root element
    document.documentElement.setAttribute('data-mantine-color-scheme', colorScheme);

    // Set midnight theme attribute for additional CSS customization
    if (currentTheme === 'midnight') {
      document.body.setAttribute('data-midnight-theme', 'true');
    } else {
      document.body.removeAttribute('data-midnight-theme');
    }
  }, [currentTheme]);

  // Persist theme to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, currentTheme);
  }, [currentTheme]);

  // Persist accents to localStorage
  useEffect(() => {
    localStorage.setItem(ACCENTS_STORAGE_KEY, JSON.stringify(pageAccents));
  }, [pageAccents]);

  const switchTheme = (themeName) => {
    if (themes[themeName]) {
      setCurrentTheme(themeName);
    }
  };

  const updatePageAccent = (page, color) => {
    setPageAccents(prev => ({
      ...prev,
      [page]: color,
    }));
  };

  const resetAccents = () => {
    setPageAccents(DEFAULT_ACCENTS);
  };

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
