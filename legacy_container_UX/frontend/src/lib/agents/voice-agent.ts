/**
 * Voice Agent - Gemini 2.5 Live API with Charon Voice
 * 
 * Bidirectional audio streaming for natural conversation.
 * Uses WebSocket for real-time communication with PCM audio.
 */

import { GoogleGenAI, Modality } from '@google/genai';
import type {
  VoiceAgentConfig,
  LiveSession,
  LiveServerMessage,
  FunctionDeclaration,
  FunctionCall,
  FunctionResponse,
  AgentContext,
  AgentEvent,
  AgentEventHandler,
  PrebuiltVoice,
} from './types';

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_MODEL = 'gemini-live-2.5-flash-preview';
const DEFAULT_VOICE: PrebuiltVoice = 'Charon';
const AUDIO_SAMPLE_RATE_INPUT = 16000;  // 16kHz mono PCM input
const AUDIO_SAMPLE_RATE_OUTPUT = 24000; // 24kHz output from Gemini

// ============================================================================
// Voice Agent Class
// ============================================================================

export class VoiceAgent {
  private ai: GoogleGenAI | null = null;
  private session: LiveSession | null = null;
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private audioWorklet: AudioWorkletNode | null = null;
  private eventHandler: AgentEventHandler | null = null;
  
  // Audio playback queue
  private audioQueue: Float32Array[] = [];
  private isPlaying = false;
  private nextPlayTime = 0;

  private config: VoiceAgentConfig;
  private tools: FunctionDeclaration[] = [];
  private systemInstruction: string = '';

