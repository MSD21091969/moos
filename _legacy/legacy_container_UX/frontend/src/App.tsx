import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
// V4.1: ContainerPage is an alias for WorkspacePage until V4 container diving is implemented
import WorkspacePage from './pages/WorkspacePage'
const ContainerPage = WorkspacePage
import { ToastContainer } from './components/ToastContainer'
import { visualFeedback } from './lib/visual-feedback'
import { useWorkspaceStore } from './lib/workspace-store'
import { initializeDiagnostics } from './lib/runtime-diagnostics'

function App() {
  useEffect(() => {
    // Expose visualFeedback to window for E2E testing
    if (process.env.NODE_ENV === 'development' || import.meta.env.DEV) {
      (window as any).__visualFeedback = {
        highlightMenu: (menu: 'session' | 'agent' | 'tool' | 'api', duration?: number) =>
          visualFeedback.highlightMenu(menu, duration ?? 500),
        highlightNodes: (nodeIds: string[], color?: string, duration?: number, label?: string) =>
          visualFeedback.highlightNodes(nodeIds, color, duration, label),
        clearHighlights: () => visualFeedback.clearHighlights(),
        getRecentOperations: (limit?: number) => visualFeedback.getRecentOperations(limit),
      }
      
      // Initialize runtime diagnostics
      ;(window as any).__workspaceStore = useWorkspaceStore
      ;(window as any).__workspaceGetState = () => useWorkspaceStore.getState()
      initializeDiagnostics(() => useWorkspaceStore.getState())
    }
  }, [])

  return (
    <>
      <Routes>
        <Route path="/" element={<Navigate to="/workspace" replace />} />
        <Route path="/workspace" element={<ContainerPage />} />
        <Route path="/workspace/:containerId" element={<ContainerPage />} />
      </Routes>
      <ToastContainer />
    </>
  )
}

export default App
