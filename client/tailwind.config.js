/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        display: ['"Syne"', 'sans-serif'],
        sans: ['"DM Sans"', 'sans-serif'],
      },
      colors: {
        ink: {
          50: '#f4f6fb',
          100: '#e8ecf6',
          200: '#c9d2e8',
          300: '#9aa9c9',
          400: '#6b7ea8',
          500: '#4a5f8f',
          600: '#364872',
          700: '#273456',
          800: '#1a243c',
          900: '#111827',
          950: '#0a0f1a',
        },
        accent: {
          DEFAULT: '#3dd6c6',
          soft: '#7ee7db',
          deep: '#1aa89a',
        },
        ember: {
          DEFAULT: '#ff6b4a',
          soft: '#ff9a82',
        },
      },
      boxShadow: {
        glass: '0 8px 32px rgba(0, 0, 0, 0.28)',
        glow: '0 0 40px rgba(61, 214, 198, 0.18)',
      },
      backgroundImage: {
        aurora:
          'radial-gradient(1200px 600px at 10% -10%, rgba(61,214,198,0.18), transparent 55%), radial-gradient(900px 500px at 90% 0%, rgba(255,107,74,0.12), transparent 50%), radial-gradient(800px 500px at 50% 100%, rgba(74,95,143,0.25), transparent 60%)',
        auroraLight:
          'radial-gradient(1200px 600px at 10% -10%, rgba(26,168,154,0.14), transparent 55%), radial-gradient(900px 500px at 90% 0%, rgba(255,107,74,0.10), transparent 50%), radial-gradient(800px 500px at 50% 100%, rgba(201,210,232,0.55), transparent 60%)',
      },
      keyframes: {
        pulseBar: {
          '0%, 100%': { opacity: '0.35', transform: 'scaleX(0.7)' },
          '50%': { opacity: '1', transform: 'scaleX(1)' },
        },
      },
      animation: {
        pulseBar: 'pulseBar 1.4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
