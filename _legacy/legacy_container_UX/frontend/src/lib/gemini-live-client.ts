/**
 * Gemini Live API Client
 * Real-time bidirectional voice + visual interaction
 *
 * Model: gemini-3-pro-preview (1M context, thinking levels)
 * Voice: Web Speech API (browser native)
 * Bridge: Collider Bridge for Copilot ↔ Host communication
 */

/* eslint-disable no-console, @typescript-eslint/no-explicit-any */
// Console logging is intentional for voice/streaming debugging
// Any types are needed for Web Speech API and dynamic tool structures

import { GoogleGenAI } from '@google/genai';
import type { Edge, Node } from '@xyflow/react';
import { SystemPromptBuilder } from './system-prompt-builder';
import { LocalIntelligence } from './local-intelligence';

// Gemini 3 Pro configuration
const GEMINI_MODEL = 'gemini-3-pro-preview'; // Gemini 3 Pro with extended thinking
const GEMINI_THINKING_BUDGET = 24576; // Max tokens for thinking
const GEMINI_TEMPERATURE = 1.0; // Required for Gemini 3

export interface LiveSessionConfig {
  apiKey: string;
  mode?: 'cloud' | 'local'; // Default to 'cloud'
  model?: string;
  systemInstruction?: string;
  tools?: unknown[];
  thinkingLevel?: 'low' | 'high'; // Gemini 3: 'low' for speed, 'high' for reasoning
  generationConfig?: {
    temperature?: number;
    topP?: number;
    topK?: number;
    maxOutputTokens?: number;
    responseMimeType?: string;
  };
  voiceConfig?: {
    rate?: number;
    pitch?: number;
    lang?: string;
  };
}

export interface VisualContext {
  nodes: Node[];
  edges: Edge[];
  selectedNodes: string[];
  activeSession: string | null;
  viewport: { x: number; y: number; zoom: number };
  timestamp: number;
  // Global context (L0 awareness)
  globalSessions?: { id: string; title: string }[];
  // Navigation breadcrumbs for level-aware context
  breadcrumbs?: { id: string; title?: string; label?: string; type?: string }[];
}

export type VoiceStatus = 'idle' | 'listening' | 'processing' | 'speaking' | 'error' | 'downloading';

type LocalToolCall = {
  id: string;
  type?: string;
  function: {
    name: string;
    arguments: string;
  };
};

export class GeminiLiveSession {
  private ai: GoogleGenAI | null = null;
  private chatHistory: Array<{ role: 'user' | 'model'; parts: any[] }> = [];
  
  // Local Intelligence
  private localAgent: LocalIntelligence | null = null;
  private localHistory: any[] = [];
  private lastContext: any = {};

  private isConnected = false;
  private statusCallback?: (status: VoiceStatus) => void;
  private transcriptCallback?: (text: string, isFinal: boolean) => void;
  private responseCallback?: (text: string) => void;
  private toolCallCallback?: (name: string, args: any) => Promise<any>;
  private audioContext: AudioContext | null = null;
  private recognition: any = null; // SpeechRecognition API
  private isMuted: boolean = false;

  constructor(private config: LiveSessionConfig) {}

