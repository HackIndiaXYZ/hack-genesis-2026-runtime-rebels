/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        primary: "var(--color-primary)",
        accent: "var(--color-accent)",
        warning: "var(--color-warning)",
        critical: "var(--color-critical)",
        success: "var(--color-success)",
        background: "var(--color-background)",
        surface: "var(--color-surface)",
        subtle: "var(--color-subtle)",
        main: "var(--color-text-main)",
        muted: "var(--color-text-muted)",
        disabled: "var(--color-text-disabled)",
        default: "var(--color-border-default)",
      },
      fontFamily: {
        display: ['"IBM Plex Sans"', 'sans-serif'],
        body: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      boxShadow: {
        'civic': '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)',
      }
    },
  },
  plugins: [],
}
