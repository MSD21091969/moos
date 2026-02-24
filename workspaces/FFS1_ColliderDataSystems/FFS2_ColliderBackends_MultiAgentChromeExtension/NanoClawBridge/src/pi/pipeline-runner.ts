import crypto from "node:crypto";
import type { AgentEvent } from "../event-parser.js";
import type { IAgentSession } from "../sdk/agent-session.js";
import type { ComposedContext } from "../sdk/types.js";

export interface PipelineStep {
    id?: string;
    prompt: string;
}

export interface PipelineResult {
    pipelineId: string;
    steps: Array<{
        id: string;
        output: string;
        hadError: boolean;
    }>;
}

export class PipelineRunner {
    constructor(private readonly agent: IAgentSession) { }

    async run(params: {
        pipelineId?: string;
        context: ComposedContext;
        steps: PipelineStep[];
    }): Promise<PipelineResult> {
        const pipelineId = params.pipelineId ?? `pipeline-${crypto.randomUUID()}`;
        const results: PipelineResult["steps"] = [];

        for (let index = 0; index < params.steps.length; index += 1) {
            const step = params.steps[index];
            const stepId = step.id ?? `step-${index + 1}`;
            const sessionId = `${pipelineId}-${stepId}`;
            this.agent.createSession({
                sessionId,
                context: params.context,
            });

            let output = "";
            let hadError = false;

            for await (const event of this.agent.sendMessage(sessionId, step.prompt)) {
                output = mergeOutput(output, event);
                if (event.kind === "error") {
                    hadError = true;
                }
            }

            this.agent.terminateSession(sessionId);

            results.push({ id: stepId, output: output.trim(), hadError });
            if (hadError) {
                break;
            }
        }

        return {
            pipelineId,
            steps: results,
        };
    }
}

function mergeOutput(current: string, event: AgentEvent): string {
    if (event.kind === "text_delta") {
        return `${current}${event.text}`;
    }

    if (event.kind === "tool_result") {
        return `${current}\n[tool:${event.name}] ${event.result}`;
    }

    if (event.kind === "error") {
        return `${current}\n[error] ${event.message}`;
    }

    return current;
}
