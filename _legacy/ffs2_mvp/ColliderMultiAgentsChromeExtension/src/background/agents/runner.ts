/**
 * LangGraph Agent Runner - Full agentic loop with tool calling
 * 
 * Features:
 * - Streaming token output for real-time display
 * - Tool integration (search, navigate, graph operations)
 * - Context-aware system prompts
 */

import { ChatGoogleGenerativeAI } from "@langchain/google-genai"
import { HumanMessage, SystemMessage, AIMessageChunk, type BaseMessage } from "@langchain/core/messages"
import { StateGraph, END, START, Annotation } from "@langchain/langgraph"
import { ToolNode } from "@langchain/langgraph/prebuilt"
import { getAgentTools } from "./tools"
import { ContextManager, type MainContext, type TabContext } from "../context/manager"

/**
 * Streaming callback type
 */
export type StreamCallback = (token: string, done: boolean) => void

/**
 * Agent state definition using LangGraph Annotation
 */
const AgentState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  tabKey: Annotation<string>(),
  appId: Annotation<string>(),
})

type AgentStateType = typeof AgentState.State

/**
 * Build system prompt from context
 */
function buildSystemPrompt(context: MainContext & { tab: TabContext | null }): string {
  const parts: string[] = [
    "You are a helpful AI assistant embedded in the Collider application.",
    "You help users navigate, search, and interact with their apps and data.",
    "",
  ]

  // Add app context
  if (context.tab) {
    parts.push(`Current App: ${context.tab.app}`)
    parts.push(`Current Node: ${context.tab.node}`)
    parts.push(`Domain: ${context.tab.domain}`)
    parts.push("")
  }

  // Add instructions from node container
  const container = context.tab?.container

  if (container?.instructions?.length) {
    parts.push("## Instructions")
    parts.push(...container.instructions)
    parts.push("")
  }

  // Add knowledge context
  if (container?.knowledge?.length) {
    parts.push("## Knowledge Context")
    parts.push(...container.knowledge.slice(0, 5)) // Limit to first 5
    parts.push("")
  }

  parts.push("Use the available tools to help answer questions and perform actions.")
  parts.push("Be concise but helpful in your responses.")

  return parts.join("\n")
}

/**
 * Create and run the agent graph (non-streaming)
 */
export async function runAgent(
  tabKey: string,
  message: string,
  apiKey: string
): Promise<string> {
  const result = await runAgentWithStreaming(tabKey, message, apiKey, () => { })
  return result
}

/**
 * Create and run the agent graph with streaming support
 */
export async function runAgentWithStreaming(
  tabKey: string,
  message: string,
  apiKey: string,
  onToken: StreamCallback
): Promise<string> {
  // Get context
  const context = ContextManager.getMergedContext(tabKey)
  const tools = getAgentTools(tabKey)

  // Initialize LLM with tools bound and streaming enabled
  const llm = new ChatGoogleGenerativeAI({
    model: "gemini-2.0-flash",
    apiKey,
    temperature: 0.7,
    streaming: true,
  }).bindTools(tools)

  // Create tool node
  const toolNode = new ToolNode(tools)

  // Accumulate streamed content
  let streamedContent = ""

  // Define the LLM call function with streaming
  async function callModel(state: AgentStateType): Promise<Partial<AgentStateType>> {
    const systemPrompt = buildSystemPrompt(context)
    const messages = [new SystemMessage(systemPrompt), ...state.messages]

    // Stream tokens
    const stream = await llm.stream(messages)
    const chunks: AIMessageChunk[] = []

    for await (const chunk of stream) {
      chunks.push(chunk)
      if (typeof chunk.content === "string") {
        streamedContent += chunk.content
        onToken(streamedContent, false)
      }
    }

    // Combine all chunks into final message
    let finalMessage = chunks[0]
    for (let i = 1; i < chunks.length; i++) {
      finalMessage = finalMessage.concat(chunks[i])
    }

    return { messages: [finalMessage] }
  }

  // Define the routing function
  function shouldContinue(state: AgentStateType): "tools" | typeof END {
    const lastMessage = state.messages[state.messages.length - 1]

    // Check if there are tool calls
    if (
      lastMessage &&
      "tool_calls" in lastMessage &&
      Array.isArray(lastMessage.tool_calls) &&
      lastMessage.tool_calls.length > 0
    ) {
      return "tools"
    }

    return END
  }

  // Build the graph
  const workflow = new StateGraph(AgentState)
    .addNode("agent", callModel)
    .addNode("tools", toolNode)
    .addEdge(START, "agent")
    .addConditionalEdges("agent", shouldContinue)
    .addEdge("tools", "agent")

  // Compile the graph
  const app = workflow.compile()

  // Run the agent
  const appId = context.tab?.app.replace(/^(cloud|filesyst):\/\//, "") || ""

  try {
    const result = await app.invoke({
      messages: [new HumanMessage(message)],
      tabKey,
      appId,
    })

    // Extract final response
    const lastMessage = result.messages[result.messages.length - 1]

    let finalContent = ""
    if (lastMessage && "content" in lastMessage) {
      const content = lastMessage.content
      if (typeof content === "string") {
        finalContent = content
      } else if (Array.isArray(content)) {
        finalContent = content
          .map((c) => (typeof c === "string" ? c : (c as { text?: string }).text || ""))
          .join("")
      }
    }

    // Signal completion
    onToken(finalContent || streamedContent, true)
    return finalContent || streamedContent || "I couldn't generate a response. Please try again."
  } catch (error) {
    onToken("", true)
    throw error
  }
}

/**
 * Get API key from context secrets
 */
export async function getApiKey(): Promise<string | null> {
  const mainContext = ContextManager.getMain()
  return mainContext?.secrets?.GOOGLE_API_KEY || null
}
