/**
 * Agent Orchestrator
 * 
 * Routes tasks between Voice, Coding, and Local agents based on:
 * - Input type (audio vs text)
 * - Task complexity
 * - Required capabilities
 */

import type {
  AgentContext,
  AgentEvent,
  AgentEventHandler,
  OrchestratorConfig,
  OrchestratorRequest,
  OrchestratorResponse,
  TaskClassification,
  FunctionDeclaration,
  FunctionResponse,
  ToolCall,
  ToolResult,
  CodeArtifact,
} from './types';
import { VoiceAgent } from './voice-agent';
import { CodingAgent } from './coding-agent';
import { LocalAgent } from './local-agent';

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_CONFIG: OrchestratorConfig = {
  defaultAgent: 'coding',
  autoRoute: true,
  errorStrategy: 'manual', // Show error, let user switch manually
};

// Intent keywords for routing
const VOICE_KEYWORDS = [
  'talk', 'speak', 'say', 'tell me', 'chat', 'conversation',
  'listen', 'hear', 'voice', 'audio',
];

const CODING_KEYWORDS = [
  'code', 'implement', 'write', 'create', 'generate', 'build',
  'fix', 'debug', 'refactor', 'optimize', 'explain code',
  'function', 'class', 'component', 'api', 'algorithm',
  'think', 'analyze', 'reason', 'complex',
];

const LOCAL_KEYWORDS = [
  'file', 'save', 'read', 'write', 'open', 'create file',
  'local', 'offline', 'quick', 'simple',
  'workspace', 'directory', 'folder',
];

// ============================================================================
// Orchestrator Class
// ============================================================================

export class AgentOrchestrator {
  private voiceAgent: VoiceAgent | null = null;
  private codingAgent: CodingAgent | null = null;
  private localAgent: LocalAgent | null = null;
  
  private eventHandler: AgentEventHandler | null = null;
  private config: OrchestratorConfig;
  private tools: FunctionDeclaration[] = [];
  private systemInstruction: string = '';
  private toolExecutor: ((call: ToolCall) => Promise<ToolResult>) | null = null;

  constructor(
    private apiKey: string,
    config?: Partial<OrchestratorConfig>
  ) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  // ==========================================================================
  // Public API
  // ==========================================================================

  /**
   * Set event handler for all agent events
   */
  onEvent(handler: AgentEventHandler): void {
    this.eventHandler = handler;
    
    // Propagate to all agents
    this.voiceAgent?.onEvent(handler);
    this.codingAgent?.onEvent(handler);
    this.localAgent?.onEvent(handler);
  }

  /**
   * Set tool executor for handling tool calls
   */
  setToolExecutor(executor: (call: ToolCall) => Promise<ToolResult>): void {
    this.toolExecutor = executor;
  }

  /**
   * Update shared tools
   */
  setTools(tools: FunctionDeclaration[]): void {
    this.tools = tools;
    this.voiceAgent?.setTools(tools);
    this.codingAgent?.setTools(tools);
    this.localAgent?.setTools(tools);
  }

  /**
   * Update shared system instruction
   */
  setSystemInstruction(instruction: string): void {
    this.systemInstruction = instruction;
    this.voiceAgent?.setSystemInstruction(instruction);
    this.codingAgent?.setSystemInstruction(instruction);
    this.localAgent?.setSystemInstruction(instruction);
  }

  /**
   * Initialize all agents
   */
  async initialize(): Promise<void> {
    // Initialize Voice Agent
    this.voiceAgent = new VoiceAgent(this.apiKey);
    this.voiceAgent.setTools(this.tools);
    this.voiceAgent.setSystemInstruction(this.systemInstruction);
    if (this.eventHandler) this.voiceAgent.onEvent(this.eventHandler);

    // Initialize Coding Agent
    this.codingAgent = new CodingAgent(this.apiKey);
    this.codingAgent.setTools(this.tools);
    this.codingAgent.setSystemInstruction(this.systemInstruction);
    if (this.eventHandler) this.codingAgent.onEvent(this.eventHandler);

    // Initialize Local Agent (with Gemini proxy)
    this.localAgent = new LocalAgent({}, this.apiKey);
    this.localAgent.setTools(this.tools);
    this.localAgent.setSystemInstruction(this.systemInstruction);
    if (this.eventHandler) this.localAgent.onEvent(this.eventHandler);
  }

  /**
   * Process a request and route to appropriate agent
   */
  async process(request: OrchestratorRequest): Promise<OrchestratorResponse> {
    // Ensure agents are initialized
    if (!this.codingAgent) {
      await this.initialize();
    }

    // Determine which agent to use
    const classification = this.classifyTask(request);
    const agentType = request.preferredAgent ?? classification.agent;

    console.log(`[Orchestrator] Routing to ${agentType} agent (confidence: ${classification.confidence})`);

    // Route to appropriate agent
    switch (agentType) {
      case 'voice':
        return this.processWithVoice(request);
      case 'coding':
        return this.processWithCoding(request);
      case 'local':
        return this.processWithLocal(request);
      default:
        return this.processWithCoding(request);
    }
  }

