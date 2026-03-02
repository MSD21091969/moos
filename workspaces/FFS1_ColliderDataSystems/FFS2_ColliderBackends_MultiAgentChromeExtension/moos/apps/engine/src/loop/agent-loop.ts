import {
    type ExecutionFunctor,
    type ProviderFunctor,
    type Prompt,
} from '@moos/functors';

export interface AgentTurnResult {
    text: string;
    executedTools: Array<{ name: string; output: unknown; error?: string }>;
}

export const runSingleTurn = async (
    provider: ProviderFunctor,
    executor: ExecutionFunctor,
    prompt: Prompt,
): Promise<AgentTurnResult> => {
    const toolResults: Array<{ name: string; output: unknown; error?: string }> = [];
    let finalText = '';

    for await (const completion of provider.modelCall(prompt)) {
        finalText = completion.content;

        if (completion.stopReason === 'tool_use' && completion.toolUses?.length) {
            for (const toolUse of completion.toolUses) {
                const toolResult = await executor.toolExecute(toolUse);
                toolResults.push({
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
    };
};
