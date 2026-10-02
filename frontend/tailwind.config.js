/** @type {import('tailwindcss').Config} */

export default {
  content: ["./index.html", "./src/**/*.{astro,html,js,ts,jsx,tsx}"],

  theme: {
    extend: {
      fontFamily: {
        sans: ["Google Sans", "Segoe UI", "system-ui", "sans-serif"],

        display: ["Google Sans", "Segoe UI", "system-ui", "sans-serif"],
      },

      boxShadow: {
        soft: "0 18px 55px rgba(15, 23, 42, 0.08)",
      },
    },
  },

  plugins: [],
};