  /**
   * Start voice conversation
   */
  async startVoiceSession(context?: AgentContext): Promise<void> {
    if (!this.voiceAgent) {
      await this.initialize();
    }
    await this.voiceAgent!.connect(context);
  }

  /**
   * Stop voice conversation
   */
  stopVoiceSession(): void {
    this.voiceAgent?.disconnect();
  }

  /**
   * Start voice recording
   */
  async startRecording(): Promise<void> {
    await this.voiceAgent?.startRecording();
  }

  /**
   * Stop voice recording
   */
  stopRecording(): void {
    this.voiceAgent?.stopRecording();
  }

  /**
   * Send text to voice agent
   */
  sendVoiceText(text: string): void {
    this.voiceAgent?.sendText(text);
  }

  /**
   * Send tool response to voice agent
   */
  sendVoiceToolResponse(responses: FunctionResponse[]): void {
    this.voiceAgent?.sendToolResponse(responses);
  }

  /**
   * Check voice connection status
   */
  isVoiceConnected(): boolean {
    return this.voiceAgent?.isConnected() ?? false;
  }

  /**
   * Get local agent capabilities
   */
  getLocalCapabilities() {
    return this.localAgent?.getCapabilities() ?? {
      fileSystem: false,
      webGPU: false,
      geminiProxy: false,
    };
  }

  /**
   * Request workspace access for local agent
   */
  async requestWorkspaceAccess(): Promise<boolean> {
    return this.localAgent?.requestWorkspaceAccess() ?? false;
  }

  /**
   * Cleanup all agents
   */
  async cleanup(): Promise<void> {
    this.voiceAgent?.disconnect();
    await this.localAgent?.unload();
  }

  // ==========================================================================
  // Private Methods
  // ==========================================================================

  private emit(event: AgentEvent): void {
    this.eventHandler?.(event);
  }

  private classifyTask(request: OrchestratorRequest): TaskClassification {
    // Audio input always goes to voice
    if (typeof request.input !== 'string') {
      return {
        agent: 'voice',
        confidence: 1.0,
        reasoning: 'Audio input detected',
      };
    }

    const input = request.input.toLowerCase();

    // Check for voice keywords
    const voiceScore = VOICE_KEYWORDS.filter(k => input.includes(k)).length;
    
    // Check for coding keywords
    const codingScore = CODING_KEYWORDS.filter(k => input.includes(k)).length;
    
    // Check for local keywords
    const localScore = LOCAL_KEYWORDS.filter(k => input.includes(k)).length;

    // Normalize scores
    const total = voiceScore + codingScore + localScore;
    if (total === 0) {
      return {
        agent: this.config.defaultAgent,
        confidence: 0.5,
        reasoning: 'No clear intent detected, using default',
      };
    }

    // Determine winner
    if (voiceScore >= codingScore && voiceScore >= localScore) {
      return {
        agent: 'voice',
        confidence: voiceScore / total,
        reasoning: `Voice keywords: ${voiceScore}`,
      };
    }

    if (localScore > codingScore) {
      return {
        agent: 'local',
        confidence: localScore / total,
        reasoning: `Local/file keywords: ${localScore}`,
      };
    }

    return {
      agent: 'coding',
      confidence: codingScore / total,
      reasoning: `Coding keywords: ${codingScore}`,
    };
  }

  private async processWithVoice(request: OrchestratorRequest): Promise<OrchestratorResponse> {
    if (!this.voiceAgent) {
      throw new Error('Voice agent not initialized');
    }

    // For text input, send to existing voice session
    if (typeof request.input === 'string') {
      if (!this.voiceAgent.isConnected()) {
        await this.voiceAgent.connect(request.context);
      }
      this.voiceAgent.sendText(request.input);
    }

    // Voice responses are handled via callbacks, return placeholder
    return {
      agentUsed: 'voice',
      message: {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '', // Will be filled via onmessage callback
        timestamp: Date.now(),
        agentType: 'voice',
      },
    };
  }

  private async processWithCoding(request: OrchestratorRequest): Promise<OrchestratorResponse> {
    if (!this.codingAgent) {
      throw new Error('Coding agent not initialized');
    }

    const prompt = typeof request.input === 'string' 
      ? request.input 
      : 'Please transcribe and respond to this audio.';

    const response = await this.codingAgent.generate({
      prompt,
      context: request.context,
    });

    // Handle tool calls
    let finalText = response.text;
    let allArtifacts = response.artifacts ?? [];

    if (response.toolCalls && this.toolExecutor) {
      // Execute tool calls and potentially re-query with results
      await this.executeToolCalls(response.toolCalls);
    }

    return {
      agentUsed: 'coding',
      message: {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: finalText,
        timestamp: Date.now(),
        agentType: 'coding',
        toolCalls: response.toolCalls,
        artifacts: allArtifacts.length > 0 ? allArtifacts : undefined,
        thinking: response.thinking,
      },
    };
  }

