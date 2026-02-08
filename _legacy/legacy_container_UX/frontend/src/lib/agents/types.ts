/**
 * Tri-Agent Architecture Type Definitions
 * 
 * Voice Agent: Gemini 2.5 Live API with Charon voice for bidirectional speech
 * Coding Agent: Gemini 3 Pro with thinking for complex reasoning
 * Local Agent: WebLLM Qwen2.5-Coder with file system access
 */

// ============================================================================
// Core Agent Interfaces
// ============================================================================

export type AgentType = 'voice' | 'coding' | 'local';

export interface AgentMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: number;
  agentType?: AgentType;
  toolCalls?: ToolCall[];
  toolResults?: ToolResult[];
  artifacts?: CodeArtifact[];
  thinking?: string; // Gemini 3 thought process
}

export interface AgentContext {
  /** Current workspace/session state from Zustand */
  workspaceState: WorkspaceSnapshot;
  /** ReactFlow canvas state */
  canvasState: CanvasSnapshot;
  /** Conversation history */
  messages: AgentMessage[];
  /** System prompt additions */
  systemContext: string;
}

export interface WorkspaceSnapshot {
  currentSessionId: string | null;
  containers: { id: string; name: string; rootId: string; containerType?: string }[];
  selectedNodeId: string | null;
  breadcrumb: { id: string; label: string }[];
}

export interface CanvasSnapshot {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  viewport: { x: number; y: number; zoom: number };
}

export interface CanvasNode {
  id: string;
  type: string;
  label: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
}

// ============================================================================
// Voice Agent Types (Gemini 2.5 Live API)
// ============================================================================

export interface VoiceAgentConfig {
  model: 'gemini-live-2.5-flash-preview';
  voice: PrebuiltVoice;
  responseModalities: Modality[];
  systemInstruction?: string;
  tools?: FunctionDeclaration[];
}

export type PrebuiltVoice = 
  | 'Charon'    // Informative (selected)
  | 'Kore'      // Firm
  | 'Fenrir'    // Excitable
  | 'Aoede'     // Breezy
  | 'Puck'      // Upbeat
  | 'Zephyr'    // Bright;

export type Modality = 'TEXT' | 'AUDIO' | 'IMAGE';

export interface LiveSession {
  /** Send text message */
  sendClientContent(params: LiveClientContentParams): void;
  /** Send real-time audio input */
  sendRealtimeInput(params: LiveRealtimeInputParams): void;
  /** Send tool response */
  sendToolResponse(params: LiveToolResponseParams): void;
  /** Close the session */
  close(): void;
}

export interface LiveClientContentParams {
  turns?: ContentTurn[];
  turnComplete?: boolean;
}

export interface LiveRealtimeInputParams {
  audio?: Blob;
  text?: string;
  audioStreamEnd?: boolean;
}

export interface LiveToolResponseParams {
  functionResponses: FunctionResponse[];
}

export interface ContentTurn {
  role: 'user' | 'model';
  parts: ContentPart[];
}

export interface ContentPart {
  text?: string;
  inlineData?: { data: string; mimeType: string };
}

export interface LiveServerMessage {
  serverContent?: {
    modelTurn?: {
      parts?: Array<{
        text?: string;
        inlineData?: { data: string; mimeType: string };
        functionCall?: FunctionCall;
      }>;
    };
    turnComplete?: boolean;
  };
  toolCall?: {
    functionCalls?: FunctionCall[];
  };
  toolCallCancellation?: {
    ids?: string[];
  };
}

export interface LiveCallbacks {
  onopen?: () => void;
  onmessage: (message: LiveServerMessage) => void;
  onerror?: (error: ErrorEvent) => void;
  onclose?: (event: CloseEvent) => void;
}

// ============================================================================
// Coding Agent Types (Gemini 3 Pro)
// ============================================================================

export interface CodingAgentConfig {
  model: 'gemini-3-pro-preview';
  thinkingConfig: ThinkingConfig;
  temperature: number;
  tools?: FunctionDeclaration[];
}

export interface ThinkingConfig {
  /** Token budget for thinking (max 24576) */
  thinkingBudget: number;
}

export interface CodingRequest {
  prompt: string;
  context: AgentContext;
  artifacts?: CodeArtifact[];
}

export interface CodingResponse {
  text: string;
  thinking?: string;
  artifacts?: CodeArtifact[];
  toolCalls?: ToolCall[];
  usage?: TokenUsage;
}

