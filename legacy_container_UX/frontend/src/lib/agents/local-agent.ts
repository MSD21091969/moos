/**
 * Local Agent - WebLLM with File System Access
 * 
 * In-browser LLM with full browser capabilities:
 * - File System Access API for reading/writing files
 * - DOM access for browser automation
 * - Gemini API proxy for complex queries
 */

import { CreateMLCEngine, type MLCEngine, type ChatCompletionMessageParam } from '@mlc-ai/web-llm';
import type {
  LocalAgentConfig,
  LocalAgentCapabilities,
  FunctionDeclaration,
  ToolCall,
  FileOperationResult,
  AgentContext,
  AgentEvent,
  AgentEventHandler,
  CodeArtifact,
} from './types';
import { CodingAgent } from './coding-agent';

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_MODEL = 'Qwen2.5-Coder-7B-Instruct-q4f16_1-MLC';
const DEFAULT_CONTEXT_SIZE = 4096;
const DEFAULT_TEMPERATURE = 0.7;

// ============================================================================
// File System Types (Web File System Access API)
// ============================================================================

interface FileSystemDirectoryHandle {
  kind: 'directory';
  name: string;
  getFileHandle(name: string, options?: { create?: boolean }): Promise<FileSystemFileHandle>;
  getDirectoryHandle(name: string, options?: { create?: boolean }): Promise<FileSystemDirectoryHandle>;
  values(): AsyncIterable<FileSystemFileHandle | FileSystemDirectoryHandle>;
  removeEntry(name: string, options?: { recursive?: boolean }): Promise<void>;
}

interface FileSystemFileHandle {
  kind: 'file';
  name: string;
  getFile(): Promise<File>;
  createWritable(): Promise<FileSystemWritableFileStream>;
}

interface FileSystemWritableFileStream extends WritableStream {
  write(data: string | ArrayBuffer | Blob): Promise<void>;
  close(): Promise<void>;
}

declare global {
  interface Window {
    showDirectoryPicker?: () => Promise<FileSystemDirectoryHandle>;
    showOpenFilePicker?: (options?: {
      types?: Array<{ description: string; accept: Record<string, string[]> }>;
      multiple?: boolean;
    }) => Promise<FileSystemFileHandle[]>;
    showSaveFilePicker?: (options?: {
      suggestedName?: string;
      types?: Array<{ description: string; accept: Record<string, string[]> }>;
    }) => Promise<FileSystemFileHandle>;
  }
}

// ============================================================================
// Local Agent Class
// ============================================================================

export class LocalAgent {
  private engine: MLCEngine | null = null;
  private eventHandler: AgentEventHandler | null = null;
  private isLoading = false;
  
  // File system state (lazy initialization)
  private workspaceHandle: FileSystemDirectoryHandle | null = null;
  
  // Gemini proxy for complex queries
  private codingAgent: CodingAgent | null = null;

  private config: LocalAgentConfig;
  private tools: FunctionDeclaration[] = [];
  private systemInstruction: string = '';

  constructor(config?: Partial<LocalAgentConfig>, geminiApiKey?: string) {
    this.config = {
      model: config?.model ?? DEFAULT_MODEL,
      contextWindowSize: config?.contextWindowSize ?? DEFAULT_CONTEXT_SIZE,
      temperature: config?.temperature ?? DEFAULT_TEMPERATURE,
      tools: config?.tools,
    };
    if (config?.tools) this.tools = config.tools;

    // Initialize Gemini proxy if API key provided
    if (geminiApiKey) {
      this.codingAgent = new CodingAgent(geminiApiKey);
    }
  }

  // ==========================================================================
  // Public API
  // ==========================================================================

  /**
   * Set event handler for agent lifecycle events
   */
  onEvent(handler: AgentEventHandler): void {
    this.eventHandler = handler;
  }

  /**
   * Update tools available to the local agent
   */
  setTools(tools: FunctionDeclaration[]): void {
    this.tools = tools;
  }