  constructor(apiKey: string, config?: Partial<VoiceAgentConfig>) {
    this.ai = new GoogleGenAI({ apiKey });
    this.config = {
      model: config?.model ?? DEFAULT_MODEL,
      voice: config?.voice ?? DEFAULT_VOICE,
      responseModalities: config?.responseModalities ?? [Modality.AUDIO, Modality.TEXT],
      systemInstruction: config?.systemInstruction,
      tools: config?.tools,
    };
    if (config?.tools) this.tools = config.tools;
    if (config?.systemInstruction) this.systemInstruction = config.systemInstruction;
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
   * Update tools available to the voice agent
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
   * Connect to Gemini Live API
   */
  async connect(context?: AgentContext): Promise<void> {
    if (!this.ai) {
      throw new Error('Voice agent not initialized');
    }

    this.emit({ type: 'connecting', agent: 'voice' });

    try {
      // Build system instruction with context
      const fullSystemInstruction = this.buildSystemInstruction(context);

      // Connect to Live API
      const session = await this.ai.live.connect({
        model: this.config.model,
        config: {
          responseModalities: this.config.responseModalities as unknown as Modality[],
          speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: {
                voiceName: this.config.voice,
              },
            },
          },
          systemInstruction: fullSystemInstruction ? { parts: [{ text: fullSystemInstruction }] } : undefined,
          tools: this.tools.length > 0 ? [{ functionDeclarations: this.tools as any }] : undefined,
        },
        callbacks: this.createCallbacks(),
      });

      this.session = session as unknown as LiveSession;
      this.emit({ type: 'connected', agent: 'voice' });
    } catch (error) {
      this.emit({ type: 'error', agent: 'voice', error: error as Error });
      throw error;
    }
  }

  /**
   * Disconnect from Live API
   */
  disconnect(): void {
    this.stopRecording();
    this.stopPlayback();
    
    if (this.session) {
      this.session.close();
      this.session = null;
    }

    this.emit({ type: 'disconnected', agent: 'voice' });
  }

  /**
   * Send text message
   */
  sendText(text: string): void {
    if (!this.session) {
      throw new Error('Voice agent not connected');
    }

    this.session.sendClientContent({
      turns: [{ role: 'user', parts: [{ text }] }],
      turnComplete: true,
    });
  }

  /**
   * Start recording audio from microphone
   */
  async startRecording(): Promise<void> {
    if (!this.session) {
      throw new Error('Voice agent not connected');
    }

    this.emit({ type: 'listening', agent: 'voice' });

    try {
      // Request microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: AUDIO_SAMPLE_RATE_INPUT,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // Create audio context
      this.audioContext = new AudioContext({ sampleRate: AUDIO_SAMPLE_RATE_INPUT });
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);

      // Create and connect audio worklet for PCM conversion
      await this.setupAudioWorklet(source);
    } catch (error) {
      this.emit({ type: 'error', agent: 'voice', error: error as Error });
      throw error;
    }
  }

  /**
   * Stop recording audio
   */
  stopRecording(): void {
    // Signal end of audio stream
    if (this.session) {
      this.session.sendRealtimeInput({ audioStreamEnd: true });
    }

    // Cleanup audio worklet
    if (this.audioWorklet) {
      this.audioWorklet.disconnect();
      this.audioWorklet = null;
    }

    // Cleanup media stream
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    // Cleanup audio context
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }
  }

  /**
   * Send tool response back to the model
   */
  sendToolResponse(responses: FunctionResponse[]): void {
    if (!this.session) {
      throw new Error('Voice agent not connected');
    }

    this.session.sendToolResponse({ functionResponses: responses });
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.session !== null;
  }

  // ==========================================================================
  // Private Methods
  // ==========================================================================

  private emit(event: AgentEvent): void {
    this.eventHandler?.(event);
  }

  private buildSystemInstruction(context?: AgentContext): string {
    const parts: string[] = [];

    // Base instruction
    if (this.systemInstruction) {
      parts.push(this.systemInstruction);
    }

    // Add workspace context
    if (context?.workspaceState) {
      parts.push(`\n## Current Workspace State`);
      parts.push(`Current Session: ${context.workspaceState.currentSessionId ?? 'None'}`);
      parts.push(`Selected Node: ${context.workspaceState.selectedNodeId ?? 'None'}`);
      parts.push(`Breadcrumb: ${context.workspaceState.breadcrumb.map(b => b.label).join(' → ') || 'Root'}`);
    }

    // Add canvas context
    if (context?.canvasState) {
      parts.push(`\n## Canvas State`);
      parts.push(`Nodes: ${context.canvasState.nodes.length}`);
      parts.push(`Edges: ${context.canvasState.edges.length}`);
      if (context.canvasState.nodes.length > 0) {
        const nodeTypes = [...new Set(context.canvasState.nodes.map(n => n.type))];
        parts.push(`Node Types: ${nodeTypes.join(', ')}`);
      }
    }

    return parts.join('\n');
  }

  private createCallbacks(): any {
    return {
      onopen: () => {
        console.log('[VoiceAgent] WebSocket connected');
      },
      onmessage: (message: any) => {
        this.handleServerMessage(message as LiveServerMessage);
      },
      onerror: (error: ErrorEvent) => {
        console.error('[VoiceAgent] WebSocket error:', error);
        this.emit({ type: 'error', agent: 'voice', error: new Error(error.message) });
      },
      onclose: (event: CloseEvent) => {
        console.log('[VoiceAgent] WebSocket closed:', event.reason);
        this.emit({ type: 'disconnected', agent: 'voice', reason: event.reason });
      },
    };
  }

  private handleServerMessage(message: LiveServerMessage): void {
    // Handle model turn (text or audio response)
    if (message.serverContent?.modelTurn?.parts) {
      for (const part of message.serverContent.modelTurn.parts) {
        // Text response
        if (part.text) {
          console.log('[VoiceAgent] Text:', part.text);
        }

        // Audio response
        if (part.inlineData?.data) {
          this.emit({ type: 'speaking', agent: 'voice' });
          const audioData = this.base64ToFloat32(part.inlineData.data);
          this.queueAudioForPlayback(audioData);
        }

        // Function call
        if (part.functionCall) {
          this.handleFunctionCall(part.functionCall);
        }
      }
    }

    // Handle tool calls
    if (message.toolCall?.functionCalls) {
      for (const call of message.toolCall.functionCalls) {
        this.handleFunctionCall(call);
      }
    }

    // Handle tool call cancellations
    if (message.toolCallCancellation?.ids) {
      console.log('[VoiceAgent] Tool calls cancelled:', message.toolCallCancellation.ids);
    }

    // Handle turn complete
    if (message.serverContent?.turnComplete) {
      console.log('[VoiceAgent] Turn complete');
    }
  }

  private handleFunctionCall(call: FunctionCall): void {
    this.emit({
      type: 'tool_call',
      agent: 'voice',
      call: {
        id: call.id ?? crypto.randomUUID(),
        type: 'function',
        function: {
          name: call.name,
          arguments: JSON.stringify(call.args),
        },
      },
    });
  }

  // ==========================================================================
  // Audio Processing
  // ==========================================================================

  private async setupAudioWorklet(source: MediaStreamAudioSourceNode): Promise<void> {
    if (!this.audioContext) return;

    // Create inline worklet processor
    const workletCode = `
      class PCMProcessor extends AudioWorkletProcessor {
        buffer = new Int16Array(2048);
        bufferIndex = 0;

        process(inputs) {
          const input = inputs[0];
          if (input.length === 0) return true;

          const channel = input[0];
          for (let i = 0; i < channel.length; i++) {
            // Convert float32 [-1, 1] to int16 [-32768, 32767]
            const sample = Math.max(-1, Math.min(1, channel[i]));
            this.buffer[this.bufferIndex++] = sample * 32767;

            if (this.bufferIndex >= this.buffer.length) {
              this.port.postMessage({
                type: 'audio',
                buffer: this.buffer.slice().buffer,
              }, [this.buffer.slice().buffer]);
              this.bufferIndex = 0;
            }
          }
          return true;
        }
      }
      registerProcessor('pcm-processor', PCMProcessor);
    `;

    const blob = new Blob([workletCode], { type: 'application/javascript' });
    const url = URL.createObjectURL(blob);

    await this.audioContext.audioWorklet.addModule(url);
    URL.revokeObjectURL(url);

    this.audioWorklet = new AudioWorkletNode(this.audioContext, 'pcm-processor');
    this.audioWorklet.port.onmessage = (event) => {
      if (event.data.type === 'audio') {
        this.sendAudioChunk(event.data.buffer);
      }
    };

    source.connect(this.audioWorklet);
  }

  private sendAudioChunk(buffer: ArrayBuffer): void {
    if (!this.session) return;

    // Send to Gemini
    this.session.sendRealtimeInput({
      audio: new Blob([buffer], { type: 'audio/pcm' }),
    });
  }

  private base64ToFloat32(base64: string): Float32Array {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }

    // Convert 16-bit PCM to float32
    const length = bytes.length / 2;
    const float32 = new Float32Array(length);
    for (let i = 0; i < length; i++) {
      // Little-endian 16-bit signed integer
      let sample = bytes[i * 2] | (bytes[i * 2 + 1] << 8);
      if (sample >= 32768) sample -= 65536;
      float32[i] = sample / 32768;
    }

    return float32;
  }

  // ==========================================================================
  // Audio Playback
  // ==========================================================================

  private queueAudioForPlayback(audioData: Float32Array): void {
    this.audioQueue.push(audioData);
    if (!this.isPlaying) {
      this.playNextAudio();
    }
  }

  private async playNextAudio(): Promise<void> {
    this.isPlaying = true;

    // Create audio context for playback if needed
    if (!this.audioContext || this.audioContext.state === 'closed') {
      this.audioContext = new AudioContext({ sampleRate: AUDIO_SAMPLE_RATE_OUTPUT });
      this.nextPlayTime = this.audioContext.currentTime;
    }

    while (this.audioQueue.length > 0) {
      const audioData: Float32Array = this.audioQueue.shift()!;
      
      // Create audio buffer
      const audioBuffer = this.audioContext.createBuffer(
        1, // mono
        audioData.length,
        AUDIO_SAMPLE_RATE_OUTPUT
      );
      // Copy audio data to buffer channel
      const channelData = audioBuffer.getChannelData(0);
      channelData.set(audioData);

      // Create and schedule source
      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(this.audioContext.destination);

      // Schedule playback
      if (this.nextPlayTime < this.audioContext.currentTime) {
        this.nextPlayTime = this.audioContext.currentTime;
      }
      source.start(this.nextPlayTime);
      this.nextPlayTime += audioBuffer.duration;
    }

    this.isPlaying = false;
  }

  private stopPlayback(): void {
    this.audioQueue = [];
    this.isPlaying = false;
  }
}

// ============================================================================
// Factory Function
// ============================================================================

export function createVoiceAgent(
  apiKey: string,
  config?: Partial<VoiceAgentConfig>
): VoiceAgent {
  return new VoiceAgent(apiKey, config);
}
