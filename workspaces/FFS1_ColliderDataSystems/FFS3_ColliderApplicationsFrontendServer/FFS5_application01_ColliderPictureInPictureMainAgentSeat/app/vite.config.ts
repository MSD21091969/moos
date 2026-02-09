import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: 'src/index.tsx',
      name: 'ColliderPiPUI',
      formats: ['es'],
      fileName: () => 'index.js'
    },
    rollupOptions: {
      external: ['react', 'react-dom', 'simple-peer'],
      output: {
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM',
          'simple-peer': 'SimplePeer'
        }
      }
    }
  }
})
