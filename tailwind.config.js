/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./novadrive/templates/**/*.html",
    "./novadrive/static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        nova: {
          900: "#0b0812",
          950: "#05030a"
        }
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        sans: ["Plus Jakarta Sans", "sans-serif"]
      },
      boxShadow: {
        glow: "0 0 40px rgba(168, 85, 247, 0.22)"
      }
    }
  },
  plugins: []
};
