/**
 * GraphTool Server client - WebSocket
 */

const GRAPHTOOL_URL = "ws://localhost:8001/ws"

type MessageHandler = (result: unknown) => void
type ErrorHandler = (error: unknown) => void

class GraphToolClient {
  private ws: WebSocket | null = null
  private sessionId: string = ""
  private messageHandlers: Map<string, MessageHandler> = new Map()
  private errorHandlers: Map<string, ErrorHandler> = new Map()
  private messageId = 0

  connect(sessionId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.sessionId = sessionId
      this.ws = new WebSocket(`${GRAPHTOOL_URL}/${sessionId}`)

      this.ws.onopen = () => {
        console.log("🔗 GraphTool connected")
        resolve()
      }

      this.ws.onerror = (e) => {
        console.error("GraphTool error:", e)
        reject(e)
      }

      this.ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data)
          if (data.type === "result") {
            // Broadcast to all handlers
            this.messageHandlers.forEach((handler) => handler(data.payload))
          } else if (data.type === "error") {
            this.errorHandlers.forEach((handler) => handler(data.payload))
          }
        } catch (err) {
          console.error("Failed to parse GraphTool message:", err)
        }
      }

      this.ws.onclose = () => {
        console.log("🔌 GraphTool disconnected")
        this.ws = null
      }
    })
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  async executeWorkflow(
    workflow: Record<string, unknown>,
    context: Record<string, unknown>
  ): Promise<unknown> {
    return this.send("workflow", workflow, context)
  }

  async executeTool(
    toolName: string,
    toolArgs: Record<string, unknown>,
    context: Record<string, unknown>
  ): Promise<unknown> {
    return this.send("tool", { name: toolName, args: toolArgs }, context)
  }

  private send(
    type: string,
    payload: Record<string, unknown>,
    context: Record<string, unknown>
  ): Promise<unknown> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error("WebSocket not connected"))
        return
      }

      const id = `msg_${++this.messageId}`
      
      this.messageHandlers.set(id, (result) => {
        this.messageHandlers.delete(id)
        this.errorHandlers.delete(id)
        resolve(result)
      })

      this.errorHandlers.set(id, (error) => {
        this.messageHandlers.delete(id)
        this.errorHandlers.delete(id)
        reject(error)
      })

      this.ws.send(JSON.stringify({ type, payload, context }))
    })
  }
}

export const graphToolClient = new GraphToolClient()
