import type { ToolExecutionResult } from '@moos/core';
import { NoopExecutionFunctor, type ExecutionFunctor, type ToolUse } from '@moos/functors';
import type { ToolRegistry } from './registry.js';

export interface IsolationPolicy {
    blockedToolPrefixes: string[];
    maxInputBytes: number;
    maxExecutionMs: number;
    allowFallbackExecution: boolean;
}

export interface ToolIsolationOverride {
    maxInputBytes?: number;
    maxExecutionMs?: number;
    allowFallbackExecution?: boolean;
}

export const defaultIsolationPolicy = (): IsolationPolicy => ({
    blockedToolPrefixes: (process.env.TOOL_RUNNER_BLOCKED_PREFIXES ?? 'internal_')
        .split(',')
        .map((value) => value.trim())
        .filter((value) => value.length > 0),
    maxInputBytes: Number(process.env.TOOL_RUNNER_MAX_INPUT_BYTES ?? 16_384),
    maxExecutionMs: Number(process.env.TOOL_RUNNER_TIMEOUT_MS ?? 1_500),
    allowFallbackExecution: (process.env.TOOL_RUNNER_ALLOW_FALLBACK ?? 'true') === 'true',
});

export class ToolRunner {
    private readonly perToolOverrides = new Map<string, ToolIsolationOverride>();

    public constructor(
        private readonly registry: ToolRegistry,
        private readonly fallback: ExecutionFunctor = new NoopExecutionFunctor(),
        private readonly policy: IsolationPolicy = defaultIsolationPolicy(),
    ) { }

    public getPolicy(): IsolationPolicy {
        return { ...this.policy, blockedToolPrefixes: [...this.policy.blockedToolPrefixes] };
    }

    public isToolNameAllowed(toolName: string): boolean {
        return !this.isBlocked(toolName);
    }

    public setToolPolicyOverride(toolName: string, override: ToolIsolationOverride): void {
        this.perToolOverrides.set(toolName, { ...override });
    }

    public getToolPolicyOverride(toolName: string): ToolIsolationOverride | undefined {
        const override = this.perToolOverrides.get(toolName);
        return override ? { ...override } : undefined;
    }

    public async execute(toolUse: ToolUse): Promise<ToolExecutionResult> {
        const effectivePolicy = this.resolvePolicy(toolUse.name);

        if (this.isBlocked(toolUse.name)) {
            return {
                output: null,
                error: 'isolation_blocked_tool',
            };
        }

        const inputBytes = Buffer.byteLength(JSON.stringify(toolUse.input ?? null), 'utf-8');
        if (inputBytes > effectivePolicy.maxInputBytes) {
            return {
                output: null,
                error: 'isolation_input_too_large',
            };
        }

        if (this.registry.has(toolUse.name)) {
            return this.withTimeout(() => this.registry.execute(toolUse), effectivePolicy.maxExecutionMs);
        }

        if (!effectivePolicy.allowFallbackExecution) {
            return {
                output: null,
                error: 'unknown_tool',
            };
        }

        return this.withTimeout(() => this.fallback.toolExecute(toolUse), effectivePolicy.maxExecutionMs);
    }

    private resolvePolicy(toolName: string): IsolationPolicy {
        const override = this.perToolOverrides.get(toolName);

        return {
            blockedToolPrefixes: [...this.policy.blockedToolPrefixes],
            maxInputBytes: override?.maxInputBytes ?? this.policy.maxInputBytes,
            maxExecutionMs: override?.maxExecutionMs ?? this.policy.maxExecutionMs,
            allowFallbackExecution:
                override?.allowFallbackExecution ?? this.policy.allowFallbackExecution,
        };
    }

    private isBlocked(toolName: string): boolean {
        return this.policy.blockedToolPrefixes.some((prefix) => toolName.startsWith(prefix));
    }

    private async withTimeout(
        run: () => Promise<ToolExecutionResult>,
        timeoutMs: number,
    ): Promise<ToolExecutionResult> {
        let timeoutId: NodeJS.Timeout | undefined;

        const timeout = new Promise<ToolExecutionResult>((resolve) => {
            timeoutId = setTimeout(() => {
                resolve({
                    output: null,
                    error: 'isolation_execution_timeout',
                });
            }, timeoutMs);
        });

        const result = await Promise.race([run(), timeout]);
        if (timeoutId) {
            clearTimeout(timeoutId);
        }

        return result;
    }
}
