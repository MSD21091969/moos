import type { AddressInfo } from 'node:net';
import { createToolServer } from './main.js';

describe('tool-server', () => {
    it('executes registry tool endpoint and exposes tools + mcp sse', async () => {
        const server = createToolServer();
        await new Promise<void>((resolve) => server.listen(0, resolve));
        const { port } = server.address() as AddressInfo;
        const base = `http://127.0.0.1:${port}`;

        const health = await fetch(`${base}/health`);
        expect(health.status).toBe(200);

        const execute = await fetch(`${base}/execute`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                id: 'tool-1',
                name: 'echo_tool',
                input: { hello: 'world' },
            }),
        });

        expect(execute.status).toBe(200);
        const payload = (await execute.json()) as {
            output: { echoed: { hello: string } };
        };
        expect(payload.output.echoed).toEqual({ hello: 'world' });

        const tools = await fetch(`${base}/tools`);
        expect(tools.status).toBe(200);
        const toolsPayload = (await tools.json()) as { tools: Array<{ name: string }> };
        expect(toolsPayload.tools.some((tool) => tool.name === 'echo_tool')).toBe(true);

        const sse = await fetch(`${base}/mcp/sse`);
        expect(sse.status).toBe(200);
        const sseText = await sse.text();
        expect(sseText).toContain('event: ready');
        expect(sseText).toContain('"jsonrpc":"2.0"');
        expect(sseText).toContain('"method":"server.ready"');
        expect(sseText).toContain('echo_tool');

        const mcpList = await fetch(`${base}/mcp/messages`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: 'rpc-1',
                method: 'tools/list',
                params: {},
            }),
        });
        expect(mcpList.status).toBe(200);
        const mcpListPayload = (await mcpList.json()) as {
            jsonrpc: '2.0';
            id: string;
            result: { tools: Array<{ name: string }> };
        };
        expect(mcpListPayload.jsonrpc).toBe('2.0');
        expect(mcpListPayload.id).toBe('rpc-1');
        expect(mcpListPayload.result.tools.some((tool) => tool.name === 'echo_tool')).toBe(
            true
        );

        const register = await fetch(`${base}/tools/register`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                name: 'dynamic_tool',
                description: 'runtime-added',
                mode: 'echo',
                isolation: {
                    maxInputBytes: 128,
                    maxExecutionMs: 50,
                },
            }),
        });

        expect(register.status).toBe(201);

        const blockedRegister = await fetch(`${base}/tools/register`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                name: 'internal_hidden_tool',
                description: 'should be blocked',
                mode: 'echo',
            }),
        });

        expect(blockedRegister.status).toBe(403);
        const blockedRegisterPayload = (await blockedRegister.json()) as {
            error: string;
            name: string;
        };
        expect(blockedRegisterPayload.error).toBe('isolation_blocked_tool');

        const executeDynamic = await fetch(`${base}/execute`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                id: 'tool-3',
                name: 'dynamic_tool',
                input: { runtime: true },
            }),
        });
        expect(executeDynamic.status).toBe(200);
        const dynamicPayload = (await executeDynamic.json()) as {
            output: { echoed: { runtime: boolean } };
        };
        expect(dynamicPayload.output.echoed).toEqual({ runtime: true });

        const dynamicPolicy = await fetch(`${base}/isolation/policy/dynamic_tool`);
        expect(dynamicPolicy.status).toBe(200);
        const dynamicPolicyPayload = (await dynamicPolicy.json()) as {
            tool: string;
            override: { maxInputBytes?: number; maxExecutionMs?: number } | null;
        };
        expect(dynamicPolicyPayload.tool).toBe('dynamic_tool');
        expect(dynamicPolicyPayload.override?.maxInputBytes).toBe(128);
        expect(dynamicPolicyPayload.override?.maxExecutionMs).toBe(50);

        const dynamicOversized = await fetch(`${base}/execute`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                id: 'tool-3b',
                name: 'dynamic_tool',
                input: { payload: 'x'.repeat(512) },
            }),
        });
        expect(dynamicOversized.status).toBe(200);
        const dynamicOversizedPayload = (await dynamicOversized.json()) as {
            error?: string;
            output: unknown;
        };
        expect(dynamicOversizedPayload.error).toBe('isolation_input_too_large');

        const mcpCall = await fetch(`${base}/mcp/messages`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: 'rpc-2',
                method: 'tools/call',
                params: {
                    name: 'dynamic_tool',
                    input: { via: 'mcp' },
                },
            }),
        });
        expect(mcpCall.status).toBe(200);
        const mcpCallPayload = (await mcpCall.json()) as {
            jsonrpc: '2.0';
            id: string;
            result: { output: { echoed: { via: string } } };
        };
        expect(mcpCallPayload.id).toBe('rpc-2');
        expect(mcpCallPayload.result.output.echoed).toEqual({ via: 'mcp' });

        const mcpInvalidParams = await fetch(`${base}/mcp/messages`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: 'rpc-3',
                method: 'tools/call',
                params: {},
            }),
        });
        expect(mcpInvalidParams.status).toBe(400);
        const mcpInvalidPayload = (await mcpInvalidParams.json()) as {
            jsonrpc: '2.0';
            id: string;
            error: { code: number; message: string };
        };
        expect(mcpInvalidPayload.error.code).toBe(-32602);

        const mcpMethodMissing = await fetch(`${base}/mcp/messages`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: 'rpc-4',
                method: 'unknown/method',
                params: {},
            }),
        });
        expect(mcpMethodMissing.status).toBe(404);
        const mcpMethodMissingPayload = (await mcpMethodMissing.json()) as {
            jsonrpc: '2.0';
            id: string;
            error: { code: number; message: string };
        };
        expect(mcpMethodMissingPayload.error.code).toBe(-32601);

        const fallbackExecute = await fetch(`${base}/execute`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                id: 'tool-2',
                name: 'unknown_tool',
                input: { ping: true },
            }),
        });

        expect(fallbackExecute.status).toBe(200);
        const fallbackPayload = (await fallbackExecute.json()) as {
            output: { acknowledged: boolean; tool: string };
        };
        expect(fallbackPayload.output.acknowledged).toBe(true);
        expect(fallbackPayload.output.tool).toBe('unknown_tool');

        const isolationPolicy = await fetch(`${base}/isolation/policy`);
        expect(isolationPolicy.status).toBe(200);
        const isolationPayload = (await isolationPolicy.json()) as {
            policy: { blockedToolPrefixes: string[]; maxInputBytes: number };
        };
        expect(isolationPayload.policy.maxInputBytes).toBeGreaterThan(0);
        expect(isolationPayload.policy.blockedToolPrefixes).toContain('internal_');

        const blockedExecute = await fetch(`${base}/execute`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                id: 'tool-4',
                name: 'internal_secret_tool',
                input: { secret: true },
            }),
        });

        expect(blockedExecute.status).toBe(200);
        const blockedPayload = (await blockedExecute.json()) as {
            output: unknown;
            error?: string;
        };
        expect(blockedPayload.error).toBe('isolation_blocked_tool');

        const oversizedExecute = await fetch(`${base}/execute`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                id: 'tool-5',
                name: 'echo_tool',
                input: { payload: 'x'.repeat(20_000) },
            }),
        });

        expect(oversizedExecute.status).toBe(200);
        const oversizedPayload = (await oversizedExecute.json()) as {
            output: unknown;
            error?: string;
        };
        expect(oversizedPayload.error).toBe('isolation_input_too_large');

        await new Promise<void>((resolve, reject) => {
            server.close((error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });
    });

    it('enforces JSON-RPC protocol semantics for mcp messages', async () => {
        const server = createToolServer();
        await new Promise<void>((resolve) => server.listen(0, resolve));
        const { port } = server.address() as AddressInfo;
        const base = `http://127.0.0.1:${port}`;

        const cases: Array<{
            name: string;
            body: string;
            expectedStatus: number;
            expectedId: string | number | null;
            expectedErrorCode?: number;
            expectResult?: boolean;
        }> = [
                {
                    name: 'parse error returns -32700',
                    body: '{bad json',
                    expectedStatus: 400,
                    expectedId: null,
                    expectedErrorCode: -32700,
                },
                {
                    name: 'invalid request returns -32600',
                    body: JSON.stringify({ jsonrpc: '2.0', id: 'x-1' }),
                    expectedStatus: 400,
                    expectedId: null,
                    expectedErrorCode: -32600,
                },
                {
                    name: 'method not found returns -32601 and preserves id',
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        id: 7,
                        method: 'unknown/method',
                        params: {},
                    }),
                    expectedStatus: 404,
                    expectedId: 7,
                    expectedErrorCode: -32601,
                },
                {
                    name: 'tools/list with missing id normalizes to null',
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'tools/list',
                        params: {},
                    }),
                    expectedStatus: 200,
                    expectedId: null,
                    expectResult: true,
                },
            ];

        for (const testCase of cases) {
            const response = await fetch(`${base}/mcp/messages`, {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: testCase.body,
            });

            expect(response.status).toBe(testCase.expectedStatus);

            const payload = (await response.json()) as {
                jsonrpc: '2.0';
                id: string | number | null;
                result?: unknown;
                error?: { code: number; message: string };
            };

            expect(payload.jsonrpc).toBe('2.0');
            expect(payload.id).toBe(testCase.expectedId);

            if (typeof testCase.expectedErrorCode === 'number') {
                expect(payload.error?.code).toBe(testCase.expectedErrorCode);
            }

            if (testCase.expectResult) {
                expect(payload.result).toBeDefined();
            }
        }

        await new Promise<void>((resolve, reject) => {
            server.close((error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });
    });

    it('meets MCP conformance load baseline for tools/list and tools/call', async () => {
        const server = createToolServer();
        await new Promise<void>((resolve) => server.listen(0, resolve));
        const { port } = server.address() as AddressInfo;
        const base = `http://127.0.0.1:${port}`;

        const totalCalls = 120;
        let successCount = 0;
        const latencies: number[] = [];

        for (let index = 0; index < totalCalls; index += 1) {
            const method = index % 2 === 0 ? 'tools/list' : 'tools/call';
            const startedAt = Date.now();

            const response = await fetch(`${base}/mcp/messages`, {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    id: `load-${index}`,
                    method,
                    params:
                        method === 'tools/call'
                            ? { name: 'echo_tool', input: { seq: index } }
                            : {},
                }),
            });

            const elapsed = Date.now() - startedAt;
            latencies.push(elapsed);

            if (!response.ok) {
                continue;
            }

            const payload = (await response.json()) as {
                jsonrpc: '2.0';
                error?: { code: number; message: string };
                result?: unknown;
            };

            if (payload.jsonrpc === '2.0' && payload.error === undefined && payload.result !== undefined) {
                successCount += 1;
            }
        }

        const successRate = successCount / totalCalls;
        const ordered = [...latencies].sort((a, b) => a - b);
        const p95 = ordered[Math.max(0, Math.ceil(ordered.length * 0.95) - 1)];

        expect(successRate).toBeGreaterThanOrEqual(0.99);
        expect(p95).toBeLessThanOrEqual(1500);

        await new Promise<void>((resolve, reject) => {
            server.close((error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });
    });
});
