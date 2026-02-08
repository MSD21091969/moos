/**
 * DOM Agent - Handles browser tab DOM operations via Content Scripts
 */
import { contextManager } from "../context/manager"

export interface DOMAction {
  type: "click" | "fill" | "scroll" | "select" | "extract" | "highlight"
  selector?: string
  value?: string
  options?: Record<string, unknown>
}

export interface DOMResult {
  success: boolean
  data?: unknown
  error?: string
}

/**
 * Execute a DOM action in a specific tab
 */
export async function executeDOMAction(
  tabKey: string,
  action: DOMAction
): Promise<DOMResult> {
  const context = await contextManager.getTabContext(tabKey)
  if (!context) {
    return { success: false, error: "Tab context not found" }
  }

  // Parse tabKey to get tabId
  const [, tabIdStr] = tabKey.split("_")
  const tabId = parseInt(tabIdStr, 10)
  
  if (isNaN(tabId)) {
    return { success: false, error: "Invalid tab ID" }
  }

  try {
    const response = await chrome.tabs.sendMessage(tabId, {
      type: "DOM_ACTION",
      payload: action,
    })
    
    if (response.success) {
      return { success: true, data: response.result }
    } else {
      return { success: false, error: response.error }
    }
  } catch (error) {
    return { success: false, error: `Content script error: ${error}` }
  }
}

/**
 * Get current selection from a tab
 */
export async function getSelection(tabKey: string): Promise<DOMResult> {
  const [, tabIdStr] = tabKey.split("_")
  const tabId = parseInt(tabIdStr, 10)
  
  if (isNaN(tabId)) {
    return { success: false, error: "Invalid tab ID" }
  }

  try {
    const response = await chrome.tabs.sendMessage(tabId, { type: "GET_SELECTION" })
    return { success: true, data: response.selection }
  } catch (error) {
    return { success: false, error: `Failed to get selection: ${error}` }
  }
}

/**
 * Get page info from a tab
 */
export async function getPageInfo(tabKey: string): Promise<DOMResult> {
  const [, tabIdStr] = tabKey.split("_")
  const tabId = parseInt(tabIdStr, 10)
  
  if (isNaN(tabId)) {
    return { success: false, error: "Invalid tab ID" }
  }

  try {
    const response = await chrome.tabs.sendMessage(tabId, { type: "GET_PAGE_INFO" })
    return { success: true, data: response }
  } catch (error) {
    return { success: false, error: `Failed to get page info: ${error}` }
  }
}

/**
 * Extract page content for context
 */
export async function extractPageContent(tabKey: string): Promise<DOMResult> {
  return executeDOMAction(tabKey, { type: "extract" })
}
