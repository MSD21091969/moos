/**
 * Native Messaging Client
 * Communicates with the FILESYST Native Host for local filesystem operations
 */

const NATIVE_HOST_NAME = "com.collider.filesyst"

export interface NativeRequest {
  action: "list" | "read" | "write" | "search" | "sync" | "ping"
  path?: string
  content?: string
  pattern?: string
  options?: Record<string, unknown>
}

export interface NativeResponse<T = unknown> {
  success: boolean
  data?: T
  error?: string
}

export interface FileEntry {
  name: string
  type: "file" | "directory"
  size?: number
}

export interface ListResult {
  path: string
  entries: FileEntry[]
}

export interface ReadResult {
  path: string
  content: string | null
  encoding?: string
  size: number
  binary?: boolean
}

export interface WriteResult {
  path: string
  size: number
}

export interface SearchMatch {
  path: string
  type: "file" | "directory"
  preview?: string
}

export interface SearchResult {
  path: string
  pattern: string
  matches: SearchMatch[]
  truncated: boolean
}

export interface TreeNode {
  name: string
  path: string
  type: "file" | "directory"
  children?: TreeNode[]
}

// Connection state
let nativePort: chrome.runtime.Port | null = null
let pendingRequests: Map<number, {
  resolve: (value: NativeResponse) => void
  reject: (error: Error) => void
  timeout: ReturnType<typeof setTimeout>
}> = new Map()
let requestId = 0

/**
 * Connect to the native host
 */
function connect(): chrome.runtime.Port {
  if (nativePort) {
    return nativePort
  }

  console.log("[Native] Connecting to native host:", NATIVE_HOST_NAME)
  nativePort = chrome.runtime.connectNative(NATIVE_HOST_NAME)

  nativePort.onMessage.addListener((message: NativeResponse & { _id?: number }) => {
    console.log("[Native] Received:", message)
    
    // Handle response with request ID
    if (message._id !== undefined) {
      const pending = pendingRequests.get(message._id)
      if (pending) {
        clearTimeout(pending.timeout)
        pendingRequests.delete(message._id)
        pending.resolve(message)
      }
    }
  })

  nativePort.onDisconnect.addListener(() => {
    const error = chrome.runtime.lastError
    console.warn("[Native] Disconnected:", error?.message || "Unknown reason")
    
    // Reject all pending requests
    for (const [id, pending] of pendingRequests) {
      clearTimeout(pending.timeout)
      pending.reject(new Error(`Native host disconnected: ${error?.message || "Unknown"}`))
    }
    pendingRequests.clear()
    nativePort = null
  })

  return nativePort
}

/**
 * Send a request to the native host
 */
export async function sendNativeRequest<T = unknown>(
  request: NativeRequest,
  timeoutMs: number = 30000
): Promise<NativeResponse<T>> {
  return new Promise((resolve, reject) => {
    try {
      const port = connect()
      const id = ++requestId
      
      // Set up timeout
      const timeout = setTimeout(() => {
        pendingRequests.delete(id)
        reject(new Error(`Native request timed out after ${timeoutMs}ms`))
      }, timeoutMs)
      
      // Store pending request
      pendingRequests.set(id, {
        resolve: resolve as (value: NativeResponse) => void,
        reject,
        timeout,
      })
      
      // Send request with ID
      port.postMessage({ ...request, _id: id })
      console.log("[Native] Sent:", { ...request, _id: id })
      
    } catch (err) {
      reject(err)
    }
  })
}

/**
 * One-shot message (for simple requests)
 */
export async function sendNativeMessage<T = unknown>(
  request: NativeRequest
): Promise<NativeResponse<T>> {
  return new Promise((resolve) => {
    chrome.runtime.sendNativeMessage(
      NATIVE_HOST_NAME,
      request,
      (response: NativeResponse<T>) => {
        if (chrome.runtime.lastError) {
          resolve({
            success: false,
            error: chrome.runtime.lastError.message || "Native messaging failed",
          })
        } else {
          resolve(response)
        }
      }
    )
  })
}

// ========== High-level API ==========

/**
 * List directory contents
 */
export async function listDirectory(
  path: string,
  options?: { showHidden?: boolean }
): Promise<NativeResponse<ListResult>> {
  return sendNativeMessage({
    action: "list",
    path,
    options,
  })
}

/**
 * Read file contents
 */
export async function readFile(
  path: string,
  options?: { maxSize?: number }
): Promise<NativeResponse<ReadResult>> {
  return sendNativeMessage({
    action: "read",
    path,
    options,
  })
}

/**
 * Write content to file
 */
export async function writeFile(
  path: string,
  content: string,
  options?: { createDirs?: boolean }
): Promise<NativeResponse<WriteResult>> {
  return sendNativeMessage({
    action: "write",
    path,
    content,
    options,
  })
}

/**
 * Search for files matching pattern
 */
export async function searchFiles(
  path: string,
  pattern: string,
  options?: { maxResults?: number; includeContent?: boolean }
): Promise<NativeResponse<SearchResult>> {
  return sendNativeMessage({
    action: "search",
    path,
    pattern,
    options,
  })
}

/**
 * Get directory tree for sync
 */
export async function getDirectoryTree(
  path: string,
  options?: { maxDepth?: number }
): Promise<NativeResponse<TreeNode>> {
  return sendNativeMessage({
    action: "sync",
    path,
    options,
  })
}

/**
 * Ping the native host to check if it's available
 */
export async function pingNativeHost(): Promise<boolean> {
  const response = await sendNativeMessage({ action: "ping" })
  return response.success
}

/**
 * Disconnect from native host
 */
export function disconnect(): void {
  if (nativePort) {
    nativePort.disconnect()
    nativePort = null
  }
}
