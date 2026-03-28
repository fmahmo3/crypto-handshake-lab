/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: [
          'JetBrains Mono',
          'Fira Code',
          'Cascadia Code',
          'SF Mono',
          'Consolas',
          'monospace',
        ],
      },
      animation: {
        'fade-in-down': 'fadeInDown 0.45s ease-out both',
        'fade-in': 'fadeIn 0.3s ease-out both',
        'tamper-flash': 'tamperFlash 0.5s ease-in-out 4',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'travel-right': 'travelRight 0.7s ease-in-out',
        'travel-left': 'travelLeft 0.7s ease-in-out',
        'shake': 'shake 0.4s ease-in-out',
        'ping-once': 'ping 0.6s ease-out 1',
      },
      keyframes: {
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-14px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        tamperFlash: {
          '0%, 100%': { backgroundColor: 'transparent' },
          '50%': { backgroundColor: 'rgba(239, 68, 68, 0.15)' },
        },
        glowPulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        },
        travelRight: {
          '0%': { left: '-8px', opacity: '0' },
          '20%': { opacity: '1' },
          '80%': { opacity: '1' },
          '100%': { left: 'calc(100% + 8px)', opacity: '0' },
        },
        travelLeft: {
          '0%': { right: '-8px', opacity: '0' },
          '20%': { opacity: '1' },
          '80%': { opacity: '1' },
          '100%': { right: 'calc(100% + 8px)', opacity: '0' },
        },
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '20%': { transform: 'translateX(-6px)' },
          '40%': { transform: 'translateX(6px)' },
          '60%': { transform: 'translateX(-4px)' },
          '80%': { transform: 'translateX(4px)' },
        },
      },
    },
  },
  plugins: [],
}