export interface CodeArtifact {
  id: string;
  type: 'code' | 'file' | 'diff';
  language: string;
  filename?: string;
  content: string;
  /** For diffs: original content */
  original?: string;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  thinkingTokens?: number;
  totalTokens: number;
}

// ============================================================================
// Local Agent Types (WebLLM)
// ============================================================================

export interface LocalAgentConfig {
  model: 'Qwen2.5-Coder-7B-Instruct-q4f16_1-MLC';
  contextWindowSize: number;
  temperature: number;
  tools?: FunctionDeclaration[];
}

export interface LocalAgentCapabilities {
  /** File System Access API available */
  fileSystem: boolean;
  /** WebGPU available for inference */
  webGPU: boolean;
  /** Can proxy complex queries to Gemini */
  geminiProxy: boolean;
}

export interface FileSystemHandle {
  kind: 'file' | 'directory';
  name: string;
}

export interface FileOperationResult {
  success: boolean;
  path?: string;
  content?: string;
  error?: string;
}

// ============================================================================
// Tool/Function Calling Types (Compatible with @google/genai SDK)
// ============================================================================

/**
 * Schema type enum matching @google/genai Type enum
 * These string values match the SDK's Type enum for compatibility
 */
export type SchemaType = 
  | 'STRING'
  | 'NUMBER' 
  | 'INTEGER'
  | 'BOOLEAN'
  | 'ARRAY'
  | 'OBJECT';

export interface ParameterSchema {
  type: SchemaType;
  description?: string;
  enum?: string[];
  items?: ParameterSchema;
  properties?: Record<string, ParameterSchema>;
  required?: string[];
  nullable?: boolean;
}

export interface FunctionDeclaration {
  name: string;
  description: string;
  parameters?: ParameterSchema;
}

export interface FunctionCall {
  id?: string;
  name: string;
  args: Record<string, unknown>;
}

export interface FunctionResponse {
  id?: string;
  name: string;
  response: unknown;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string; // JSON string
  };
}

export interface ToolResult {
  toolCallId: string;
  result: unknown;
  error?: string;
}

// ============================================================================
// Orchestrator Types
// ============================================================================

export interface OrchestratorConfig {
  /** Default agent for text queries */
  defaultAgent: AgentType;
  /** Enable automatic agent routing */
  autoRoute: boolean;
  /** Fallback behavior on error */
  errorStrategy: 'manual' | 'fallback';
}

export interface TaskClassification {
  agent: AgentType;
  confidence: number;
  reasoning: string;
}

export interface OrchestratorRequest {
  input: string | AudioInput;
  context: AgentContext;
  preferredAgent?: AgentType;
}

export interface AudioInput {
  type: 'audio';
  data: ArrayBuffer;
  sampleRate: number;
  channels: number;
}

export interface OrchestratorResponse {
  agentUsed: AgentType;
  message: AgentMessage;
  audioOutput?: ArrayBuffer;
}

// ============================================================================
// Event Types
// ============================================================================

export type AgentEvent = 
  | { type: 'connecting'; agent: AgentType }
  | { type: 'connected'; agent: AgentType }
  | { type: 'disconnected'; agent: AgentType; reason?: string }
  | { type: 'error'; agent: AgentType; error: Error }
  | { type: 'thinking'; agent: AgentType }
  | { type: 'speaking'; agent: AgentType }
  | { type: 'listening'; agent: AgentType }
  | { type: 'tool_call'; agent: AgentType; call: ToolCall }
  | { type: 'tool_result'; agent: AgentType; result: ToolResult }
  | { type: 'artifact'; agent: AgentType; artifact: CodeArtifact }
  | { type: 'model_loading'; agent: 'local'; progress: number; text: string };

export type AgentEventHandler = (event: AgentEvent) => void;

// ============================================================================
// Error Types
// ============================================================================

export class AgentError extends Error {
  constructor(
    message: string,
    public agent: AgentType,
    public code: AgentErrorCode,
    public recoverable: boolean = false
  ) {
    super(message);
    this.name = 'AgentError';
  }
}

export type AgentErrorCode = 
  | 'CONNECTION_FAILED'
  | 'API_KEY_MISSING'
  | 'QUOTA_EXCEEDED'
  | 'MODEL_NOT_AVAILABLE'
  | 'WEBGPU_NOT_SUPPORTED'
  | 'FILE_PERMISSION_DENIED'
  | 'TOOL_EXECUTION_FAILED'
  | 'AUDIO_NOT_SUPPORTED'
  | 'SESSION_EXPIRED';
