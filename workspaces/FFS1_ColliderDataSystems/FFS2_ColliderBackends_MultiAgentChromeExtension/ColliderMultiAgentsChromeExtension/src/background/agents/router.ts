/**
 * LangGraph Router - Routes messages to appropriate agents
 */

import { ContextManager, type MainContext, type TabContext } from "../context/manager"

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

  // MVP: Simple echo response
  // Production: Route to actual agent implementations
  switch (agent) {
    case "filesyst":
      return `[FILESYST Agent] Processing: ${message}`
    case "dom":
      return `[DOM Agent] Processing: ${message}`
    case "cloud":
    default:
      return `[CLOUD Agent] Processing: ${message}`
  }
}
