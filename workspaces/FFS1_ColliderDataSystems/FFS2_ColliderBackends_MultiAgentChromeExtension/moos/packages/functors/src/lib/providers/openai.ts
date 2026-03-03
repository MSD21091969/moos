import OpenAI from 'openai';
import type {
    Completion,
    Message,
    Prompt,
    ProviderFunctor,
    ToolSchema,
    ToolUse,
} from '../types.js';

function toOpenAIMessages(
    system: string,
    messages: Message[],
): OpenAI.ChatCompletionMessageParam[] {
    const result: OpenAI.ChatCompletionMessageParam[] = [];

    if (system) {
        result.push({ role: 'system', content: system });
    }

    for (const msg of messages) {
        if (typeof msg.content === 'string') {
            result.push({
                role: msg.role as 'user' | 'assistant',
                content: msg.content,
            });
            continue;
        }

        if (msg.role === 'assistant') {
            const textParts = msg.content.filter((b) => b.type === 'text');
            const toolUseParts = msg.content.filter((b) => b.type === 'tool_use');

            const toolCalls: OpenAI.ChatCompletionMessageToolCall[] = toolUseParts.map((b) => ({
                id: b.id ?? '',
                type: 'function' as const,
                function: {
                    name: b.name ?? '',
                    arguments: JSON.stringify(b.input ?? {}),
                },
            }));

            result.push({
                role: 'assistant',
                content: textParts.map((b) => b.text ?? '').join('') || null,
                tool_calls: toolCalls.length > 0 ? toolCalls : undefined,
            });
        } else {
            // User messages may contain tool_result blocks
            const toolResults = msg.content.filter((b) => b.type === 'tool_result');
            if (toolResults.length > 0) {
                for (const tr of toolResults) {
                    result.push({
                        role: 'tool',
                        tool_call_id: tr.tool_use_id ?? '',
                        content: tr.content ?? '',
                    });
                }
            } else {
                const text = msg.content
                    .filter((b) => b.type === 'text')
                    .map((b) => b.text ?? '')
                    .join('');
                result.push({ role: 'user', content: text });
            }
        }
    }

    return result;
}

function toOpenAITools(
    tools: ToolSchema[],
): OpenAI.ChatCompletionTool[] {
    return tools.map((tool) => ({
        type: 'function' as const,
        function: {
            name: tool.name,
            description: tool.description ?? '',
            parameters: tool.input_schema ?? { type: 'object', properties: {} },
        },
    }));
}

export class OpenAiProviderFunctor implements ProviderFunctor {
    readonly name = 'openai' as const;
    private readonly client: OpenAI;

    constructor(
        apiKey: string,
        private readonly model: string = 'gpt-4o',
        private readonly maxTokens: number = 4096,
    ) {
        this.client = new OpenAI({ apiKey });
    }

    async *modelCall(prompt: Prompt): AsyncGenerator<Completion, void, void> {
        const response = await this.client.chat.completions.create({
            model: this.model,
            max_tokens: this.maxTokens,
            messages: toOpenAIMessages(prompt.system, prompt.messages),
            tools: prompt.tools.length > 0 ? toOpenAITools(prompt.tools) : undefined,
        });

        const choice = response.choices[0];
        if (!choice) {
            yield { content: '', stopReason: 'error' };
            return;
        }

        const textContent = choice.message.content ?? '';
        const toolUses: ToolUse[] = (choice.message.tool_calls ?? [])
            .filter((tc): tc is OpenAI.ChatCompletionMessageFunctionToolCall => tc.type === 'function')
            .map((tc) => ({
                id: tc.id,
                name: tc.function.name,
                input: JSON.parse(tc.function.arguments || '{}') as unknown,
            }));

        const finishReason = choice.finish_reason;
        const stopReason = finishReason === 'tool_calls'
            ? 'tool_use' as const
            : finishReason === 'length'
                ? 'max_tokens' as const
                : toolUses.length > 0
                    ? 'tool_use' as const
                    : 'end_turn' as const;

        yield {
            content: textContent,
            stopReason,
            toolUses: toolUses.length > 0 ? toolUses : undefined,
            usage: response.usage
                ? {
                    inputTokens: response.usage.prompt_tokens,
                    outputTokens: response.usage.completion_tokens,
                }
                : undefined,
        };
    }
}
