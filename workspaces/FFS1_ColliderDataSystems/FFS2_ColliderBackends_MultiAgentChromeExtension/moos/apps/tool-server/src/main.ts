import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import {
    JSON_RPC_ERROR_CODES,
    JSON_RPC_VERSION,
    MCP_METHODS,
    type JsonRpcResponse,
    isJsonRpcRequestShape,
} from '@moos/core';
import type { ToolUse } from '@moos/functors';
import { createDefaultRegistry } from './registry.js';
import { ToolRunner } from './tool-runner.js';

const port = Number(process.env.PORT ?? 8001);

const readJsonBody = async <T>(req: IncomingMessage): Promise<T> => {
    const chunks: Buffer[] = [];
    for await (const chunk of req) {
        chunks.push(Buffer.from(chunk));
    }
    const payload = Buffer.concat(chunks).toString('utf-8') || '{}';
    return JSON.parse(payload) as T;
};

const readBodyText = async (req: IncomingMessage): Promise<string> => {
    const chunks: Buffer[] = [];
    for await (const chunk of req) {
        chunks.push(Buffer.from(chunk));
    }

    return Buffer.concat(chunks).toString('utf-8');
};

const sendJson = (res: ServerResponse, statusCode: number, body: unknown): void => {
    res.statusCode = statusCode;
    res.setHeader('content-type', 'application/json');
    res.end(JSON.stringify(body));
};

export const createToolServer = () => {
    const registry = createDefaultRegistry();
    const toolRunner = new ToolRunner(registry);

    return createServer(async (req, res) => {
        try {
            const executeTool = async (toolUse: ToolUse) => toolRunner.execute(toolUse);

            if (req.method === 'GET' && req.url === '/health') {
                sendJson(res, 200, { status: 'ok', service: 'tool-server' });
                return;
            }

            if (req.method === 'GET' && req.url === '/tools') {
                sendJson(res, 200, { tools: registry.list() });
                return;
            }

            if (req.method === 'GET' && req.url === '/mcp/sse') {
                res.statusCode = 200;
                res.setHeader('content-type', 'text/event-stream');
                res.setHeader('cache-control', 'no-cache');
                res.setHeader('connection', 'keep-alive');

                const payload = JSON.stringify({
                    jsonrpc: JSON_RPC_VERSION,
                    method: MCP_METHODS.serverReady,
                    params: {
                        protocol: 'mcp-sse-v0',
                        tools: registry.list(),
                    },
                });

                res.write(`event: ready\n`);
                res.write(`data: ${payload}\n\n`);
                res.end();
                return;
            }

            if (req.method === 'POST' && req.url === '/tools/register') {
                const payload = await readJsonBody<{
                    name: string;
                    description?: string;
                    mode?: 'echo' | 'sum_numbers';
                    isolation?: {
                        maxInputBytes?: number;
                        maxExecutionMs?: number;
                    };
                }>(req);

                if (!payload.name || payload.name.trim().length === 0) {
                    sendJson(res, 400, { error: 'invalid_tool_name' });
                    return;
                }

                if (!toolRunner.isToolNameAllowed(payload.name)) {
                    sendJson(res, 403, {
                        error: 'isolation_blocked_tool',
                        name: payload.name,
                    });
                    return;
                }

                registry.registerRuntime({
                    name: payload.name,
                    description: payload.description,
                    mode: payload.mode,
                });

                if (payload.isolation) {
                    toolRunner.setToolPolicyOverride(payload.name, {
                        maxInputBytes: payload.isolation.maxInputBytes,
                        maxExecutionMs: payload.isolation.maxExecutionMs,
                    });
                }

                sendJson(res, 201, {
                    registered: true,
                    name: payload.name,
                });
                return;
            }

            if (req.method === 'GET' && req.url?.startsWith('/isolation/policy/')) {
                const toolName = decodeURIComponent(req.url.replace('/isolation/policy/', ''));
                sendJson(res, 200, {
                    tool: toolName,
                    override: toolRunner.getToolPolicyOverride(toolName) ?? null,
                });
                return;
            }

            if (req.method === 'GET' && req.url === '/isolation/policy') {
                sendJson(res, 200, {
                    policy: toolRunner.getPolicy(),
                });
                return;
            }

            if (req.method === 'POST' && req.url === '/execute') {
                const toolUse = await readJsonBody<ToolUse>(req);
                const result = await executeTool(toolUse);
                sendJson(res, 200, result);
                return;
            }

            if (req.method === 'POST' && req.url === '/mcp/messages') {
                const rawBody = await readBodyText(req);
                let parsedMessage: unknown;

                try {
                    parsedMessage = JSON.parse(rawBody || '{}');
                } catch {
                    sendJson(res, 400, {
                        jsonrpc: JSON_RPC_VERSION,
                        id: null,
                        error: {
                            code: JSON_RPC_ERROR_CODES.parseError,
                            message: 'parse error',
                        },
                    } satisfies JsonRpcResponse);
                    return;
                }

                if (!isJsonRpcRequestShape(parsedMessage)) {
                    sendJson(res, 400, {
                        jsonrpc: JSON_RPC_VERSION,
                        id: null,
                        error: {
                            code: JSON_RPC_ERROR_CODES.invalidRequest,
                            message: 'invalid request',
                        },
                    } satisfies JsonRpcResponse);
                    return;
                }

                const message = parsedMessage;
                const responseBase: Pick<JsonRpcResponse, 'jsonrpc' | 'id'> = {
                    jsonrpc: JSON_RPC_VERSION,
                    id: message.id ?? null,
                };

                if (message.method === MCP_METHODS.toolsList) {
                    sendJson(res, 200, {
                        ...responseBase,
                        result: {
                            tools: registry.list(),
                        },
                    } satisfies JsonRpcResponse);
                    return;
                }

                if (message.method === MCP_METHODS.toolsCall) {
                    const name =
                        typeof message.params?.name === 'string'
                            ? message.params.name
                            : undefined;

                    if (!name || name.trim().length === 0) {
                        sendJson(res, 400, {
                            ...responseBase,
                            error: {
                                code: JSON_RPC_ERROR_CODES.invalidParams,
                                message: 'invalid params: name is required',
                            },
                        } satisfies JsonRpcResponse);
                        return;
                    }

                    const toolUse: ToolUse = {
                        id: String(responseBase.id ?? 'mcp-call'),
                        name,
                        input: message.params?.input,
                    };

                    const callResult = await executeTool(toolUse);
                    sendJson(res, 200, {
                        ...responseBase,
                        result: callResult,
                    } satisfies JsonRpcResponse);
                    return;
                }

                sendJson(res, 404, {
                    ...responseBase,
                    error: {
                        code: JSON_RPC_ERROR_CODES.methodNotFound,
                        message: 'method not found',
                    },
                } satisfies JsonRpcResponse);
                return;
            }

            sendJson(res, 404, { error: 'not_found' });
        } catch (error) {
            sendJson(res, 500, {
                error: 'internal_error',
                message: error instanceof Error ? error.message : 'unknown',
            });
        }
    });
};

const server = createToolServer();

if (process.env.NODE_ENV !== 'test') {
    server.listen(port, () => {
        console.log(`[moos-tool-server] listening on :${port}`);
    });
}
