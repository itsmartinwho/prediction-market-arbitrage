import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Quantitative dark-slate palette: one primary accent (cyan) + semantic status hues.
        neon: {
          cyan: "#5ba8be",
          magenta: "#8b9bb4",
          yellow: "#c9a24b",
          green: "#4ca97a",
          red: "#d16969",
          orange: "#c9a24b",
        },
        void: {
          black: "#0b0e14",
          darker: "#07090d",
        },
        dark: {
          gray: "#11161f",
          lighter: "#1f2836",
          border: "#222b38",
          surface: "#161d28",
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
