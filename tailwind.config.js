/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        'brand': {
          DEFAULT: '#0C1B2A',
          50: '#E6F0FF',
          100: '#CCE1FF',
          200: '#99C3FF',
          300: '#66A5FF',
          400: '#3387FF',
          500: '#0C1B2A',
          600: '#0A1824',
          700: '#08141E',
          800: '#061018',
          900: '#040C12',
        },
        'brandBg': '#E6F0FF',
        'textSecondary': '#475569',
      },
      boxShadow: {
        'soft': '0 4px 20px rgba(12, 27, 42, 0.08)',
        'card': '0 10px 40px rgba(12, 27, 42, 0.12)',
      },
    },
  },
  plugins: [
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        napiatke: {
          'primary': '#0C1B2A',
          'primary-content': '#ffffff',
          'secondary': '#3387FF',
          'secondary-content': '#ffffff',
          'accent': '#10b981',
          'accent-content': '#ffffff',
          'neutral': '#1f2937',
          'neutral-content': '#ffffff',
          'base-100': '#ffffff',
          'base-200': '#f8fafc',
          'base-300': '#e2e8f0',
          'base-content': '#1e293b',
          'info': '#3b82f6',
          'success': '#22c55e',
          'warning': '#f59e0b',
          'error': '#ef4444',
        },
      },
      'light',
      'dark',
      'corporate',
    ],
    darkTheme: 'dark',
    base: true,
    styled: true,
    utils: true,
  },
}
