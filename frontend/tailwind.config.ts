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
        // The old neon names, toned down: accents for headings, prices and states.
        neon: {
          cyan: "#62b6c8",
          magenta: "#b597d6",
          yellow: "#d8b45c",
          green: "#52bd88",
          red: "#e06c6c",
          orange: "#dd965c",
        },
        void: {
          black: "#0d1117",
          darker: "#090c10",
        },
        dark: {
          gray: "#121821",
          lighter: "#232c38",
          border: "#26303d",
          surface: "#161d27",
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
