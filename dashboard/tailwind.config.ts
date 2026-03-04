import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'JetBrains Mono'", "monospace"],
      },
      colors: {
        surface: {
          DEFAULT: "#0d1117",
          card: "#161b22",
          border: "#21262d",
          hover: "#1c2128",
        },
        accent: {
          blue: "#58a6ff",
          green: "#3fb950",
          red: "#f85149",
          yellow: "#d29922",
          purple: "#bc8cff",
          cyan: "#76e3ea",
        },
      },
    },
  },
  plugins: [],
};

export default config;