  private async processWithLocal(request: OrchestratorRequest): Promise<OrchestratorResponse> {
    if (!this.localAgent) {
      throw new Error('Local agent not initialized');
    }

    const prompt = typeof request.input === 'string'
      ? request.input
      : 'Please respond to this request.';

    // Check if this is a complex query that should be proxied to Gemini
    const isComplex = this.isComplexQuery(prompt);
    
    let text: string;
    let toolCalls: ToolCall[] | undefined;
    let artifacts: CodeArtifact[] | undefined;

    if (isComplex && this.localAgent.getCapabilities().geminiProxy) {
      // Proxy to Gemini for complex queries
      text = await this.localAgent.proxyToGemini(prompt, request.context);
    } else {
      // Use local LLM
      const response = await this.localAgent.generate(prompt, request.context);
      text = response.text;
      toolCalls = response.toolCalls;
      artifacts = response.artifacts;
    }

    // Handle tool calls
    if (toolCalls && this.toolExecutor) {
      await this.executeToolCalls(toolCalls);
    }

    return {
      agentUsed: 'local',
      message: {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: text,
        timestamp: Date.now(),
        agentType: 'local',
        toolCalls,
        artifacts,
      },
    };
  }

  private isComplexQuery(prompt: string): boolean {
    const complexIndicators = [
      'explain in detail',
      'analyze',
      'compare',
      'implement a complete',
      'design',
      'architecture',
      'multiple files',
      'full implementation',
    ];

    const lower = prompt.toLowerCase();
    return complexIndicators.some(indicator => lower.includes(indicator));
  }

  private async executeToolCalls(calls: ToolCall[]): Promise<ToolResult[]> {
    if (!this.toolExecutor) {
      return calls.map(call => ({
        toolCallId: call.id,
        result: null,
        error: 'No tool executor configured',
      }));
    }

    const results: ToolResult[] = [];
    
    for (const call of calls) {
      try {
        const result = await this.toolExecutor(call);
        results.push(result);
        this.emit({ type: 'tool_result', agent: 'coding', result });
      } catch (error) {
        results.push({
          toolCallId: call.id,
          result: null,
          error: String(error),
        });
      }
    }

    return results;
  }
}

// ============================================================================
// Context Builder (replaces system-prompt-builder.ts)
// ============================================================================

export function buildAgentContext(
  workspaceStore: unknown,
  reactFlowInstance: unknown,
  additionalContext?: string
): AgentContext {
  // Extract workspace state
  const ws = workspaceStore as {
    currentSessionId?: string | null;
    containers?: Array<{ id: string; name: string; rootId: string; containerType?: string }>;
    selectedNodeId?: string | null;
    breadcrumb?: Array<{ id: string; label: string }>;
  } | null;

  const workspaceState = {
    currentSessionId: ws?.currentSessionId ?? null,
    containers: ws?.containers ?? [],
    selectedNodeId: ws?.selectedNodeId ?? null,
    breadcrumb: ws?.breadcrumb ?? [],
  };

  // Extract canvas state from ReactFlow
  const rf = reactFlowInstance as {
    getNodes?: () => Array<{ id: string; type?: string; data?: { label?: string }; position: { x: number; y: number } }>;
    getEdges?: () => Array<{ id: string; source: string; target: string; type?: string }>;
    getViewport?: () => { x: number; y: number; zoom: number };
  } | null;

  const nodes = rf?.getNodes?.() ?? [];
  const edges = rf?.getEdges?.() ?? [];
  const viewport = rf?.getViewport?.() ?? { x: 0, y: 0, zoom: 1 };

  const canvasState = {
    nodes: nodes.map(n => ({
      id: n.id,
      type: n.type ?? 'default',
      label: n.data?.label ?? n.id,
      position: n.position,
      data: n.data ?? {},
    })),
    edges: edges.map(e => ({
      id: e.id,
      source: e.source,
      target: e.target,
      type: e.type,
    })),
    viewport,
  };

  return {
    workspaceState,
    canvasState,
    messages: [],
    systemContext: additionalContext ?? '',
  };
}

// ============================================================================
// Factory Function
// ============================================================================

export function createOrchestrator(
  apiKey: string,
  config?: Partial<OrchestratorConfig>
): AgentOrchestrator {
  return new AgentOrchestrator(apiKey, config);
}
