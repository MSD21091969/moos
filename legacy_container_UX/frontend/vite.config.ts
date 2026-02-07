import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '')
    
    return {
        plugins: [react()],
        resolve: {
            alias: {
                '@': path.resolve(__dirname, './src'),
            },
        },
        server: {
            port: 5173,
            host: true,
            open: false,
            hmr: {
                overlay: false,
            },
            proxy: {
                '/api/v5': {
                    target: env.VITE_API_URL || 'http://localhost:8000',
                    changeOrigin: true,
                },
                '/api': {
                    target: env.VITE_API_URL || 'http://localhost:8000',
                    changeOrigin: true,
                    rewrite: (path) => path.replace(/^\/api/, ''),
                },
            },
        },
        build: {
            target: 'esnext',
            minify: 'esbuild', // Faster than terser
        },
        optimizeDeps: {
            include: ['react', 'react-dom', '@google/genai'], // Pre-bundle heavy deps
        },
    }
})
