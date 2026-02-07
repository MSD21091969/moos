/**
 * LangGraph Router - Routes messages to appropriate agents
 */

import { ContextManager, type MainContext, type TabContext } from "../context/manager"
// Dynamic import to avoid crashing service worker with heavy LangChain libs
let runnerModule: typeof import("./runner") | null = null

async function getRunner() {
  if (!runnerModule) {
    try {
      runnerModule = await import("./runner")
    } catch (e) {
      console.error("[Router] Failed to load runner module:", e)
      return null
    }
  }
  return runnerModule
}

export async function getApiKey(): Promise<string | null> {
  const runner = await getRunner()
  return runner?.getApiKey() ?? null
}

export type AgentType = "cloud" | "filesyst" | "dom"

export interface RouteResult {
  agent: AgentType
  context: MainContext & { tab: TabContext | null }
}

/**
 * Route a message to the appropriate agent based on context
 */
export function routeMessage(tabKey: string, message: string): RouteResult {
  const context = ContextManager.getMergedContext(tabKey)
  const tab = context.tab

  // Determine agent based on domain
  let agent: AgentType = "cloud"

  if (tab) {
    if (tab.domain === "FILESYST") {
      agent = "filesyst"
    } else if (tab.domain === "CLOUD") {
      agent = "cloud"
    }

    // Check if this is a DOM action request
    if (message.toLowerCase().includes("click") ||
      message.toLowerCase().includes("type") ||
      message.toLowerCase().includes("scroll")) {
      agent = "dom"
    }
  }

  return { agent, context }
}

/**
 * Process message through router and agent
 */
export async function processMessage(
  tabKey: string,
  message: string
): Promise<string> {
  const { agent, context } = routeMessage(tabKey, message)

  console.log(`🎯 Routing to ${agent} agent for tab ${tabKey}`)

  // Get API key from context
  const apiKey = await getApiKey()

  if (!apiKey) {
    console.warn("⚠️ No API key found, falling back to stub response")
    return getFallbackResponse(agent, message)
  }

  try {
    // Dynamically load runner to avoid crashing service worker
    const runner = await getRunner()
    if (!runner) {
      return "AI agent not available - module failed to load"
    }
    const response = await runner.runAgent(tabKey, message, apiKey)
    return response
  } catch (error) {
    console.error("❌ Agent error:", error)
    return `Error processing request: ${error instanceof Error ? error.message : String(error)}`
  }
}

/**
 * Fallback responses when API key not available
 */
function getFallbackResponse(agent: AgentType, message: string): string {
  switch (agent) {
    case "filesyst":
      return `[FILESYST Agent] Processing: ${message}\n\n(Note: No API key configured. Add GOOGLE_API_KEY to secrets for AI responses.)`
    case "dom":
      return `[DOM Agent] Processing: ${message}\n\n(Note: No API key configured. Add GOOGLE_API_KEY to secrets for AI responses.)`
    case "cloud":
    default:
      return `[CLOUD Agent] Processing: ${message}\n\n(Note: No API key configured. Add GOOGLE_API_KEY to secrets for AI responses.)`
  }
}
