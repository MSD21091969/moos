/**
 * CLOUD Agent - Manages cloud backend operations
 */
import { contextManager } from "../context/manager"
import * as dataClient from "../external/data"
import * as vectorClient from "../external/vectordb"
import { graphToolClient } from "../external/graphtool"

export interface CloudAction {
  type: "navigate" | "query" | "execute" | "search" | "chat"
  path?: string
  query?: string
  workflowId?: string
  input?: Record<string, unknown>
}

export interface CloudResult {
  success: boolean
  data?: unknown
  error?: string
}

/**
 * Execute a cloud action
 */
export async function executeCloudAction(
  tabKey: string,
  action: CloudAction
): Promise<CloudResult> {
  const context = await contextManager.getTabContext(tabKey)
  
  if (!context || context.domain !== "CLOUD") {
    return { success: false, error: "Tab is not in CLOUD domain" }
  }

  try {
    switch (action.type) {
      case "navigate": {
        if (!action.path) {
          return { success: false, error: "Path required for navigate" }
        }
        // Get node at path
        const appId = context.app.replace("cloud://", "")
        const node = await dataClient.getNode(appId, action.path)
        
        // Update tab context
        await contextManager.updateTabContext(tabKey, {
          node: action.path,
          container: node.container as any,
        })
        
        return { success: true, data: node }
      }

      case "query": {
        // Execute a query against the knowledge base
        const results = await vectorClient.search(action.query || "", 5)
        return { success: true, data: results }
      }

      case "execute": {
        // Execute a workflow via GraphTool
        if (!action.workflowId) {
          return { success: false, error: "Workflow ID required" }
        }
        
        const result = await graphToolClient.executeWorkflow(
          { workflow_id: action.workflowId, input: action.input || {} },
          { app: context.app, node: context.node }
        )
        
        return { success: true, data: result }
      }

      case "search": {
        // Semantic search in VectorDB
        const results = await vectorClient.search(action.query || "", 10)
        return { success: true, data: results }
      }

      case "chat": {
        // Send message to GraphTool for LLM processing
        const result = await new Promise((resolve, reject) => {
          const callbacks = {
            onMessage: (msg: unknown) => resolve(msg),
            onError: (err: unknown) => reject(err),
            onComplete: () => {},
          }
          graphToolClient.executeTool(
            "chat",
            { message: action.query, context: context.container },
            callbacks as Record<string, unknown>
          )
        })
        return { success: true, data: result }
      }

      default:
        return { success: false, error: `Unknown action type: ${action.type}` }
    }
  } catch (error) {
    return { success: false, error: String(error) }
  }
}

/**
 * Get app node tree from Data Server
 */
export async function getCloudTree(appAddress: string): Promise<CloudResult> {
  try {
    const appId = appAddress.replace("cloud://", "")
    const nodes = await dataClient.getNodeTree(appId)
    return { success: true, data: nodes }
  } catch (error) {
    return { success: false, error: String(error) }
  }
}
