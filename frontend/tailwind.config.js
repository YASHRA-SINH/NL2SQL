/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 18px 60px rgba(15, 23, 42, 0.16)",
        glow: "0 0 28px rgba(20, 184, 166, 0.28)",
      },
    },
  },
  plugins: [],
};
