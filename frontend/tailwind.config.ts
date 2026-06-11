import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0f14",
        olive: "#43443c",
        muted: "#667085",
        line: "#dde7ee",
        shell: "#f7fafc",
        panel: "#ffffff",
        brand: {
          DEFAULT: "#0f4c81",
          dark: "#0b2f4a",
          soft: "#edf6fb",
          ice: "#d8edf8",
        },
      },
      fontFamily: {
        sans: ["var(--font-dm-sans)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-dm-mono)", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 2px rgba(11,15,20,0.05), 0 8px 24px rgba(11,15,20,0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
