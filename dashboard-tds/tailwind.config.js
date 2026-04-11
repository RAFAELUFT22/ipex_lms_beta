/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      // ── Horizonte Cerrado — M3 color tokens ──────────────────────
      colors: {
        // Surfaces (warm cream / parchment)
        "surface":                  "#fff8f2",
        "surface-bright":           "#fff8f2",
        "surface-dim":              "#e4d9c7",
        "surface-container-lowest": "#ffffff",
        "surface-container-low":    "#fef2e0",
        "surface-container":        "#f8ecda",
        "surface-container-high":   "#f2e7d5",
        "surface-container-highest":"#ede1cf",
        "surface-variant":          "#ede1cf",
        "surface-tint":             "#00658b",
        "background":               "#fff8f2",
        "on-background":            "#201b10",
        "on-surface":               "#201b10",
        "on-surface-variant":       "#3f484e",
        "outline":                  "#6f787f",
        "outline-variant":          "#bfc8cf",
        "inverse-surface":          "#363024",
        "inverse-on-surface":       "#fbefdd",
        // Primary — Sky Blue
        "primary":                  "#006184",
        "primary-container":        "#007ba7",
        "on-primary":               "#ffffff",
        "on-primary-container":     "#f5faff",
        "primary-fixed":            "#c4e7ff",
        "primary-fixed-dim":        "#7cd0ff",
        "on-primary-fixed":         "#001e2c",
        "on-primary-fixed-variant": "#004c69",
        "inverse-primary":          "#7cd0ff",
        // Secondary — Golden Amber
        "secondary":                "#7c5800",
        "secondary-container":      "#fdc65c",
        "on-secondary":             "#ffffff",
        "on-secondary-container":   "#745200",
        "secondary-fixed":          "#ffdea7",
        "secondary-fixed-dim":      "#f4be55",
        "on-secondary-fixed":       "#271900",
        "on-secondary-fixed-variant":"#5e4200",
        // Tertiary — Terracotta
        "tertiary":                 "#953f34",
        "tertiary-container":       "#b4564a",
        "on-tertiary":              "#ffffff",
        "on-tertiary-container":    "#fff7f6",
        "tertiary-fixed":           "#ffdad5",
        "tertiary-fixed-dim":       "#ffb4a9",
        "on-tertiary-fixed":        "#400101",
        "on-tertiary-fixed-variant":"#7c2c23",
        // Error
        "error":                    "#ba1a1a",
        "error-container":          "#ffdad6",
        "on-error":                 "#ffffff",
        "on-error-container":       "#93000a",
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        lg:      "0.75rem",
        xl:      "1.5rem",
        full:    "9999px",
      },
      fontFamily: {
        headline: ["Lexend", "sans-serif"],
        body:     ["Lexend", "sans-serif"],
        label:    ["Lexend", "sans-serif"],
        // keep Inter alias for existing Aurora components
        inter:    ["Inter", "sans-serif"],
      },
      backgroundImage: {
        "cerrado-gradient": "linear-gradient(135deg, #006184 0%, #007ba7 100%)",
      },
      boxShadow: {
        "cerrado-float": "0 32px 32px rgba(116,82,0,0.06)",
        "cerrado-fab":   "0 4px 32px rgba(116,82,0,0.06)",
      },
    },
  },
  plugins: [],
}