  /**
   * Initialize Live API connection with audio streaming
   */
  async connect(
    onStatusChange?: (status: VoiceStatus) => void,
    onTranscript?: (text: string, isFinal: boolean) => void,
    onToolCall?: (name: string, args: any) => Promise<any>,
    onResponse?: (text: string) => void
  ): Promise<void> {
    this.statusCallback = onStatusChange;
    this.transcriptCallback = onTranscript;
    this.toolCallCallback = onToolCall;
    this.responseCallback = onResponse;

    try {
      this.updateStatus('processing');

      if (this.config.mode === 'local') {
        // Initialize Local Agent
        this.updateStatus('downloading');
        this.localAgent = new LocalIntelligence({
          modelId: this.config.model, // Optional override
          systemInstruction: this.config.systemInstruction || this.getDefaultSystemInstruction(),
        });
        
        await this.localAgent.init((progress) => {
          console.log(`[Local Model] ${progress.text}`);
        });
        
        this.localHistory = []; // Reset history
        
      } else {
        // Initialize Cloud Agent (Gemini 3 Pro with new SDK)
        this.ai = new GoogleGenAI({ apiKey: this.config.apiKey });

        // Create tools array
        const rawTools = this.config.tools || GeminiLiveSession.getDefaultTools();
        
        // DEBUG: Check tools structure
        console.log('[GeminiLive] Using Gemini 3 Pro with extended thinking');
        console.log('[GeminiLive] Raw tools count:', rawTools.length);

        // Reset chat history for new session
        this.chatHistory = [];
      }

      // Set up Web Speech API for voice recognition
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onresult = (event: any) => {
          const last = event.results.length - 1;
          const transcript = event.results[last][0].transcript;
          const isFinal = event.results[last].isFinal;

          if (this.transcriptCallback) {
            this.transcriptCallback(transcript, isFinal);
          }

          // Process final transcripts
          if (isFinal) {
            this.processVoiceCommand(transcript);
          }
        };

        this.recognition.onerror = (event: any) => {
          // no-speech is common and expected - don't treat as error
          if (event.error === 'no-speech') {
            console.log('Speech recognition: no speech detected, restarting...');
            // Restart listening if still in voice mode
            if (this.isConnected && this.recognition) {
              try {
                this.recognition.start();
              } catch {
                // May already be started
              }
            }
            return;
          }
          // aborted is also common when switching modes
          if (event.error === 'aborted') {
            console.log('Speech recognition: aborted');
            return;
          }
          console.error('Speech recognition error:', event.error);
          this.updateStatus('error');
        };

        this.recognition.start();
      }

      // Set up audio output context
      this.audioContext = new AudioContext();

      this.isConnected = true;
      this.updateStatus('listening');
    } catch (error) {
      console.error('Failed to connect to AI Service:', error);
      this.updateStatus('error');
      throw error;
    }
  }

  /**
   * Process voice command with AI
   */
  private async processVoiceCommand(text: string): Promise<void> {
    if (!this.isConnected) return;

    try {
      this.updateStatus('processing');

      if (this.config.mode === 'local' && this.localAgent) {
        await this.processLocalCommand(text);
      } else if (this.ai) {
        await this.processCloudCommand(text);
      }

      this.updateStatus('listening');
    } catch (error) {
      console.error('Error processing voice command:', error);
      this.updateStatus('error');
    }
  }

  private async processLocalCommand(text: string): Promise<void> {
    if (!this.localAgent) return;

    const tools = this.config.tools || GeminiLiveSession.getDefaultTools();
    // Unwrap if needed
    const rawTools = (tools.length > 0 && (tools[0] as any).functionDeclarations) 
      ? (tools[0] as any).functionDeclarations 
      : tools;

    // Send message
    const result = await this.localAgent.sendMessage(
      text, 
      this.localHistory, 
      rawTools,
      this.config.systemInstruction || this.getDefaultSystemInstruction()
    );

    // Add user message to history
    this.localHistory.push({ role: 'user', content: text });

    // Handle tool calls
    const toolCalls = result.toolCalls as LocalToolCall[] | undefined;

    if (toolCalls && toolCalls.length > 0) {
      // Add assistant message with tool calls to history
      this.localHistory.push({ 
        role: 'assistant', 
        content: result.text || null,
        tool_calls: toolCalls 
      });

      for (const call of toolCalls) {
        if (this.toolCallCallback) {
          try {
            const args = JSON.parse(call.function.arguments);
            const toolResult = await this.toolCallCallback(call.function.name, args);
            
            // Add tool result to history
            this.localHistory.push({
              role: 'tool',
              tool_call_id: call.id,
              content: JSON.stringify(toolResult)
            });
          } catch (err) {
            console.error(`Tool execution failed for ${call.function.name}:`, err);
            this.localHistory.push({
              role: 'tool',
              tool_call_id: call.id,
              content: JSON.stringify({ error: String(err) })
            });
          }
        }
      }

      // Follow up with model to get final response
      const followUp = await this.localAgent.sendMessage(
        "", // Empty prompt for follow-up
        this.localHistory,
        rawTools
      );
      
      const responseText = followUp.text;
      this.localHistory.push({ role: 'assistant', content: responseText });
      
      if (this.responseCallback) this.responseCallback(responseText);
      this.speak(responseText);

    } else {
      // Just text response
      const responseText = result.text;
      this.localHistory.push({ role: 'assistant', content: responseText });
      
      if (this.responseCallback) this.responseCallback(responseText);
      this.speak(responseText);
    }
  }

  private async processCloudCommand(text: string): Promise<void> {
    if (!this.ai) {
      console.error('AI not initialized');
      return;
    }

    // Build tools for function calling
    const rawTools = this.config.tools || GeminiLiveSession.getDefaultTools();
    const toolDeclarations = Array.isArray(rawTools) && rawTools.length > 0 && !(rawTools[0] as any).functionDeclarations
      ? rawTools
      : (rawTools[0] as any)?.functionDeclarations || [];

    // Add user message to history
    this.chatHistory.push({
      role: 'user',
      parts: [{ text }],
    });

    // Build system instruction
    const systemInstruction = this.config.systemInstruction || SystemPromptBuilder.build(this.lastContext);

    // Generate response using Gemini 3 Pro with thinking
    let response = await this.ai.models.generateContent({
      model: this.config.model || GEMINI_MODEL,
      contents: this.chatHistory,
      config: {
        temperature: GEMINI_TEMPERATURE,
        systemInstruction: systemInstruction ? { parts: [{ text: systemInstruction }] } : undefined,
        thinkingConfig: {
          thinkingBudget: this.config.thinkingLevel === 'low' ? 8192 : GEMINI_THINKING_BUDGET,
        },
        tools: toolDeclarations.length > 0 ? [{ functionDeclarations: toolDeclarations }] : undefined,
      },
    });

    // Handle tool calls loop
    let maxIterations = 10; // Prevent infinite loops
    while (maxIterations-- > 0) {
      const candidate = (response as any).candidates?.[0];
      const parts = candidate?.content?.parts || [];
      
      // Check for function calls
      const functionCalls = parts.filter((p: any) => p.functionCall);
      
      if (functionCalls.length === 0) {
        // No tool calls, extract text and speak
        const textParts = parts.filter((p: any) => p.text);
        const responseText = textParts.map((p: any) => p.text).join('');
        
        // Extract thinking if present
        const thinkingParts = parts.filter((p: any) => p.thought);
        if (thinkingParts.length > 0) {
          console.log('[Gemini 3] Thinking:', thinkingParts.map((p: any) => p.thought).join(''));
        }
        
        // Add model response to history preserving thoughtSignature (recommended for quality)
        // The signature is on the last part for non-function-call responses
        const lastPart = parts[parts.length - 1];
        const historyParts: any[] = [{ text: responseText }];
        if (lastPart?.thoughtSignature) {
          historyParts[0].thoughtSignature = lastPart.thoughtSignature;
        }
        this.chatHistory.push({
          role: 'model',
          parts: historyParts,
        });
        
        if (this.responseCallback) {
          this.responseCallback(responseText);
        }
        
        this.speak(responseText);
        break;
      }

      // Execute all tool calls
      const toolResponses = [];
      for (const part of functionCalls) {
        const call = part.functionCall;
        if (this.toolCallCallback) {
          try {
            const toolResult = await this.toolCallCallback(call.name, call.args);
            toolResponses.push({
              name: call.name,
              response: { result: toolResult },
            });
          } catch (err) {
            console.error(`Tool execution failed for ${call.name}:`, err);
            toolResponses.push({
              name: call.name,
              response: { error: String(err) },
            });
          }
        }
      }

      // Add function calls and responses to history
      // Gemini 3 Pro requires thoughtSignature to be preserved in history for function calls
      this.chatHistory.push({
        role: 'model',
        parts: functionCalls.map((p: any, idx: number) => {
          const part: any = { functionCall: p.functionCall };
          // First function call in sequential/parallel calls has the signature
          if (idx === 0 && p.thoughtSignature) {
            part.thoughtSignature = p.thoughtSignature;
          }
          return part;
        }),
      });

      this.chatHistory.push({
        role: 'user',
        parts: toolResponses.map((r) => ({
          functionResponse: r,
        })),
      });

      // Continue the conversation with tool results
      response = await this.ai.models.generateContent({
        model: this.config.model || GEMINI_MODEL,
        contents: this.chatHistory,
        config: {
          temperature: GEMINI_TEMPERATURE,
          systemInstruction: systemInstruction ? { parts: [{ text: systemInstruction }] } : undefined,
          thinkingConfig: {
            thinkingBudget: GEMINI_THINKING_BUDGET,
          },
          tools: toolDeclarations.length > 0 ? [{ functionDeclarations: toolDeclarations }] : undefined,
        },
      });
    }
  }

  /**
   * Stream visual context to AI in real-time
   */
  async streamVisualContext(context: VisualContext): Promise<void> {
    if (!this.isConnected || !this.ai) {
      console.warn('Live session not connected');
      return;
    }

    this.lastContext = context;
    // Use the builder to get the visual context string
    // We can't access the private method directly, so we'll rely on the builder's public interface
    // For now, we'll just store the context and let the next message pick it up
    // or if we want to send it immediately:
    
    // const contextDescription = SystemPromptBuilder.build(context); 
    // But that builds the WHOLE prompt. We just want the visual part for updates.
    // The SystemPromptBuilder doesn't expose just the visual part publicly yet.
    // Let's just update the lastContext and let the next interaction use it, 
    // or send a simplified update.
    
    // For this specific client, we might want to keep a local version of visual context builder
    // OR update SystemPromptBuilder to expose it.
    // Let's stick to the existing pattern but use the builder for the initial system prompt.
    
    const contextDescription = this.buildVisualContextDescription(context);

    // Context is sent with next command
    // Store for later use
    (this as any)._lastContext = contextDescription;
  }

  /**
   * Send voice command or text message
   */
  async sendMessage(text: string): Promise<void> {
    if (!this.isConnected || !this.ai) {
      throw new Error('Not connected to Gemini 3');
    }

    this.updateStatus('processing');
    await this.processVoiceCommand(text);
  }

  /**
   * Speak text using Web Speech API
   */
  private speak(text: string): void {
    if (!('speechSynthesis' in window)) {
      console.warn('Speech synthesis not supported');
      return;
    }

    // Skip speaking if muted
    if (this.isMuted) {
      console.log('Audio muted, skipping speech:', text);
      return;
    }

    // STOP LISTENING TO PREVENT SELF-HEARING
    if (this.recognition) {
      console.log('🛑 Pausing recognition while speaking...');
      this.recognition.stop();
    }

    this.updateStatus('speaking');

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = this.config.voiceConfig?.rate || 1.1;
    utterance.pitch = this.config.voiceConfig?.pitch || 1.0;
    utterance.lang = this.config.voiceConfig?.lang || 'en-US';

    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      console.log('[GeminiLive] Available voices:', voices.map(v => `${v.name} (${v.lang})`));
      
      // Prefer female US/UK English voices for clearer speech
      const preferredVoice =
        voices.find((v) => v.name.includes('Microsoft Zira') && v.lang === 'en-US') ||  // Windows female US
        voices.find((v) => v.name.includes('Microsoft Jenny') && v.lang === 'en-US') || // Windows 11 female US
        voices.find((v) => v.name.includes('Google US English') && v.name.includes('Female')) ||
        voices.find((v) => v.name.includes('Samantha') && v.lang.startsWith('en')) ||   // macOS female
        voices.find((v) => v.name.includes('Google UK English Female')) ||
        voices.find((v) => v.lang === 'en-US' && v.name.toLowerCase().includes('female')) ||
        voices.find((v) => v.lang === 'en-GB' && v.name.toLowerCase().includes('female')) ||
        voices.find((v) => v.lang === 'en-US') ||
        voices.find((v) => v.lang === 'en-GB') ||
        voices.find((v) => v.lang.startsWith('en'));

      if (preferredVoice) {
        console.log('[GeminiLive] Selected voice:', preferredVoice.name, preferredVoice.lang);
        utterance.voice = preferredVoice;
      } else {
        console.warn('[GeminiLive] No English voice found, using default:', voices[0]?.name);
      }
    };

    // Load voices if not ready
    if (window.speechSynthesis.getVoices().length === 0) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    } else {
      loadVoices();
    }

    utterance.onend = () => {
      console.log('✅ Speech ended, resuming recognition...');
      this.updateStatus('listening');
      // RESUME LISTENING
      if (this.recognition) {
        try {
          // Small delay to ensure audio channel is clear
          setTimeout(() => {
             try {
               this.recognition.start();
               console.log('🎤 Recognition resumed');
             } catch {
               console.log('Recognition already active or blocked');
             }
          }, 100);
        } catch {
          // Ignore if already started
          console.log('Recognition already active');
        }
      }
    };

    utterance.onerror = (e) => {
      console.error('Speech error:', e);
      this.updateStatus('error');
      // Ensure we resume even on error
      if (this.recognition) {
        try {
          this.recognition.start();
        } catch { /* ignore */ }
      }
    };

    window.speechSynthesis.speak(utterance);
  }

  /**
   * Disconnect and cleanup
   */
  async disconnect(): Promise<void> {
    if (this.recognition) {
      this.recognition.stop();
      this.recognition = null;
    }

    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }

    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }

    this.isConnected = false;
    this.updateStatus('idle');
  }

  /**
   * Build visual context description for AI
   */
  private buildVisualContextDescription(context: VisualContext): string {
    // Defensive null checks - context properties may be undefined during initialization
    const nodes = context?.nodes ?? [];
    const edges = context?.edges ?? [];
    const selectedNodes = context?.selectedNodes ?? [];
    const activeSession = context?.activeSession ?? null;
    const viewport = context?.viewport ?? { x: 0, y: 0, zoom: 1 };
    const globalSessions = context?.globalSessions ?? [];

    const nodeDescriptions = nodes
      .map((n) => {
        const selected = selectedNodes.includes(n.id) ? '(SELECTED)' : '';
        return `- ${n.data?.label || n.type} at (${Math.round(n.position.x)}, ${Math.round(
          n.position.y
        )}) ${selected}`;
      })
      .join('\n');

    const connectionDescriptions = edges
      .map((e) => {
        const source = nodes.find((n) => n.id === e.source)?.data?.label || e.source;
        const target = nodes.find((n) => n.id === e.target)?.data?.label || e.target;
        return `- ${source} → ${target}`;
      })
      .join('\n');

    const globalContext = globalSessions 
      ? `\nGlobal Sessions (L0 Awareness): ${globalSessions.map(s => s.title).join(', ')}`
      : '';

    return `
VISUAL CONTEXT UPDATE:
Session: ${activeSession || 'None'}
Viewport: x=${Math.round(viewport.x)}, y=${Math.round(viewport.y)}, zoom=${viewport.zoom.toFixed(2)}
Selected: ${selectedNodes.length} node(s)
${globalContext}

Nodes (${nodes.length} total):
${nodeDescriptions}

Connections (${edges.length} total):
${connectionDescriptions}

Time: ${new Date(context.timestamp).toLocaleTimeString()}
`.trim();
  }

  /**
   * Default system instruction for visual workspace control
   */
  private getDefaultSystemInstruction(): string {
    return SystemPromptBuilder.build(this.lastContext);
  }

  /**
   * Default tool definitions for visual control
   */
  public static getDefaultTools(): unknown[] {
    return [
      // =======================================================================
      // BRIDGE TOOLS (Copilot ↔ Host communication)
      // =======================================================================
      {
        name: 'write_report',
        description: 'Write a report to the Collider Bridge outbox for Copilot to read. Use this to share findings, test results, or state snapshots with external tools.',
        parameters: {
          type: 'object',
          properties: {
            report_type: { 
              type: 'string', 
              enum: ['test_result', 'state_snapshot', 'finding', 'suggestion'],
              description: 'Type of report' 
            },
            title: { type: 'string', description: 'Report title' },
            content: { type: 'string', description: 'Report content (markdown supported)' },
            data: { type: 'object', description: 'Structured data to include' },
          },
          required: ['report_type', 'title'],
        },
      },
      {
        name: 'read_bridge_inbox',
        description: 'Read any pending commands from the Collider Bridge inbox. Returns commands queued by Copilot.',
        parameters: {
          type: 'object',
          properties: {},
        },
      },
      // =======================================================================
      // SESSION & WORKSPACE TOOLS
      // =======================================================================
      {
        name: 'create_session',
        description: 'Create a new Session (Sticky Note) on the L0 canvas.',
        parameters: {
          type: 'object',
          properties: {
            title: { type: 'string', description: 'Session title/name' },
            position_x: { type: 'number', description: 'X coordinate for session' },
            position_y: { type: 'number', description: 'Y coordinate for session' },
            theme_color: { type: 'string', description: 'Hex color for session theme' },
          },
        },
      },
      {
        name: 'list_sessions',
        description: 'List all available Sessions (Sticky Notes) with their positions and status.',
        parameters: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'query_sessions',
        description: 'SEMANTIC SEARCH: Find sessions by meaning, color, tags, or shared status. Use this when the user asks for "finance stuff" or "red notes".',
        parameters: {
          type: 'object',
          properties: {
            color: { type: 'string', description: 'Filter by theme color (e.g., "red", "#ff0000")' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Filter by tags' },
            is_shared: { type: 'boolean', description: 'Filter by shared status' },
            search_term: { type: 'string', description: 'Semantic search term (e.g., "finance", "urgent")' }
          },
        },
      },
      {
        name: 'get_user_session',
        description: 'Get details of the current UserSession (Root L0 Container). Returns user info, permissions, and root resources.',
        parameters: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'observe_canvas',
        description:
          'See current visual state of the UserSessionSpace - selected Sticky Notes (Containers), viewport zoom, and topology. Use this to understand the visual graph.',
        parameters: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'switch_session',
        description: 'Dive into a different Session (Sticky Note) by ID or title.',
        parameters: {
          type: 'object',
          properties: {
            session_id: { type: 'string', description: 'Session ID to switch to' },
            session_title: { type: 'string', description: 'Session title to search for' },
          },
        },
      },
      {
        name: 'delete_session',
        description: 'Delete a Session (Sticky Note) by ID.',
        parameters: {
          type: 'object',
          properties: {
            session_id: { type: 'string', description: 'Session ID to delete' },
            confirm: { type: 'boolean', description: 'Confirmation required' },
          },
          required: ['session_id'],
        },
      },
      {
        name: 'move_nodes',
        description: 'Move selected Sticky Notes (Containers) to a new position.',
        parameters: {
          type: 'object',
          properties: {
            node_ids: {
              type: 'array',
              items: { type: 'string' },
              description: 'IDs of Sticky Notes to move',
            },
            delta_x: { type: 'number', description: 'Horizontal movement in pixels' },
            delta_y: { type: 'number', description: 'Vertical movement in pixels' },
            animate: { type: 'boolean', description: 'Use smooth animation' },
          },
          required: ['node_ids', 'delta_x', 'delta_y'],
        },
      },
      {
        name: 'select_nodes',
        description: 'Select Sticky Notes (Containers) by ID, type, or label pattern.',
        parameters: {
          type: 'object',
          properties: {
            node_ids: {
              type: 'array',
              items: { type: 'string' },
              description: 'Specific Sticky Note IDs',
            },
            type: { type: 'string', description: 'Container type (session/agent/tool/source)' },
            label_pattern: { type: 'string', description: 'Regex pattern to match labels' },
            clear_existing: { type: 'boolean', description: 'Clear current selection first' },
          },
        },
      },
      {
        name: 'apply_layout',
        description: 'Auto-arrange Sticky Notes using layout algorithm.',
        parameters: {
          type: 'object',
          properties: {
            algorithm: {
              type: 'string',
              enum: ['force', 'circular', 'tree', 'grid'],
              description: 'Layout algorithm',
            },
            node_ids: {
              type: 'array',
              items: { type: 'string' },
              description: 'Nodes to layout (empty = all)',
            },
            spacing: { type: 'number', description: 'Space between nodes in pixels' },
            animate: { type: 'boolean', description: 'Animate to new positions' },
          },
          required: ['algorithm'],
        },
      },
      {
        name: 'update_theme',
        description: 'Change visual theme colors and styles',
        parameters: {
          type: 'object',
          properties: {
            preset: {
              type: 'string',
              enum: ['ocean', 'forest', 'sunset', 'professional', 'dark', 'light'],
            },
            primary_color: { type: 'string', description: 'Hex color for primary elements' },
            background_color: { type: 'string', description: 'Hex color for background' },
            node_style: {
              type: 'string',
              enum: ['rounded', 'sharp', 'soft'],
              description: 'Node border style',
            },
          },
        },
      },
      {
        name: 'create_node',
        description: 'Create a new node in the workspace',
        parameters: {
          type: 'object',
          properties: {
            type: { type: 'string', enum: ['object', 'agent', 'tool'], description: 'Node type' },
            label: { type: 'string', description: 'Node label/name' },
            position_x: { type: 'number', description: 'X coordinate' },
            position_y: { type: 'number', description: 'Y coordinate' },
            connect_to: {
              type: 'array',
              items: { type: 'string' },
              description: 'Node IDs to connect to',
            },
          },
          required: ['type', 'label'],
        },
      },
      {
        name: 'delete_nodes',
        description: 'Delete nodes from workspace',
        parameters: {
          type: 'object',
          properties: {
            node_ids: {
              type: 'array',
              items: { type: 'string' },
              description: 'IDs of nodes to delete',
            },
            confirm: { type: 'boolean', description: 'Skip confirmation prompt' },
          },
          required: ['node_ids'],
        },
      },
      {
        name: 'create_custom_tool',
        description: 'Create a user-level custom tool definition that can be added to sessions.',
        parameters: {
          type: 'object',
          properties: {
            name: { type: 'string', description: 'Display name of the tool' },
            description: { type: 'string', description: 'What the tool does' },
            builtin_tool: { type: 'string', description: 'Backing builtin tool name (e.g., csv_analyzer)' },
            config: { type: 'object', description: 'Configuration payload for the tool' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Tags for discovery' },
          },
          required: ['name', 'builtin_tool'],
        },
      },
      {
        name: 'create_custom_agent',
        description: 'Create a user-level custom agent definition.',
        parameters: {
          type: 'object',
          properties: {
            name: { type: 'string', description: 'Agent name' },
            description: { type: 'string', description: 'Agent summary' },
            system_prompt: { type: 'string', description: 'System prompt for the agent' },
            model: { type: 'string', description: 'Model identifier (e.g., gpt-4o)' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Tags for discovery' },
          },
          required: ['name'],
        },
      },
      {
        name: 'add_tool_to_session',
        description: 'Attach an existing tool definition to a session.',
        parameters: {
          type: 'object',
          properties: {
            session_id: { type: 'string', description: 'Target session ID' },
            tool_name: { type: 'string', description: 'Tool definition name to attach' },
            display_name: { type: 'string', description: 'Override display title' },
            config_overrides: { type: 'object', description: 'Preset params or config overrides' },
          },
          required: ['session_id', 'tool_name'],
        },
      },
      {
        name: 'add_agent_to_session',
        description: 'Attach an existing agent definition to a session.',
        parameters: {
          type: 'object',
          properties: {
            session_id: { type: 'string', description: 'Target session ID' },
            agent_id: { type: 'string', description: 'Agent definition ID to attach' },
            display_name: { type: 'string', description: 'Override display title' },
            model_override: { type: 'string', description: 'Optional model override' },
            prompt_override: { type: 'string', description: 'Optional system prompt override' },
            active: { type: 'boolean', description: 'Mark as active agent' },
          },
          required: ['session_id', 'agent_id'],
        },
      },
      {
        name: 'browse_tools',
        description: 'List available tool definitions (optionally by category).',
        parameters: {
          type: 'object',
          properties: {
            category: { type: 'string', description: 'Filter tools by category' },
          },
        },
      },
      {
        name: 'browse_agents',
        description: 'List available agent definitions for a session (optionally search).',
        parameters: {
          type: 'object',
          properties: {
            session_id: { type: 'string', description: 'Session context for available agents' },
            search: { type: 'string', description: 'Search query for agent names or tags' },
          },
        },
      },
    ];
  }

  /**
   * Update voice status and notify callback
   */
  private updateStatus(status: VoiceStatus): void {
    if (this.statusCallback) {
      this.statusCallback(status);
    }
  }

  get connected(): boolean {
    return this.isConnected;
  }

  /**
   * Mute/unmute audio output
   */
  setMuted(muted: boolean): void {
    this.isMuted = muted;
    if (muted && window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel(); // Stop current speech
    }
  }
}