  /**
   * Update system instruction
   */
  setSystemInstruction(instruction: string): void {
    this.systemInstruction = instruction;
  }

  /**
   * Get agent capabilities based on browser support
   */
  getCapabilities(): LocalAgentCapabilities {
    return {
      fileSystem: 'showDirectoryPicker' in window,
      webGPU: 'gpu' in navigator,
      geminiProxy: this.codingAgent !== null,
    };
  }

  /**
   * Initialize the local LLM engine
   */
  async initialize(): Promise<void> {
    if (this.engine || this.isLoading) return;

    const capabilities = this.getCapabilities();
    if (!capabilities.webGPU) {
      throw new Error('WebGPU not supported in this browser');
    }

    this.isLoading = true;

    try {
      this.engine = await CreateMLCEngine(this.config.model, {
        initProgressCallback: (report) => {
          this.emit({
            type: 'model_loading',
            agent: 'local',
            progress: report.progress,
            text: report.text,
          });
        },
      });

      this.emit({ type: 'connected', agent: 'local' });
    } catch (error) {
      this.emit({ type: 'error', agent: 'local', error: error as Error });
      throw error;
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Check if engine is ready
   */
  isReady(): boolean {
    return this.engine !== null;
  }

  /**
   * Generate a response
   */
  async generate(
    prompt: string,
    context?: AgentContext
  ): Promise<{ text: string; toolCalls?: ToolCall[]; artifacts?: CodeArtifact[] }> {
    if (!this.engine) {
      await this.initialize();
    }

    if (!this.engine) {
      throw new Error('Local agent failed to initialize');
    }

    this.emit({ type: 'thinking', agent: 'local' });

    // Build messages
    const messages = this.buildMessages(prompt, context);

    // Convert tools to OpenAI format for WebLLM
    const tools = this.tools.length > 0 ? this.convertToolsToOpenAI() : undefined;

    try {
      const response = await this.engine.chat.completions.create({
        messages,
        temperature: this.config.temperature,
        max_tokens: 2048,
        tools,
        tool_choice: tools ? 'auto' : undefined,
      });

      const choice = response.choices[0];
      const text = choice.message.content ?? '';
      const toolCalls = choice.message.tool_calls?.map(tc => ({
        id: tc.id,
        type: 'function' as const,
        function: {
          name: tc.function.name,
          arguments: tc.function.arguments,
        },
      }));

      // Extract artifacts from response
      const artifacts = this.extractArtifacts(text);

      // Emit events
      if (toolCalls) {
        for (const call of toolCalls) {
          this.emit({ type: 'tool_call', agent: 'local', call });
        }
      }
      if (artifacts) {
        for (const artifact of artifacts) {
          this.emit({ type: 'artifact', agent: 'local', artifact });
        }
      }

      return { text, toolCalls, artifacts };
    } catch (error) {
      this.emit({ type: 'error', agent: 'local', error: error as Error });
      throw error;
    }
  }

  /**
   * Stream a response
   */
  async *generateStream(
    prompt: string,
    context?: AgentContext
  ): AsyncGenerator<{ text?: string; toolCalls?: ToolCall[] }> {
    if (!this.engine) {
      await this.initialize();
    }

    if (!this.engine) {
      throw new Error('Local agent failed to initialize');
    }

    this.emit({ type: 'thinking', agent: 'local' });

    const messages = this.buildMessages(prompt, context);
    const tools = this.tools.length > 0 ? this.convertToolsToOpenAI() : undefined;

    try {
      const stream = await this.engine.chat.completions.create({
        messages,
        temperature: this.config.temperature,
        max_tokens: 2048,
        tools,
        tool_choice: tools ? 'auto' : undefined,
        stream: true,
        stream_options: { include_usage: true },
      });

      let accumulatedText = '';

      for await (const chunk of stream) {
        const delta = chunk.choices[0]?.delta;
        
        if (delta?.content) {
          accumulatedText += delta.content;
          yield { text: accumulatedText };
        }

        if (delta?.tool_calls) {
          const toolCalls = delta.tool_calls.map(tc => ({
            id: tc.id ?? crypto.randomUUID(),
            type: 'function' as const,
            function: {
              name: tc.function?.name ?? '',
              arguments: tc.function?.arguments ?? '{}',
            },
          }));
          yield { toolCalls };
        }
      }
    } catch (error) {
      this.emit({ type: 'error', agent: 'local', error: error as Error });
      throw error;
    }
  }

  /**
   * Proxy a complex query to Gemini
   */
  async proxyToGemini(prompt: string, context?: AgentContext): Promise<string> {
    if (!this.codingAgent) {
      throw new Error('Gemini proxy not available - no API key provided');
    }

    const response = await this.codingAgent.generate({
      prompt,
      context: context ?? {
        workspaceState: { currentSessionId: null, containers: [], selectedNodeId: null, breadcrumb: [] },
        canvasState: { nodes: [], edges: [], viewport: { x: 0, y: 0, zoom: 1 } },
        messages: [],
        systemContext: '',
      },
    });

    return response.text;
  }

  /**
   * Reset conversation
   */
  async resetChat(): Promise<void> {
    if (this.engine) {
      await this.engine.resetChat();
    }
  }

  /**
   * Unload the model
   */
  async unload(): Promise<void> {
    if (this.engine) {
      await this.engine.unload();
      this.engine = null;
    }
    this.emit({ type: 'disconnected', agent: 'local' });
  }

  // ==========================================================================
  // File System Operations (Lazy Initialization)
  // ==========================================================================

  /**
   * Request workspace directory access (lazy)
   */
  async requestWorkspaceAccess(): Promise<boolean> {
    if (!('showDirectoryPicker' in window)) {
      return false;
    }

    try {
      this.workspaceHandle = await window.showDirectoryPicker!();
      return true;
    } catch (error) {
      // User cancelled or permission denied
      console.warn('[LocalAgent] Workspace access denied:', error);
      return false;
    }
  }

  /**
   * Check if workspace access is granted
   */
  hasWorkspaceAccess(): boolean {
    return this.workspaceHandle !== null;
  }

  /**
   * Read a file from the workspace
   */
  async readFile(path: string): Promise<FileOperationResult> {
    if (!this.workspaceHandle) {
      // Lazy: request access on first file operation
      const granted = await this.requestWorkspaceAccess();
      if (!granted) {
        return { success: false, error: 'Workspace access not granted' };
      }
    }

    try {
      const handle = await this.resolveFilePath(path);
      if (!handle || handle.kind !== 'file') {
        return { success: false, error: `File not found: ${path}` };
      }

      const file = await (handle as FileSystemFileHandle).getFile();
      const content = await file.text();

      return { success: true, path, content };
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  /**
   * Write a file to the workspace
   */
  async writeFile(path: string, content: string): Promise<FileOperationResult> {
    if (!this.workspaceHandle) {
      const granted = await this.requestWorkspaceAccess();
      if (!granted) {
        return { success: false, error: 'Workspace access not granted' };
      }
    }

    try {
      const handle = await this.resolveFilePath(path, true);
      if (!handle || handle.kind !== 'file') {
        return { success: false, error: `Cannot write to: ${path}` };
      }

      const writable = await (handle as FileSystemFileHandle).createWritable();
      await writable.write(content);
      await writable.close();

      return { success: true, path };
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  /**
   * List files in a directory
   */
  async listDirectory(path: string = ''): Promise<FileOperationResult & { files?: string[] }> {
    if (!this.workspaceHandle) {
      const granted = await this.requestWorkspaceAccess();
      if (!granted) {
        return { success: false, error: 'Workspace access not granted' };
      }
    }

    try {
      let dirHandle: FileSystemDirectoryHandle = this.workspaceHandle!;

      if (path) {
        const handle = await this.resolveFilePath(path);
        if (!handle || handle.kind !== 'directory') {
          return { success: false, error: `Directory not found: ${path}` };
        }
        dirHandle = handle as FileSystemDirectoryHandle;
      }

      const files: string[] = [];
      for await (const entry of dirHandle.values()) {
        files.push(entry.kind === 'directory' ? `${entry.name}/` : entry.name);
      }

      return { success: true, path, files };
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  // ==========================================================================
  // Private Methods
  // ==========================================================================

  private emit(event: AgentEvent): void {
    this.eventHandler?.(event);
  }

  private buildMessages(prompt: string, context?: AgentContext): ChatCompletionMessageParam[] {
    const messages: ChatCompletionMessageParam[] = [];

    // System message
    const systemParts: string[] = [];
    
    if (this.systemInstruction) {
      systemParts.push(this.systemInstruction);
    }

    // Add capabilities info
    const caps = this.getCapabilities();
    systemParts.push(`\n## Your Capabilities`);
    systemParts.push(`- File System Access: ${caps.fileSystem ? 'Available' : 'Not available'}`);
    systemParts.push(`- Gemini Proxy: ${caps.geminiProxy ? 'Available for complex queries' : 'Not available'}`);

    // Add context
    if (context) {
      systemParts.push(this.formatContext(context));
    }

    if (systemParts.length > 0) {
      messages.push({
        role: 'system',
        content: systemParts.join('\n'),
      });
    }

    // Add conversation history
    if (context?.messages) {
      for (const msg of context.messages.slice(-10)) { // Last 10 messages
        if (msg.role === 'user' || msg.role === 'assistant') {
          messages.push({
            role: msg.role,
            content: msg.content,
          });
        }
      }
    }

    // Add the prompt
    messages.push({
      role: 'user',
      content: prompt,
    });

    return messages;
  }

  private formatContext(context: AgentContext): string {
    const parts: string[] = ['\n## Current Context'];

    if (context.workspaceState) {
      parts.push(`Session: ${context.workspaceState.currentSessionId ?? 'None'}`);
      parts.push(`Selected: ${context.workspaceState.selectedNodeId ?? 'None'}`);
    }

    if (context.canvasState) {
      parts.push(`Canvas: ${context.canvasState.nodes.length} nodes, ${context.canvasState.edges.length} edges`);
    }

    return parts.join('\n');
  }

  private convertToolsToOpenAI(): Array<{
    type: 'function';
    function: {
      name: string;
      description: string;
      parameters: Record<string, unknown>;
    };
  }> {
    return this.tools.map(tool => ({
      type: 'function' as const,
      function: {
        name: tool.name,
        description: tool.description,
        parameters: (tool.parameters ?? {}) as Record<string, unknown>,
      },
    }));
  }

  private extractArtifacts(text: string): CodeArtifact[] {
    const artifacts: CodeArtifact[] = [];
    const codeBlockRegex = /```(\w+)(?::([^\n]+))?\n([\s\S]*?)```/g;
    
    let match;
    while ((match = codeBlockRegex.exec(text)) !== null) {
      const [, language, filename, content] = match;
      if (content.trim().split('\n').length < 3) continue;

      artifacts.push({
        id: crypto.randomUUID(),
        type: 'code',
        language: language.toLowerCase(),
        filename: filename?.trim(),
        content: content.trim(),
      });
    }

    return artifacts;
  }

  private async resolveFilePath(
    path: string,
    create = false
  ): Promise<FileSystemFileHandle | FileSystemDirectoryHandle | null> {
    if (!this.workspaceHandle) return null;

    const parts = path.split('/').filter(Boolean);
    let current: FileSystemDirectoryHandle = this.workspaceHandle;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;

      try {
        if (isLast && !path.endsWith('/')) {
          // File
          return await current.getFileHandle(part, { create });
        } else {
          // Directory
          current = await current.getDirectoryHandle(part, { create });
        }
      } catch {
        return null;
      }
    }

    return current;
  }
}

// ============================================================================
// Factory Function
// ============================================================================

export function createLocalAgent(
  config?: Partial<LocalAgentConfig>,
  geminiApiKey?: string
): LocalAgent {
  return new LocalAgent(config, geminiApiKey);
}
