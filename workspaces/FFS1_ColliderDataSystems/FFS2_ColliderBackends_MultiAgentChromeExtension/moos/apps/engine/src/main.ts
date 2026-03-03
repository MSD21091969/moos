import {
    HttpExecutionFunctor,
    McpJsonRpcExecutionFunctor,
    ToolFirstProviderFunctor,
} from '@moos/functors';
import { MutationEnvelopeSchema, type MutationEnvelope } from '@moos/core';
import { fetchBootstrapContext } from './context/bootstrap-client.js';
import { runAgentLoop } from './loop/agent-loop.js';
import { SessionManager } from './session/manager.js';

const sleep = async (delayMs: number): Promise<void> => {
    await new Promise((resolve) => setTimeout(resolve, delayMs));
};

const publishMorphismsToBus = async (
    agentCompatUrl: string,
    envelope: MutationEnvelope,
): Promise<boolean> => {
    const maxAttempts = Math.max(1, Number(process.env.MOOS_MORPHISM_PUBLISH_ATTEMPTS ?? 3));
    const baseDelayMs = Math.max(25, Number(process.env.MOOS_MORPHISM_PUBLISH_DELAY_MS ?? 150));

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            const response = await fetch(`${agentCompatUrl}/agent/morphisms`, {
                method: 'POST',
                headers: {
                    'content-type': 'application/json',
                },
                body: JSON.stringify(envelope),
            });

            if (response.ok) {
                return true;
            }

            const responseBody = await response.text().catch(() => '');
            console.warn('[moos-engine] morphism publish rejected by agent bus', {
                attempt,
                maxAttempts,
                status: response.status,
                body: responseBody.slice(0, 500),
            });
        } catch (error) {
            console.warn('[moos-engine] morphism publish transport failure', {
                attempt,
                maxAttempts,
                message: error instanceof Error ? error.message : String(error),
            });
        }

        if (attempt < maxAttempts) {
            await sleep(baseDelayMs * attempt);
        }
    }

    return false;
};

const bootstrap = async (): Promise<void> => {
    const dataServerUrl = process.env.DATA_SERVER_URL ?? 'http://127.0.0.1:8000';
    const toolServerUrl = process.env.TOOL_SERVER_URL ?? 'http://127.0.0.1:8001';
    const agentCompatUrl = process.env.AGENT_COMPAT_URL ?? 'http://127.0.0.1:8004';

    const provider = new ToolFirstProviderFunctor();
    const fallbackExecutor = new HttpExecutionFunctor(toolServerUrl);
    const executor = new McpJsonRpcExecutionFunctor(toolServerUrl, fallbackExecutor);
    const sessions = new SessionManager();

    const session = sessions.create('bootstrap-session');
    const context = await fetchBootstrapContext(dataServerUrl, ['bootstrap.morphism']);

    sessions.append(session.sessionId, { role: 'user', content: 'bootstrap-started' });

    const result = await runAgentLoop(
        {
            provider,
            executor,
            maxTurns: 5,
            onValidatedMorphisms: async ({ turn, morphisms }) => {
                console.log('[moos-engine] validated morphisms', {
                    turn,
                    count: morphisms.length,
                    morphism_types: morphisms.map((m) => m.morphism_type),
                });

                const envelopeResult = MutationEnvelopeSchema.safeParse({
                    source: 'engine',
                    turn,
                    sessionKey: session.sessionId,
                    morphisms,
                });

                if (!envelopeResult.success) {
                    console.warn('[moos-engine] invalid mutation envelope; skipping publish', {
                        turn,
                        count: morphisms.length,
                    });
                    return;
                }

                const published = await publishMorphismsToBus(agentCompatUrl, envelopeResult.data);
                if (!published) {
                    console.warn('[moos-engine] exhausted morphism publish retries', {
                        turn,
                        count: morphisms.length,
                    });
                }
            },
        },
        {
            system: context.system,
            messages: [...context.messages, { role: 'user', content: 'hello moos' }],
            tools: [{ name: 'echo_tool', description: 'echo contract tool' }],
        },
    );

    sessions.append(session.sessionId, { role: 'assistant', content: result.finalText });

    console.log('[moos-engine] loop result:', result.finalText);
    console.log('[moos-engine] turns:', result.turns.length);
    console.log('[moos-engine] stop reason:', result.stopReason);
};

void bootstrap();
