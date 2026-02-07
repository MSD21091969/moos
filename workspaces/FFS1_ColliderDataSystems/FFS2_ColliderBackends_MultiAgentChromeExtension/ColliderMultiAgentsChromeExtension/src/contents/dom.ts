/**
 * Content Script - Runs in every tab for DOM access
 * Communicates with Service Worker via chrome.runtime messaging
 */
import type { PlasmoCSConfig } from "plasmo"

export const config: PlasmoCSConfig = {
  matches: ["<all_urls>"],
  run_at: "document_idle",
}

// DOM Agent interface
interface DOMSelection {
  selector: string
  text: string
  html: string
  rect: { x: number; y: number; width: number; height: number }
}

interface DOMAction {
  type: "click" | "fill" | "scroll" | "select" | "extract"
  selector?: string
  value?: string
  options?: Record<string, unknown>
}

// Selection tracking
let currentSelection: DOMSelection | null = null

// Listen for selection changes
document.addEventListener("selectionchange", () => {
  const selection = window.getSelection()
  if (selection && selection.toString().trim()) {
    const range = selection.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    currentSelection = {
      selector: getUniqueSelector(range.startContainer.parentElement),
      text: selection.toString(),
      html: range.cloneContents().textContent || "",
      rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
    }
  } else {
    currentSelection = null
  }
})

// Generate unique CSS selector for an element
function getUniqueSelector(element: Element | null): string {
  if (!element) return ""
  if (element.id) return `#${element.id}`
  
  const path: string[] = []
  let current: Element | null = element
  
  while (current && current !== document.body) {
    let selector = current.tagName.toLowerCase()
    if (current.className && typeof current.className === "string") {
      selector += "." + current.className.split(" ").filter(Boolean).join(".")
    }
    path.unshift(selector)
    current = current.parentElement
  }
  
  return path.join(" > ").slice(0, 100)
}

// Execute DOM actions
async function executeDOMAction(action: DOMAction): Promise<unknown> {
  const { type, selector, value, options } = action
  
  let element: Element | null = null
  if (selector) {
    element = document.querySelector(selector)
    if (!element) {
      throw new Error(`Element not found: ${selector}`)
    }
  }
  
  switch (type) {
    case "click":
      if (element) (element as HTMLElement).click()
      return { success: true }
    
    case "fill":
      if (element && value !== undefined) {
        (element as HTMLInputElement).value = value
        element.dispatchEvent(new Event("input", { bubbles: true }))
        element.dispatchEvent(new Event("change", { bubbles: true }))
      }
      return { success: true }
    
    case "scroll":
      if (element) {
        element.scrollIntoView({ behavior: "smooth", ...(options as ScrollIntoViewOptions) })
      } else {
        window.scrollBy({ top: (options as { y?: number })?.y || 100, behavior: "smooth" })
      }
      return { success: true }
    
    case "select":
      if (selector) {
        const elements = document.querySelectorAll(selector)
        return {
          count: elements.length,
          elements: Array.from(elements).slice(0, 10).map((el) => ({
            tag: el.tagName,
            text: el.textContent?.slice(0, 100),
            selector: getUniqueSelector(el),
          })),
        }
      }
      return { count: 0, elements: [] }
    
    case "extract":
      return {
        url: window.location.href,
        title: document.title,
        selection: currentSelection,
        pageText: document.body.innerText.slice(0, 5000),
        metadata: {
          description: document.querySelector('meta[name="description"]')?.getAttribute("content"),
          keywords: document.querySelector('meta[name="keywords"]')?.getAttribute("content"),
        },
      }
    
    default:
      throw new Error(`Unknown action type: ${type}`)
  }
}

// Listen for messages from Service Worker
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "DOM_ACTION") {
    executeDOMAction(message.payload)
      .then((result) => sendResponse({ success: true, result }))
      .catch((error) => sendResponse({ success: false, error: error.message }))
    return true // Keep channel open for async response
  }
  
  if (message.type === "GET_SELECTION") {
    sendResponse({ selection: currentSelection })
    return false
  }
  
  if (message.type === "GET_PAGE_INFO") {
    sendResponse({
      url: window.location.href,
      title: document.title,
      domain: window.location.hostname,
    })
    return false
  }
})

// Notify SW that content script is ready
chrome.runtime.sendMessage({
  type: "CONTENT_SCRIPT_READY",
  payload: {
    url: window.location.href,
    title: document.title,
  },
})

console.log("[Collider] Content script loaded")
