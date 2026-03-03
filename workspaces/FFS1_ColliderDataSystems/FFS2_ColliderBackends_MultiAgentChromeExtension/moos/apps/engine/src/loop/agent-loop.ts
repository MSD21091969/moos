import {
    type ExecutionFunctor,
    type ProviderFunctor,
    type Prompt,
    type Message,
    type ContentBlock,
} from '@moos/functors';
import { type GraphMorphism, parseGraphMutationOutput } from '@moos/core';

export interface AgentTurnResult {
    text: string;
    executedTools: Array<{ id: string; name: string; output: unknown; error?: string }>;
    validatedMorphisms: GraphMorphism[];
}

export const runSingleTurn = async (
    provider: ProviderFunctor,
    executor: ExecutionFunctor,
    prompt: Prompt,
): Promise<AgentTurnResult> => {
    const toolResults: AgentTurnResult['executedTools'] = [];
    const validatedMorphisms: GraphMorphism[] = [];
    let finalText = '';

    for await (const completion of provider.modelCall(prompt)) {
        finalText = completion.content;
        const parsedMutation = parseGraphMutationOutput(completion.content);
        if (parsedMutation) {
            validatedMorphisms.push(...parsedMutation.morphisms);
        }

        if (completion.stopReason === 'tool_use' && completion.toolUses?.length) {
            for (const toolUse of completion.toolUses) {
                const toolResult = await executor.toolExecute(toolUse);
                toolResults.push({
                    id: toolUse.id,
                    name: toolUse.name,
                    output: toolResult.output,
                    error: toolResult.error,
                });
            }
        }

        if (completion.stopReason !== 'tool_use') {
            break;
        }
    }

    return {
        text: finalText,
        executedTools: toolResults,
        validatedMorphisms,
    };
};

// --- Multi-turn agent loop ---

export interface AgentLoopConfig {
    maxTurns?: number;
    provider: ProviderFunctor;
    executor: ExecutionFunctor;
    onValidatedMorphisms?: (payload: {
        turn: number;
        morphisms: GraphMorphism[];
    }) => Promise<void> | void;
}

export interface AgentLoopResult {
    finalText: string;
    turns: AgentTurnResult[];
    history: Message[];
    stopReason: 'end_turn' | 'max_turns' | 'error';
}

export const runAgentLoop = async (
    config: AgentLoopConfig,
    initialPrompt: Prompt,
): Promise<AgentLoopResult> => {
    const history: Message[] = [...initialPrompt.messages];
    const turns: AgentTurnResult[] = [];
    let turnCount = 0;
    const maxTurns = config.maxTurns ?? 20;

    while (turnCount < maxTurns) {
        turnCount++;
        const prompt: Prompt = { ...initialPrompt, messages: history };

        const turnResult = await runSingleTurn(config.provider, config.executor, prompt);
        turns.push(turnResult);

        if (turnResult.validatedMorphisms.length > 0 && config.onValidatedMorphisms) {
            await config.onValidatedMorphisms({
                turn: turnCount,
                morphisms: turnResult.validatedMorphisms,
            });
        }

        // Build assistant message content blocks
        const assistantBlocks: ContentBlock[] = [];
        if (turnResult.text) {
            assistantBlocks.push({ type: 'text', text: turnResult.text });
        }
        for (const tool of turnResult.executedTools) {
            assistantBlocks.push({
                type: 'tool_use',
                id: tool.id,
                name: tool.name,
                input: tool.output,
            });
        }

        history.push({
            role: 'assistant',
            content: assistantBlocks.length === 1 && assistantBlocks[0].type === 'text'
                ? assistantBlocks[0].text ?? ''
                : assistantBlocks,
        });

        // If tools were executed, append tool results and continue
        if (turnResult.executedTools.length > 0) {
            const toolResultBlocks: ContentBlock[] = turnResult.executedTools.map((tool) => ({
                type: 'tool_result' as const,
                tool_use_id: tool.id,
                content: typeof tool.output === 'string'
                    ? tool.output
                    : JSON.stringify(tool.output),
            }));

            history.push({
                role: 'user',
                content: toolResultBlocks,
            });
            continue;
        }

        // No tools executed → model is done
        return { finalText: turnResult.text, turns, history, stopReason: 'end_turn' };
    }

    return {
        finalText: turns.at(-1)?.text ?? '',
        turns,
        history,
        stopReason: 'max_turns',
    };
};
