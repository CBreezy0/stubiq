/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './hooks/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          950: '#09111f',
          900: '#10213b',
          800: '#173057'
        }
      },
      boxShadow: {
        panel: '0 18px 48px rgba(15, 23, 42, 0.22)'
      }
    },
  },
  plugins: [],
};
