import Anthropic from '@anthropic-ai/sdk';
import type {
    Completion,
    Message,
    Prompt,
    ProviderFunctor,
    ToolSchema,
    ToolUse,
} from '../types.js';

function toAnthropicMessages(
    messages: Message[],
): Anthropic.MessageParam[] {
    return messages.map((msg): Anthropic.MessageParam => {
        if (typeof msg.content === 'string') {
            return { role: msg.role, content: msg.content };
        }
        const blocks: Anthropic.ContentBlockParam[] = msg.content.map((block) => {
            switch (block.type) {
                case 'text':
                    return { type: 'text', text: block.text ?? '' };
                case 'tool_use':
                    return {
                        type: 'tool_use',
                        id: block.id ?? '',
                        name: block.name ?? '',
                        input: block.input ?? {},
                    };
                case 'tool_result':
                    return {
                        type: 'tool_result',
                        tool_use_id: block.tool_use_id ?? '',
                        content: block.content ?? '',
                    };
                default:
                    return { type: 'text', text: '' };
            }
        });
        return { role: msg.role, content: blocks };
    });
}

function toAnthropicTools(
    tools: ToolSchema[],
): Anthropic.Tool[] {
    return tools.map((tool) => ({
        name: tool.name,
        description: tool.description ?? '',
        input_schema: (tool.input_schema ?? { type: 'object', properties: {} }) as Anthropic.Tool.InputSchema,
    }));
}

export class AnthropicProviderFunctor implements ProviderFunctor {
    readonly name = 'anthropic' as const;
    private readonly client: Anthropic;

    constructor(
        apiKey: string,
        private readonly model: string = 'claude-sonnet-4-6',
        private readonly maxTokens: number = 4096,
    ) {
        this.client = new Anthropic({ apiKey });
    }

    async *modelCall(prompt: Prompt): AsyncGenerator<Completion, void, void> {
        const response = await this.client.messages.create({
            model: this.model,
            max_tokens: this.maxTokens,
            system: prompt.system || undefined,
            messages: toAnthropicMessages(prompt.messages),
            tools: prompt.tools.length > 0 ? toAnthropicTools(prompt.tools) : undefined,
        });

        // Extract text content and tool uses from response
        let textContent = '';
        const toolUses: ToolUse[] = [];

        for (const block of response.content) {
            if (block.type === 'text') {
                textContent += block.text;
            } else if (block.type === 'tool_use') {
                toolUses.push({
                    id: block.id,
                    name: block.name,
                    input: block.input,
                });
            }
        }

        const stopReason = response.stop_reason === 'tool_use'
            ? 'tool_use' as const
            : response.stop_reason === 'max_tokens'
                ? 'max_tokens' as const
                : 'end_turn' as const;

        yield {
            content: textContent,
            stopReason,
            toolUses: toolUses.length > 0 ? toolUses : undefined,
            usage: {
                inputTokens: response.usage.input_tokens,
                outputTokens: response.usage.output_tokens,
            },
        };
    }
}
