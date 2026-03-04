import type { AddressInfo } from 'node:net';
import { createServer } from 'node:http';
import {
    HttpExecutionFunctor,
    McpJsonRpcExecutionFunctor,
    ToolFirstProviderFunctor,
} from '@moos/functors';
import { fetchBootstrapContext } from '../context/bootstrap-client.js';
import { runSingleTurn } from '../loop/agent-loop.js';

describe('engine contract flow', () => {
    it('executes end-to-end bootstrap + tool execution flow', async () => {
        let mcpCallCount = 0;
        let executeCallCount = 0;

        const dataServer = createServer((req, res) => {
            if (req.method === 'POST' && req.url === '/bootstrap') {
                res.statusCode = 200;
                res.setHeader('content-type', 'application/json');
                res.end(JSON.stringify({
                    system: 'integration-system',
                    messages: ['morphism:bootstrap.morphism provider:echo'],
                }));
                return;
            }
            res.statusCode = 404;
            res.end();
        });

        const toolServer = createServer(async (req, res) => {
            if (req.method === 'POST' && req.url === '/mcp/messages') {
                const chunks: Buffer[] = [];
                for await (const chunk of req) {
                    chunks.push(Buffer.from(chunk));
                }
                const body = JSON.parse(Buffer.concat(chunks).toString('utf-8')) as {
                    jsonrpc: '2.0';
                    id: string;
                    method: string;
                    params?: { name?: string };
                };

                mcpCallCount += 1;

                if (body.method !== 'tools/call') {
                    res.statusCode = 404;
                    res.setHeader('content-type', 'application/json');
                    res.end(
                        JSON.stringify({
                            jsonrpc: '2.0',
                            id: body.id ?? null,
                            error: { code: -32601, message: 'method not found' },
                        }),
                    );
                    return;
                }

                res.statusCode = 200;
                res.setHeader('content-type', 'application/json');
                res.end(
                    JSON.stringify({
                        jsonrpc: '2.0',
                        id: body.id,
                        result: {
                            output: {
                                acknowledged: true,
                                tool: body.params?.name,
                                via: 'mcp',
                            },
                        },
                    }),
                );
                return;
            }

            if (req.method === 'POST' && req.url === '/execute') {
                executeCallCount += 1;

                res.statusCode = 200;
                res.setHeader('content-type', 'application/json');
                res.end(
                    JSON.stringify({
                        output: { acknowledged: true, tool: 'fallback' },
                    }),
                );
                return;
            }
            res.statusCode = 404;
            res.end();
        });

        await new Promise<void>((resolve) => dataServer.listen(0, resolve));
        await new Promise<void>((resolve) => toolServer.listen(0, resolve));

        const dataPort = (dataServer.address() as AddressInfo).port;
        const toolPort = (toolServer.address() as AddressInfo).port;

        const context = await fetchBootstrapContext(
            `http://127.0.0.1:${dataPort}`,
            ['bootstrap.morphism'],
        );

        const result = await runSingleTurn(
            new ToolFirstProviderFunctor(),
            new McpJsonRpcExecutionFunctor(
                `http://127.0.0.1:${toolPort}`,
                new HttpExecutionFunctor(`http://127.0.0.1:${toolPort}`),
            ),
            {
                system: context.system,
                messages: [
                    ...context.messages,
                    {
                        role: 'user',
                        content: 'integration-run',
                    },
                ],
                tools: [{ name: 'echo_tool' }],
            },
        );

        expect(result.text).toContain('complete:');
        expect(result.executedTools).toHaveLength(1);
        expect(result.executedTools[0].name).toBe('echo_tool');
        expect(result.executedTools[0].output).toEqual({
            acknowledged: true,
            tool: 'echo_tool',
            via: 'mcp',
        });
        expect(mcpCallCount).toBe(1);
        expect(executeCallCount).toBe(0);

        await new Promise<void>((resolve, reject) => {
            toolServer.close((error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });

        await new Promise<void>((resolve, reject) => {
            dataServer.close((error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });
    });
});
