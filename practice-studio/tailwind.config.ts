import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        "foreground-secondary": "rgb(var(--foreground-secondary) / <alpha-value>)",
        surface: {
          panel: "rgb(var(--surface-panel) / <alpha-value>)",
        },
        accent: "rgb(var(--accent) / <alpha-value>)",
        warning: {
          DEFAULT: "rgb(var(--warning) / <alpha-value>)",
          soft: "rgb(var(--warning-soft) / <alpha-value>)",
          border: "rgb(var(--warning-border) / <alpha-value>)",
        },
        status: {
          correct: "rgb(var(--status-correct) / <alpha-value>)",
          "correct-text": "rgb(var(--status-correct-text) / <alpha-value>)",
          "correct-soft": "rgb(var(--status-correct-soft) / <alpha-value>)",
          assisted: "rgb(var(--status-assisted) / <alpha-value>)",
          "assisted-soft": "rgb(var(--status-assisted-soft) / <alpha-value>)",
          wrong: "rgb(var(--status-wrong) / <alpha-value>)",
          "wrong-soft": "rgb(var(--status-wrong-soft) / <alpha-value>)",
          skipped: "rgb(var(--status-skipped) / <alpha-value>)",
          neutral: "rgb(var(--status-neutral) / <alpha-value>)",
          "on-correct": "rgb(var(--status-on-correct) / <alpha-value>)",
          "on-assisted": "rgb(var(--status-on-assisted) / <alpha-value>)",
          "on-wrong": "rgb(var(--status-on-wrong) / <alpha-value>)",
        },
      },
      // Learner choice: base text 15px.
      fontSize: {
        base: ["0.9375rem", { lineHeight: "1.5rem" }],
      },
      fontFamily: {
        sans: [
          "var(--font-geist-sans)",
          '"Geist"',
          '"Geist Fallback"',
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "sans-serif",
        ],
        // Secondary/accent family: non-code numbers and labels (scores, Q1/Q2, timers, IDs).
        display: ['"Roboto Slab Variable"', '"Roboto Slab"', "Georgia", "serif"],
        mono: [
          "var(--font-geist-mono)",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};
export default config;

