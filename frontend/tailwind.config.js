/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                "primary": "#1132d4",
                "background-light": "#f6f6f8",
                "background-dark": "#101322",
            },
            fontFamily: {
                "display": ["Inter", "sans-serif"],
                "sans": ["Inter", "sans-serif"],
            },
            borderRadius: { "DEFAULT": "0.5rem", "lg": "1rem", "xl": "1.5rem", "2xl": "2rem" },
            backgroundImage: {
                'dot-pattern': 'radial-gradient(#cbd5e1 1px, transparent 1px)',
            },
            boxShadow: {
                'glass': '0 4px 30px rgba(0, 0, 0, 0.1)',
                'inner-light': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)',
            },
            animation: {
                'progress': 'progress-move 2s linear infinite',
            },
            keyframes: {
                'progress-move': {
                    '0%': { backgroundPosition: '100% 0' },
                    '100%': { backgroundPosition: '-100% 0' },
                }
            }
        },
    },
    plugins: [],
}
