import { GoogleGenAI, type Content, type FunctionDeclaration, type Part } from '@google/genai';
import type {
    Completion,
    Message,
    Prompt,
    ProviderFunctor,
    ToolSchema,
    ToolUse,
} from '../types.js';

function toGeminiContents(messages: Message[]): Content[] {
    return messages.map((msg): Content => {
        const role = msg.role === 'assistant' ? 'model' : 'user';
        if (typeof msg.content === 'string') {
            return { role, parts: [{ text: msg.content }] };
        }
        const parts: Part[] = msg.content.map((block) => {
            switch (block.type) {
                case 'text':
                    return { text: block.text ?? '' };
                case 'tool_use':
                    return {
                        functionCall: {
                            name: block.name ?? '',
                            args: (block.input ?? {}) as Record<string, unknown>,
                        },
                    };
                case 'tool_result':
                    return {
                        functionResponse: {
                            name: block.tool_use_id ?? '',
                            response: { result: block.content ?? '' },
                        },
                    };
                default:
                    return { text: '' };
            }
        });
        return { role, parts };
    });
}

function toGeminiFunctionDeclarations(tools: ToolSchema[]): FunctionDeclaration[] {
    return tools.map((tool) => ({
        name: tool.name,
        description: tool.description ?? '',
        parameters: tool.input_schema as Record<string, unknown> | undefined,
    }));
}

export class GeminiProviderFunctor implements ProviderFunctor {
    readonly name = 'gemini' as const;
    private readonly client: GoogleGenAI;

    constructor(
        apiKey: string,
        private readonly model: string = 'gemini-2.5-flash',
    ) {
        this.client = new GoogleGenAI({ apiKey });
    }

    async *modelCall(prompt: Prompt): AsyncGenerator<Completion, void, void> {
        const functionDeclarations = prompt.tools.length > 0
            ? toGeminiFunctionDeclarations(prompt.tools)
            : undefined;

        const contents = toGeminiContents(prompt.messages);

        const response = await this.client.models.generateContent({
            model: this.model,
            contents,
            config: {
                systemInstruction: prompt.system || undefined,
                tools: functionDeclarations
                    ? [{ functionDeclarations }]
                    : undefined,
            },
        });

        let textContent = '';
        const toolUses: ToolUse[] = [];
        let idCounter = 0;

        const candidates = response.candidates;
        if (candidates && candidates.length > 0) {
            const parts = candidates[0].content?.parts ?? [];
            for (const part of parts) {
                if (part.text) {
                    textContent += part.text;
                }
                if (part.functionCall) {
                    toolUses.push({
                        id: `gemini-tool-${idCounter++}`,
                        name: part.functionCall.name ?? '',
                        input: part.functionCall.args ?? {},
                    });
                }
            }
        }

        const finishReason = candidates?.[0]?.finishReason;
        const stopReason = finishReason === 'STOP'
            ? (toolUses.length > 0 ? 'tool_use' as const : 'end_turn' as const)
            : finishReason === 'MAX_TOKENS'
                ? 'max_tokens' as const
                : toolUses.length > 0
                    ? 'tool_use' as const
                    : 'end_turn' as const;

        yield {
            content: textContent,
            stopReason,
            toolUses: toolUses.length > 0 ? toolUses : undefined,
            usage: response.usageMetadata
                ? {
                    inputTokens: response.usageMetadata.promptTokenCount ?? 0,
                    outputTokens: response.usageMetadata.candidatesTokenCount ?? 0,
                }
                : undefined,
        };
    }
}
