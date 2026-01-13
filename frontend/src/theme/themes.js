import { colors } from './colors';

// Theme presets for Homelab Manager

export const darkTheme = {
  colorScheme: 'dark',
  primaryColor: 'blue',
  colors: {
    ...colors,
    // Dark theme background colors
    dark: [
      '#C1C2C5', // 0 - lightest text
      '#A6A7AB', // 1 - lighter text
      '#909296', // 2 - light text
      '#5C5F66', // 3 - muted text
      '#373A40', // 4 - border
      '#2C2E33', // 5 - hover
      '#25262B', // 6 - background (main)
      '#1A1B1E', // 7 - paper/cards
      '#141517', // 8 - dark elements
      '#101113', // 9 - darkest
    ],
  },
  other: {
    // Page-specific accent colors
    pageAccents: {
      dashboard: 'violet',
      devices: 'blue',
      services: 'teal',
      automation: 'purple',
    },
  },
  fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
  fontFamilyMonospace: 'Courier New, Courier, monospace',
  headings: {
    fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
    fontWeight: 600,
  },
};

export const lightTheme = {
  colorScheme: 'light',
  primaryColor: 'blue',
  colors: {
    ...colors,
    // Light theme uses default Mantine gray scale
  },
  other: {
    // Page-specific accent colors (same as dark)
    pageAccents: {
      dashboard: 'violet',
      devices: 'blue',
      services: 'teal',
      automation: 'purple',
    },
  },
  fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
  fontFamilyMonospace: 'Courier New, Courier, monospace',
  headings: {
    fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
    fontWeight: 600,
  },
};

export const midnightTheme = {
  colorScheme: 'dark',
  primaryColor: 'blue',
  colors: {
    ...colors,
    // Midnight theme - deeper, blue-tinted blacks
    dark: [
      '#B8CDEB', // 0 - lightest text (blue-tinted)
      '#9FB9DB', // 1 - lighter text
      '#86A5CB', // 2 - light text
      '#5A7BA3', // 3 - muted text
      '#2E3F5A', // 4 - border (dark blue)
      '#1E2A3F', // 5 - hover
      '#141D2E', // 6 - background (main - deep blue-black)
      '#0D1421', // 7 - paper/cards (very dark blue)
      '#080D15', // 8 - dark elements
      '#030508', // 9 - darkest (almost black)
    ],
  },
  other: {
    // Page-specific accent colors
    pageAccents: {
      dashboard: 'violet',
      devices: 'blue',
      services: 'teal',
      automation: 'purple',
    },
  },
  fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
  fontFamilyMonospace: 'Courier New, Courier, monospace',
  headings: {
    fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
    fontWeight: 600,
  },
};

// Export all themes
export const themes = {
  dark: darkTheme,
  light: lightTheme,
  midnight: midnightTheme,
};

// Default theme
export const defaultTheme = 'dark';
