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
        // Cyberpunk color palette
        neon: {
          cyan: "#00ffff",
          magenta: "#ff00ff",
          yellow: "#ffff00",
          green: "#00ff00",
          red: "#ff0044",
        },
        void: {
          black: "#0a0a0f",
          darker: "#050508",
        },
        dark: {
          gray: "#1a1a2e",
          lighter: "#2a2a4e",
          border: "#3a3a5e",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        neon: "0 0 5px theme('colors.neon.cyan'), 0 0 20px theme('colors.neon.cyan')",
        "neon-magenta":
          "0 0 5px theme('colors.neon.magenta'), 0 0 20px theme('colors.neon.magenta')",
        "neon-green":
          "0 0 5px theme('colors.neon.green'), 0 0 20px theme('colors.neon.green')",
        "neon-red":
          "0 0 5px theme('colors.neon.red'), 0 0 20px theme('colors.neon.red')",
      },
      animation: {
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        glow: "glow 2s ease-in-out infinite alternate",
        scanline: "scanline 8s linear infinite",
      },
      keyframes: {
        glow: {
          "0%": { opacity: "0.5" },
          "100%": { opacity: "1" },
        },
        scanline: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
