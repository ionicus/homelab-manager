import { createTheme } from '@mantine/core';
import { themes, defaultTheme } from './themes';
import { components } from './components';

// Create the base Mantine theme using dark theme as default
export const theme = createTheme({
  ...themes[defaultTheme],
  components,
});

// Export themes for theme switching
export { themes, defaultTheme };

// Export individual theme objects
export { darkTheme, lightTheme, midnightTheme } from './themes';

// Export colors for direct access if needed
export { colors } from './colors';
