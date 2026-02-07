import { CreateMLCEngine, MLCEngine, InitProgressCallback } from "@mlc-ai/web-llm";

// =============================================================================
// LOCAL INTELLIGENCE - WebLLM Wrapper (EXPERIMENTAL)
// =============================================================================

// Qwen2.5-Coder-3B: Best balance of code understanding and browser performance
// - 3B params fits in most GPUs with 4GB+ VRAM
// - Excellent code completion and understanding
// - ~4K context window (limited for large files)
const DEFAULT_MODEL = "Qwen2.5-Coder-3B-Instruct-q4f16_1-MLC";

// Alternative models (uncomment to switch):
// const DEFAULT_MODEL = "Llama-3.2-1B-Instruct-q4f32_1-MLC"; // Faster, less capable
// const DEFAULT_MODEL = "Qwen2.5-Coder-7B-Instruct-q4f16_1-MLC"; // More capable, needs 8GB+ VRAM

export interface LocalAgentConfig {
    modelId?: string;
    temperature?: number;
    systemInstruction?: string;
}

/**
 * LocalIntelligence - WebLLM-based local model inference
 * 
 * ⚠️ EXPERIMENTAL: This is an experimental feature for local-first AI.
 * Limitations:
 * - Context window: ~4K tokens (vs 1M for Gemini 3)
 * - First load: Downloads 1-3GB model weights
 * - Requires WebGPU support (Edge, Chrome 113+)
 * - Performance varies by GPU
 * 
 * Use Gemini (cloud) for production; WebLLM for offline/privacy experiments.
 */
export class LocalIntelligence {
    private engine: MLCEngine | null = null;
    private modelId: string;
    private isLoaded = false;
    private hasFailed = false;
    private loadPromise: Promise<void> | null = null;

    constructor(config: LocalAgentConfig = {}) {
        this.modelId = config.modelId || DEFAULT_MODEL;
    }

    /**
     * Initialize the engine and download weights if needed
     */
    async init(onProgress?: InitProgressCallback): Promise<void> {
        if (this.isLoaded) return;
        if (this.hasFailed) {
            throw new Error("Previous attempt to load local model failed. Please refresh to try again or use Cloud mode.");
        }
        if (this.loadPromise) return this.loadPromise;

        if (!('gpu' in navigator)) {
            throw new Error("WebGPU is not supported in this browser. Please use Edge, Chrome, or a compatible browser.");
        }

        // eslint-disable-next-line no-console
        console.log(`[LocalIntelligence] Initializing model: ${this.modelId}`);
        
        this.loadPromise = (async () => {
            try {
                this.engine = await CreateMLCEngine(
                    this.modelId,
                    { 
                        initProgressCallback: onProgress,
                        logLevel: "INFO"
                    }
                );
                this.isLoaded = true;
                // eslint-disable-next-line no-console
                console.log("[LocalIntelligence] Model loaded successfully");
            } catch (error) {
                console.error("[LocalIntelligence] Failed to load model:", error);
                this.loadPromise = null;
                this.hasFailed = true;
                
                // Check for common WebGPU errors
                const errStr = String(error);
                if (errStr.includes("GPUAdapter") || errStr.includes("device lost") || errStr.includes("DXGI_ERROR_DEVICE_REMOVED")) {
                    throw new Error("WebGPU initialization failed. Your device or browser might not support running this model locally. Please try Cloud mode.");
                }
                
                throw error;
            }
        })();

        return this.loadPromise;
    }

    /**
     * Send a message to the local model
     */
    async sendMessage(
        text: string, 
        history: Array<{ role: string; content: string | null; tool_calls?: unknown[] }> = [], 
        tools: Array<unknown> = [],
        systemInstruction?: string
    ): Promise<{ text: string; toolCalls?: Array<unknown> }> {
        if (!this.engine) {
            throw new Error("Engine not initialized. Call init() first.");
        }

        // Convert Google-style tools to OpenAI-style tools if needed
        const openAITools = this.convertToolsToOpenAI(tools);

        const messages = [
            { role: "system", content: systemInstruction || "You are a helpful assistant." },
            ...history,
            { role: "user", content: text }
        ];

        try {
            const reply = await this.engine.chat.completions.create({
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                messages: messages as any, 
                tools: openAITools.length > 0 ? openAITools : undefined,
                tool_choice: openAITools.length > 0 ? "auto" : undefined,
                temperature: 0.7,
            });

            const choice = reply.choices[0];
            const responseText = choice.message.content || "";
            const toolCalls = choice.message.tool_calls;

            return {
                text: responseText,
                toolCalls: toolCalls as Array<unknown>
            };

        } catch (error) {
            console.error("[LocalIntelligence] Generation failed:", error);
            throw error;
        }
    }

    /**
     * Convert Google Generative AI tool format to OpenAI format
     */
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    private convertToolsToOpenAI(googleTools: Array<any>): Array<any> {
        // Handle the case where tools are wrapped in { functionDeclarations: [...] }
        let funcs = googleTools;
        if (googleTools.length > 0 && googleTools[0].functionDeclarations) {
            funcs = googleTools[0].functionDeclarations;
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return funcs.map((tool: any) => ({
            type: "function",
            function: {
                name: tool.name,
                description: tool.description,
                parameters: tool.parameters
            }
        }));
    }

    get loaded(): boolean {
        return this.isLoaded;
    }
}
