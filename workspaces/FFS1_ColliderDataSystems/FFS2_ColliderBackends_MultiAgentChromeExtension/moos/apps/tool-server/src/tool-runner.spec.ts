import type { ToolUse } from '@moos/functors';
import { NoopExecutionFunctor } from '@moos/functors';
import { ToolRegistry } from './registry.js';
import { ToolRunner, type IsolationPolicy } from './tool-runner.js';

describe('tool-runner', () => {
    const baseToolUse: ToolUse = {
        id: 'runner-1',
        name: 'echo_tool',
        input: { hello: 'world' },
    };

    it('executes registered tools through registry', async () => {
        const registry = new ToolRegistry();
        registry.register({
            name: 'echo_tool',
            description: 'echo',
            execute: async (input) => ({ echoed: input }),
        });

        const policy: IsolationPolicy = {
            blockedToolPrefixes: [],
            maxInputBytes: 1024,
            maxExecutionMs: 100,
            allowFallbackExecution: true,
        };

        const runner = new ToolRunner(registry, new NoopExecutionFunctor(), policy);
        const result = await runner.execute(baseToolUse);

        expect(result.error).toBeUndefined();
        expect(result.output).toEqual({ echoed: { hello: 'world' } });
    });

    it('applies blocked-tool isolation policy', async () => {
        const registry = new ToolRegistry();
        const policy: IsolationPolicy = {
            blockedToolPrefixes: ['internal_'],
            maxInputBytes: 1024,
            maxExecutionMs: 100,
            allowFallbackExecution: true,
        };

        const runner = new ToolRunner(registry, new NoopExecutionFunctor(), policy);
        const result = await runner.execute({
            ...baseToolUse,
            name: 'internal_sensitive',
        });

        expect(result.error).toBe('isolation_blocked_tool');
        expect(result.output).toBeNull();
    });

    it('times out tool execution based on policy', async () => {
        const registry = new ToolRegistry();
        registry.register({
            name: 'slow_tool',
            description: 'slow',
            execute: async () => {
                await new Promise((resolve) => setTimeout(resolve, 20));
                return { ok: true };
            },
        });

        const policy: IsolationPolicy = {
            blockedToolPrefixes: [],
            maxInputBytes: 1024,
            maxExecutionMs: 1,
            allowFallbackExecution: true,
        };

        const runner = new ToolRunner(registry, new NoopExecutionFunctor(), policy);
        const result = await runner.execute({
            ...baseToolUse,
            name: 'slow_tool',
        });

        expect(result.error).toBe('isolation_execution_timeout');
        expect(result.output).toBeNull();
    });

    it('reports tool name allowance from isolation policy', () => {
        const registry = new ToolRegistry();
        const policy: IsolationPolicy = {
            blockedToolPrefixes: ['internal_', 'admin_'],
            maxInputBytes: 1024,
            maxExecutionMs: 100,
            allowFallbackExecution: true,
        };

        const runner = new ToolRunner(registry, new NoopExecutionFunctor(), policy);

        expect(runner.isToolNameAllowed('echo_tool')).toBe(true);
        expect(runner.isToolNameAllowed('internal_trace')).toBe(false);
        expect(runner.isToolNameAllowed('admin_reset')).toBe(false);
    });

    it('enforces per-tool input and timeout overrides', async () => {
        const registry = new ToolRegistry();
        registry.register({
            name: 'tight_tool',
            description: 'tight policy',
            execute: async () => {
                await new Promise((resolve) => setTimeout(resolve, 20));
                return { ok: true };
            },
        });

        const policy: IsolationPolicy = {
            blockedToolPrefixes: [],
            maxInputBytes: 4096,
            maxExecutionMs: 200,
            allowFallbackExecution: true,
        };

        const runner = new ToolRunner(registry, new NoopExecutionFunctor(), policy);
        runner.setToolPolicyOverride('tight_tool', {
            maxInputBytes: 8,
            maxExecutionMs: 1,
        });

        const oversized = await runner.execute({
            id: 'ovr-1',
            name: 'tight_tool',
            input: { payload: 'abcdefghijk' },
        });
        expect(oversized.error).toBe('isolation_input_too_large');

        const timeout = await runner.execute({
            id: 'ovr-2',
            name: 'tight_tool',
            input: 'ok',
        });
        expect(timeout.error).toBe('isolation_execution_timeout');
    });

    it('supports per-tool fallback disable override', async () => {
        const registry = new ToolRegistry();
        const policy: IsolationPolicy = {
            blockedToolPrefixes: [],
            maxInputBytes: 1024,
            maxExecutionMs: 100,
            allowFallbackExecution: true,
        };

        const runner = new ToolRunner(registry, new NoopExecutionFunctor(), policy);
        runner.setToolPolicyOverride('unknown_tool', {
            allowFallbackExecution: false,
        });

        const result = await runner.execute({
            id: 'ovr-3',
            name: 'unknown_tool',
            input: {},
        });

        expect(result.error).toBe('unknown_tool');
        expect(result.output).toBeNull();
    });
});
