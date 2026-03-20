/**
 * Animantis Mantine Theme — Cyberpunk dark theme with neon accents.
 *
 * Maps our design tokens to Mantine's theming system while preserving
 * the existing CSS custom properties for backward compatibility.
 */

import { createTheme, type MantineColorsTuple } from '@mantine/core';

/* ── Custom color palettes ─────────────────────────────────── */

const cyanPalette: MantineColorsTuple = [
  '#e0fffe',
  '#b3fffc',
  '#80fff7',
  '#4dfff3',
  '#1affef',
  '#00e6d6',
  '#00b3a6',
  '#008077',
  '#004d47',
  '#001a18',
];

const purplePalette: MantineColorsTuple = [
  '#f0e5ff',
  '#d4b3ff',
  '#b880ff',
  '#9c4dff',
  '#7b2fff',
  '#6a1be6',
  '#5515b3',
  '#400f80',
  '#2b0a4d',
  '#16051a',
];

const pinkPalette: MantineColorsTuple = [
  '#ffe5ef',
  '#ffb3d0',
  '#ff80b1',
  '#ff4d92',
  '#ff2d78',
  '#e61960',
  '#b3134a',
  '#800d35',
  '#4d081f',
  '#1a030a',
];

/* ── Theme configuration ───────────────────────────────────── */

export const animantisTheme = createTheme({
  /* Colors */
  colors: {
    cyan: cyanPalette,
    purple: purplePalette,
    pink: pinkPalette,
  },
  primaryColor: 'cyan',
  primaryShade: 4,

  /* Typography */
  fontFamily: 'var(--font-body)',
  headings: {
    fontFamily: 'var(--font-heading)',
    fontWeight: '700',
  },

  /* Border radius */
  radius: {
    xs: '4px',
    sm: '6px',
    md: '10px',
    lg: '14px',
    xl: '20px',
  },
  defaultRadius: 'md',

  /* Shadows */
  shadows: {
    xs: '0 1px 4px rgba(0, 0, 0, 0.3)',
    sm: '0 2px 8px rgba(0, 0, 0, 0.3)',
    md: '0 4px 16px rgba(0, 0, 0, 0.4)',
    lg: '0 8px 32px rgba(0, 0, 0, 0.5)',
    xl: '0 12px 48px rgba(0, 0, 0, 0.6)',
  },

  /* Spacing (Fibonacci Sequence) */
  spacing: {
    xs: '8px',
    sm: '13px',
    md: '21px',
    lg: '34px',
    xl: '55px',
  },

  /* Component overrides */
  components: {
    Card: {
      defaultProps: {
        shadow: 'md',
        radius: 'lg',
        padding: 'lg',
        withBorder: true,
      },
      styles: () => ({
        root: {
          backgroundColor: 'rgba(12, 18, 34, 0.85)',
          borderColor: 'rgba(255, 255, 255, 0.08)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          transition: 'border-color 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease',
          '&:hover': {
            borderColor: 'rgba(255, 255, 255, 0.12)',
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
          },
        },
      }),
    },
    Button: {
      defaultProps: {
        radius: 'md',
      },
    },
    Badge: {
      defaultProps: {
        radius: 'sm',
        variant: 'light',
      },
    },
    TextInput: {
      styles: () => ({
        input: {
          backgroundColor: 'rgba(12, 18, 34, 0.85)',
          borderColor: 'rgba(255, 255, 255, 0.08)',
          color: '#e8eaed',
          '&:focus': {
            borderColor: '#00ffe5',
            boxShadow: '0 0 20px rgba(0, 255, 229, 0.15)',
          },
        },
      }),
    },
    Textarea: {
      styles: () => ({
        input: {
          backgroundColor: 'rgba(12, 18, 34, 0.85)',
          borderColor: 'rgba(255, 255, 255, 0.08)',
          color: '#e8eaed',
          '&:focus': {
            borderColor: '#00ffe5',
            boxShadow: '0 0 20px rgba(0, 255, 229, 0.15)',
          },
        },
      }),
    },
    Modal: {
      defaultProps: {
        radius: 'lg',
        centered: true,
        overlayProps: { backgroundOpacity: 0.6, blur: 4 },
      },
      styles: () => ({
        content: {
          backgroundColor: 'rgba(12, 18, 34, 0.95)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          backdropFilter: 'blur(20px)',
        },
      }),
    },
    Drawer: {
      defaultProps: {
        overlayProps: { backgroundOpacity: 0.6, blur: 4 },
      },
      styles: () => ({
        content: {
          backgroundColor: 'rgba(12, 18, 34, 0.95)',
        },
      }),
    },
    Skeleton: {
      styles: () => ({
        root: {
          '&::before': {
            background: 'rgba(255, 255, 255, 0.03)',
          },
          '&::after': {
            background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.06), transparent)',
          },
        },
      }),
    },
  },
});
