/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Syne', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
      },
      colors: {
        ink: '#0D0D0D',
        paper: '#F5F2ED',
        cream: '#EDE8E0',
        accent: '#E8521A',
        'accent-light': '#F5896A',
        sage: '#7C9A6E',
        slate: '#4A5568',
        muted: '#9CA3AF',
      },
    },
  },
  plugins: [],
}
