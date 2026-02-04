/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f7ff',
          100: '#e0efff',
          200: '#b8ddff',
          300: '#7bc4ff',
          400: '#3ba3ff',
          500: '#0d7fff',
          600: '#0066e6',
          700: '#0050b8',
          800: '#004496',
          900: '#003a7a',
        },
        dxc: {
          blue: '#0066e6',
          dark: '#1a1a1a',
          gray: '#6b7280',
          light: '#f9fafb',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'dxc': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'dxc-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      },
    },
  },
  plugins: [],
}

