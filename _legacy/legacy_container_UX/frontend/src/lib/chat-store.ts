import { create } from 'zustand'
import { ChatMessage } from './types'

interface ChatStore {
  messages: ChatMessage[]
  isAgentTyping: boolean
  currentWorkflow: string | null
  
  // Actions
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void
  clearMessages: () => void
  
  // Workflow
  startWorkflow: (workflowId: string) => void
  endWorkflow: () => void
  
  // Agent state
  setAgentTyping: (isTyping: boolean) => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isAgentTyping: false,
  currentWorkflow: null,

  addMessage: (message) => {
    const newMessage: ChatMessage = {
      ...message,
      id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      timestamp: new Date().toISOString(),
    }
    
    set((state) => ({
      messages: [...state.messages, newMessage],
    }))
  },

  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    })),

  clearMessages: () => set({ messages: [] }),

  startWorkflow: (workflowId) => set({ currentWorkflow: workflowId }),
  endWorkflow: () => set({ currentWorkflow: null }),

  setAgentTyping: (isTyping) => set({ isAgentTyping: isTyping }),
}))
