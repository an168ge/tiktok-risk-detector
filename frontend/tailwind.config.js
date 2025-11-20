/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#00f2ea',
          dark: '#00d9d2',
        },
        danger: {
          DEFAULT: '#ff2d55',
          light: '#ff6b88',
        },
        warning: {
          DEFAULT: '#ff9500',
          light: '#ffb340',
        },
        success: {
          DEFAULT: '#34c759',
          light: '#5dd87d',
        },
      },
    },
  },
  plugins: [],
}
