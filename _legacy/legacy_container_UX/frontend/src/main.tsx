import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'
import { visualFeedback } from './lib/visual-feedback'

// Collider Bridge (DEV only) - Copilot ↔ Host communication
import { initColliderBridge } from './lib/chat/collider-bridge'
import { startBridgeExecutor } from './lib/chat/collider-bridge-executor'

// Expose environment mode for debugging
const VITE_MODE = import.meta.env.VITE_MODE || 'unknown';
console.log(`🚀 App Mode: ${VITE_MODE}`);
(window as any).__VITE_MODE__ = VITE_MODE;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

declare global {
  interface Window {
    __visualFeedback?: typeof visualFeedback
  }
}

window.__visualFeedback = visualFeedback

// Initialize Collider Bridge in DEV mode
if (import.meta.env.DEV) {
  initColliderBridge()
  startBridgeExecutor()
}

createRoot(document.getElementById('root')!).render(
  // Temporarily disable StrictMode for PixiJS development
  // StrictMode runs effects twice which breaks PixiJS initialization
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </QueryClientProvider>,
)
