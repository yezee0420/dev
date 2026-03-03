export const Colors = {
  dark: {
    background: '#000000',
    surface: '#121212',
    card: '#1a1a1a',
    text: '#ffffff',
    textSecondary: '#a0a0a0',
    border: '#2a2a2a',
    primary: '#0095f6',
    error: '#ed4956',
    heart: '#ed4956',
    separator: '#262626',
    inputBg: '#363636',
    placeholder: '#8e8e8e',
  },
  light: {
    background: '#ffffff',
    surface: '#fafafa',
    card: '#ffffff',
    text: '#262626',
    textSecondary: '#8e8e8e',
    border: '#dbdbdb',
    primary: '#0095f6',
    error: '#ed4956',
    heart: '#ed4956',
    separator: '#efefef',
    inputBg: '#fafafa',
    placeholder: '#8e8e8e',
  },
};

export type ThemeColors = typeof Colors.dark;

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
};
