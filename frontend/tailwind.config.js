/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: '#f9f9f7',
        cream: '#f2f2eb',
        ink: '#1a1a1a',
        slate: '#666666',
        muted: '#999999',
        accent: '#2563eb', // Blue
        sage: '#4ade80', // Green
      },
      fontFamily: {
        display: ['system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      }
    },
  },
  plugins: [],
}
