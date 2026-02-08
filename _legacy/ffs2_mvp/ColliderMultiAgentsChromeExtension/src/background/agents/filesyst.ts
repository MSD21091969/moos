/**
 * FILESYST Agent - Handles local filesystem operations via Native Messaging
 */
import { contextManager } from "../context/manager"
import {
  listDirectory,
  readFile,
  writeFile,
  searchFiles,
  getDirectoryTree,
  pingNativeHost,
  type NativeResponse,
} from "../external/native"

export interface FilesystAction {
  type: "read" | "write" | "list" | "search" | "sync" | "ping"
  path?: string
  content?: string
  pattern?: string
  options?: Record<string, unknown>
}

export interface FilesystResult {
  success: boolean
  data?: unknown
  error?: string
}

/**
 * Execute a filesystem action via Native Messaging
 */
export async function executeFilesystAction(
  tabKey: string,
  action: FilesystAction
): Promise<FilesystResult> {
  const context = await contextManager.getTabContext(tabKey)

  if (!context || context.domain !== "FILESYST") {
    return { success: false, error: "Tab is not in FILESYST domain" }
  }

  // Resolve path: use action.path or fall back to context node
  const basePath = action.path || context.node || ""

  try {
    switch (action.type) {
      case "ping": {
        const pong = await pingNativeHost()
        return { success: pong, data: pong ? "pong" : null }
      }

      case "list":
        return await listDirectory(basePath)

      case "read":
        if (!action.path) {
          return { success: false, error: "Path required for read action" }
        }
        return await readFile(action.path, { maxSize: action.options?.max_size as number | undefined })

      case "write":
        if (!action.path || action.content === undefined) {
          return { success: false, error: "Path and content required for write action" }
        }
        return await writeFile(action.path, action.content, action.options as { createDirs?: boolean })

      case "search":
        return await searchFiles(basePath, action.pattern || "*", action.options as { maxResults?: number; includeContent?: boolean })

      case "sync":
        return await getDirectoryTree(basePath, { maxDepth: action.options?.max_depth as number | undefined })

      default:
        return { success: false, error: `Unknown action type: ${action.type}` }
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error("[Filesyst] Action failed:", action.type, message)
    return { success: false, error: message }
  }
}

/**
 * Get filesystem tree for an app
 */
export async function getFilesystemTree(appAddress: string): Promise<FilesystResult> {
  // Parse filesyst://FFS1/path
  const match = appAddress.match(/^filesyst:\/\/(\w+)(\/.*)?$/)
  if (!match) {
    return { success: false, error: "Invalid filesyst address" }
  }

  const [, workspace, path = "/"] = match

  // Map workspace aliases to actual paths
  const workspacePaths: Record<string, string> = {
    FFS0: "D:/FFS0_Factory",
    FFS1: "D:/FFS0_Factory/workspaces/FFS1_ColliderDataSystems",
    FFS2: "D:/FFS0_Factory/workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension",
    FFS3: "D:/FFS0_Factory/workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer",
  }

  const basePath = workspacePaths[workspace]
  if (!basePath) {
    return { success: false, error: `Unknown workspace: ${workspace}` }
  }

  const fullPath = path === "/" ? basePath : `${basePath}${path}`

  try {
    const result = await getDirectoryTree(fullPath, { maxDepth: 3 })
    if (result.success) {
      return {
        success: true,
        data: {
          workspace,
          path,
          tree: result.data,
        },
      }
    }
    return result
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return { success: false, error: message }
  }
}
