/**
 * Agent Tools - Callable tools for LangGraph agent
 * 
 * Provides tools for:
 * - Knowledge base search (VectorDbServer)
 * - Node navigation and listing (DataServer)
 * - Graph operations (GraphToolServer)
 */

import { tool } from "@langchain/core/tools"
import { z } from "zod"
import * as vectordb from "../external/vectordb"
import * as dataApi from "../external/data"
import { graphToolClient } from "../external/graphtool"
import { ContextManager } from "../context/manager"

/**
 * Search knowledge base for relevant information (Semantic Search)
 */
export const searchKnowledgeTool = tool(
  async ({ query, nResults = 5 }: { query: string; nResults?: number }) => {
    try {
      const results = await vectordb.search(query, nResults)
      if (results.length === 0) {
        return "No relevant documents found."
      }
      return JSON.stringify(results, null, 2)
    } catch (error) {
      return `Error searching knowledge: ${error}`
    }
  },
  {
    name: "search_knowledge",
    description: "Semantic search the knowledge base for relevant documents and information. Use this when the user asks about something that might be in documentation, knowledge articles, or stored content.",
    schema: z.object({
      query: z.string().describe("The search query to find relevant knowledge"),
      nResults: z.number().optional().describe("Number of results to return (default: 5)"),
    }),
  }
)

/**
 * Embed new content into the knowledge base
 */
export const embedContentTool = tool(
  async ({ text, documentId, metadata }: { text: string; documentId: string; metadata?: Record<string, unknown> }) => {
    try {
      const result = await vectordb.embed(text, documentId, metadata)
      return `Successfully embedded document: ${result.id}`
    } catch (error) {
      return `Error embedding content: ${error}`
    }
  },
  {
    name: "embed_content",
    description: "Add new content to the knowledge base by embedding it. Use this when the user wants to store information for later retrieval.",
    schema: z.object({
      text: z.string().describe("The text content to embed"),
      documentId: z.string().describe("A unique identifier for the document"),
      metadata: z.record(z.string(), z.any()).optional().describe("Optional metadata like source, date, tags"),
    }),
  }
)

/**
 * Get node data from the current app
 */
export const getNodeTool = tool(
  async ({ path, appId }: { path: string; appId: string }) => {
    try {
      const node = await dataApi.getNode(appId, path)
      return JSON.stringify(node, null, 2)
    } catch (error) {
      return `Error getting node: ${error}`
    }
  },
  {
    name: "get_node",
    description: "Get detailed information about a specific node in the app. Use this to retrieve node metadata, content, and container information.",
    schema: z.object({
      path: z.string().describe("The path to the node (e.g., '/docs/api')"),
      appId: z.string().describe("The app ID to get the node from"),
    }),
  }
)

/**
 * Navigate to a different node
 */
export const navigateTool = tool(
  async ({ path, tabKey }: { path: string; tabKey: string }) => {
    try {
      const context = ContextManager.getTab(tabKey)
      if (!context) {
        return "Error: Tab context not found"
      }

      const appId = context.app.replace(/^(cloud|filesyst):\/\//, "")
      const node = await dataApi.getNode(appId, path)

      // Update tab context with new node
      await ContextManager.setTab(tabKey, {
        ...context,
        node: path,
        container: node.container,
      })

      return `Navigated to ${path}. Node: ${JSON.stringify(node, null, 2)}`
    } catch (error) {
      return `Error navigating: ${error}`
    }
  },
  {
    name: "navigate",
    description: "Navigate to a different node path within the current app. Use this when the user wants to go to a specific location.",
    schema: z.object({
      path: z.string().describe("The path to navigate to"),
      tabKey: z.string().describe("The tab key for context"),
    }),
  }
)

/**
 * List children of a node
 */
export const listNodesTool = tool(
  async ({ path, appId }: { path: string; appId: string }) => {
    try {
      const nodes = await dataApi.getNodeTree(appId)
      // Filter to children of the given path
      const children = nodes.filter((n) => {
        const parentPath = path === "/" ? "" : path
        return n.path.startsWith(parentPath) && n.path !== path
      })
      return JSON.stringify(children.slice(0, 20), null, 2)
    } catch (error) {
      return `Error listing nodes: ${error}`
    }
  },
  {
    name: "list_nodes",
    description: "List child nodes under a given path. Use this to explore the app structure.",
    schema: z.object({
      path: z.string().describe("The parent path to list children of"),
      appId: z.string().describe("The app ID"),
    }),
  }
)

/**
 * Execute a graph workflow via GraphToolServer
 */
export const executeWorkflowTool = tool(
  async ({ workflowName, inputs, appId }: { workflowName: string; inputs: Record<string, unknown>; appId: string }) => {
    try {
      const result = await graphToolClient.executeWorkflow(
        { name: workflowName, ...inputs },
        { appId }
      )
      return JSON.stringify(result, null, 2)
    } catch (error) {
      return `Error executing workflow: ${error}`
    }
  },
  {
    name: "execute_workflow",
    description: "Execute a named workflow from the graph tool server. Use this for complex multi-step operations.",
    schema: z.object({
      workflowName: z.string().describe("The name of the workflow to execute"),
      inputs: z.record(z.string(), z.any()).describe("Input parameters for the workflow"),
      appId: z.string().describe("The app ID context"),
    }),
  }
)

/**
 * Execute a graph tool operation
 */
export const executeGraphToolTool = tool(
  async ({ toolName, args, appId }: { toolName: string; args: Record<string, unknown>; appId: string }) => {
    try {
      const result = await graphToolClient.executeTool(
        toolName,
        args,
        { appId }
      )
      return JSON.stringify(result, null, 2)
    } catch (error) {
      return `Error executing graph tool: ${error}`
    }
  },
  {
    name: "execute_graph_tool",
    description: "Execute a specific tool from the graph tool server. Available tools include code execution, file operations, and API calls.",
    schema: z.object({
      toolName: z.string().describe("The name of the tool to execute"),
      args: z.record(z.string(), z.any()).describe("Arguments for the tool"),
      appId: z.string().describe("The app ID context"),
    }),
  }
)

/**
 * Get resolved container with inheritance
 */
export const getResolvedContainerTool = tool(
  async ({ path, appId }: { path: string; appId: string }) => {
    try {
      const resolved = await dataApi.getResolvedContainer(appId, path)
      return JSON.stringify(resolved, null, 2)
    } catch (error) {
      return `Error getting resolved container: ${error}`
    }
  },
  {
    name: "get_resolved_container",
    description: "Get a node's container with all inheritance resolved. This shows the full effective configuration after merging parent containers.",
    schema: z.object({
      path: z.string().describe("The node path"),
      appId: z.string().describe("The app ID"),
    }),
  }
)

/**
 * Get all available tools for the agent
 */
export function getAgentTools(_tabKey: string) {
  return [
    // Knowledge/Search tools
    searchKnowledgeTool,
    embedContentTool,

    // Node/Navigation tools
    getNodeTool,
    navigateTool,
    listNodesTool,
    getResolvedContainerTool,

    // Graph operation tools
    executeWorkflowTool,
    executeGraphToolTool,
  ]
}
