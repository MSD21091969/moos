/** @type {import('tailwindcss').Config} */
export default {
    darkMode: 'class',
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {},
    },
    safelist: [
        'bg-slate-900/85',
        'bg-slate-900/90',
        'bg-slate-900/95',
        'backdrop-blur-md',
    ],
    plugins: [],
}
