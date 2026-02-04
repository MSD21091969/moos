/**
 * Context Manager - Central state management
 * Manages MainContext, TabContexts, and Cache
 */

import { Storage } from "@plasmohq/storage"

// Types
export interface MainContext {
  user: {
    id: string
    email: string
    profile: { display_name?: string }
  } | null
  permissions: AppPermission[]
  secrets: Record<string, string>
  apps: AppInfo[]
}

export interface TabContext {
  app: string  // "cloud://app1" | "filesyst://FFS1"
  node: string // "/dashboard"
  domain: "FILESYST" | "CLOUD" | "ADMIN"
  container: NodeContainer | null
  threadId: string
  messages: Message[]
}

export interface PiPContext {
  mode: "single" | "multi"
  focuses: string[]
  activeTabKey: string
}

export interface ContextCache {
  appConfigs: Map<string, AppConfig>
  nodeContexts: Map<string, NodeContainer>
  policies: CachePolicies
}

export interface CachePolicies {
  nodeContextTTL: number  // -1 = infinite (SSE invalidation)
  toolIndexRefresh: number
  appConfigRefresh: number
}

interface AppPermission {
  id: string
  application_id: string
  can_read: boolean
  can_write: boolean
  is_admin: boolean
}

interface AppInfo {
  id: string
  app_id: string
  display_name: string
}

interface AppConfig {
  // Backend-only, but we may cache some public parts
}

interface NodeContainer {
  manifest: Record<string, unknown>
  instructions: string[]
  rules: string[]
  skills: string[]
  tools: { name: string; schema: unknown }[]
  knowledge: string[]
  workflows: unknown[]
  configs: Record<string, unknown>
}

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: number
}

// Storage
const storage = new Storage({ area: "session" })

// Default values
const defaultMainContext: MainContext = {
  user: null,
  permissions: [],
  secrets: {},
  apps: [],
}

const defaultCachePolicies: CachePolicies = {
  nodeContextTTL: -1,
  toolIndexRefresh: 60000,
  appConfigRefresh: 300000,
}

/**
 * Context Manager Singleton
 */
class ContextManagerClass {
  private main: MainContext = defaultMainContext
  private tabs: Map<string, TabContext> = new Map()
  private pip: PiPContext = { mode: "single", focuses: [], activeTabKey: "" }
  private cache: ContextCache = {
    appConfigs: new Map(),
    nodeContexts: new Map(),
    policies: defaultCachePolicies,
  }

  // Initialize from storage
  async init() {
    const storedMain = await storage.get<MainContext>("main_context")
    if (storedMain) this.main = storedMain

    const storedTabs = await storage.get<[string, TabContext][]>("tab_contexts")
    if (storedTabs) this.tabs = new Map(storedTabs)

    const storedPip = await storage.get<PiPContext>("pip_context")
    if (storedPip) this.pip = storedPip

    console.log("🔧 Context Manager initialized")
  }

  // Main context
  getMain(): MainContext {
    return this.main
  }

  async setMain(ctx: Partial<MainContext>) {
    this.main = { ...this.main, ...ctx }
    await storage.set("main_context", this.main)
  }

  // Tab contexts
  getTab(tabKey: string): TabContext | undefined {
    return this.tabs.get(tabKey)
  }

  async setTab(tabKey: string, ctx: TabContext) {
    this.tabs.set(tabKey, ctx)
    await storage.set("tab_contexts", Array.from(this.tabs.entries()))
  }

  async removeTab(tabKey: string) {
    this.tabs.delete(tabKey)
    await storage.set("tab_contexts", Array.from(this.tabs.entries()))
  }

  getAllTabs(): Map<string, TabContext> {
    return this.tabs
  }

  // PiP context
  getPip(): PiPContext {
    return this.pip
  }

  async setPip(ctx: Partial<PiPContext>) {
    this.pip = { ...this.pip, ...ctx }
    await storage.set("pip_context", this.pip)
  }

  // Cache
  getCachedNode(key: string): NodeContainer | undefined {
    return this.cache.nodeContexts.get(key)
  }

  setCachedNode(key: string, container: NodeContainer) {
    this.cache.nodeContexts.set(key, container)
  }

  invalidateCache(key?: string) {
    if (key) {
      this.cache.nodeContexts.delete(key)
    } else {
      this.cache.nodeContexts.clear()
    }
  }

  // Merge context for agent
  getMergedContext(tabKey: string): MainContext & { tab: TabContext | null } {
    return {
      ...this.main,
      tab: this.tabs.get(tabKey) || null,
    }
  }
}

export const ContextManager = new ContextManagerClass()
