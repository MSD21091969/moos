import type { Server } from 'node:http';
import type { AddressInfo } from 'node:net';
import WebSocket from 'ws';

import { createAgentCompatServer, createDataServer, createNanoClawCompatBridge } from './main.js';

const startServer = async (server: Server): Promise<string> => {
    await new Promise<void>((resolve) => server.listen(0, resolve));
    const { port } = server.address() as AddressInfo;
    return `http://127.0.0.1:${port}`;
};

const closeServer = async (server: Server): Promise<void> => {
    await new Promise<void>((resolve, reject) => {
        server.close((error) => {
            if (error) {
                reject(error);
                return;
            }
            resolve();
        });
    });
};

const waitFor = async (predicate: () => boolean, timeoutMs = 2000): Promise<void> => {
    const start = Date.now();
    while (!predicate()) {
        if (Date.now() - start > timeoutMs) {
            throw new Error('Timed out waiting for condition');
        }
        await new Promise((resolve) => setTimeout(resolve, 10));
    }
};

describe('data-server', () => {
    it('serves health and stores morphism/bootstrap context', async () => {
        const server = createDataServer();
        const base = await startServer(server);

        const health = await fetch(`${base}/health`);
        expect(health.status).toBe(200);

        const shape = {
            inputs: [{ name: 'x', schema: 'number' }],
            outputs: [{ name: 'x', schema: 'number' }],
        };

        const morphismResponse = await fetch(`${base}/morphisms`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                id: 'm-1',
                source: shape,
                target: shape,
                properties: { provider: 'echo' },
            }),
        });
        expect(morphismResponse.status).toBe(201);

        const bootstrap = await fetch(`${base}/bootstrap`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({ morphismIds: ['m-1'], system: 'test-system' }),
        });

        expect(bootstrap.status).toBe(200);
        const payload = (await bootstrap.json()) as { system: string; messages: string[] };
        expect(payload.system).toBe('test-system');
        expect(payload.messages).toHaveLength(1);

        await closeServer(server);
    });

    it('implements FFS3 REST compatibility contracts', async () => {
        const server = createDataServer();
        const base = await startServer(server);

        const loginResp = await fetch(`${base}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({ username: 'Sam', password: 'Sam' }),
        });
        expect(loginResp.status).toBe(200);
        const loginData = (await loginResp.json()) as { access_token: string };
        const bearer = `Bearer ${loginData.access_token}`;

        const meResp = await fetch(`${base}/api/v1/users/me`, {
            headers: { Authorization: bearer },
        });
        expect(meResp.status).toBe(200);

        const usersResp = await fetch(`${base}/api/v1/users`, {
            headers: { Authorization: bearer },
        });
        expect(usersResp.status).toBe(200);

        const appsResp = await fetch(`${base}/api/v1/apps/`, {
            headers: { Authorization: bearer },
        });
        expect(appsResp.status).toBe(200);
        const apps = (await appsResp.json()) as Array<{ id: string }>;
        expect(apps.length).toBeGreaterThan(0);
        const appId = apps[0].id;

        const treeResp = await fetch(`${base}/api/v1/apps/${appId}/nodes/tree`, {
            headers: { Authorization: bearer },
        });
        expect(treeResp.status).toBe(200);

        const workflowResp = await fetch(`${base}/api/v1/execution/workflow/workflow-demo`, {
            method: 'POST',
            headers: {
                Authorization: bearer,
                'content-type': 'application/json',
            },
            body: JSON.stringify({ input: {} }),
        });
        expect(workflowResp.status).toBe(200);

        const appUserLogin = await fetch(`${base}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({ username: 'Jules', password: 'Jules' }),
        });
        const appUserData = (await appUserLogin.json()) as { access_token: string };
        const appUserPending = await fetch(`${base}/api/v1/apps/${appId}/pending-requests`, {
            headers: { Authorization: `Bearer ${appUserData.access_token}` },
        });
        expect(appUserPending.status).toBe(403);

        const appAdminLogin = await fetch(`${base}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({ username: 'Alex', password: 'Alex' }),
        });
        const appAdminData = (await appAdminLogin.json()) as { access_token: string };
        const appAdminBearer = `Bearer ${appAdminData.access_token}`;

        const pendingResp = await fetch(`${base}/api/v1/apps/${appId}/pending-requests`, {
            headers: { Authorization: appAdminBearer },
        });
        expect(pendingResp.status).toBe(200);
        const pending = (await pendingResp.json()) as Array<{ id: string }>;
        expect(pending.length).toBeGreaterThan(0);

        const approveResp = await fetch(
            `${base}/api/v1/apps/${appId}/requests/${pending[0].id}/approve`,
            {
                method: 'POST',
                headers: {
                    Authorization: appAdminBearer,
                    'content-type': 'application/json',
                },
                body: JSON.stringify({ role: 'app_user' }),
            },
        );
        expect(approveResp.status).toBe(200);

        await closeServer(server);
    });
});

describe('agent-compat-server', () => {
    it('creates compatible agent sessions', async () => {
        const sessionStore = new Map();
        const server = createAgentCompatServer(sessionStore);
        const base = await startServer(server);

        const health = await fetch(`${base}/health`);
        expect(health.status).toBe(200);

        const resp = await fetch(`${base}/agent/session`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                role: 'app_admin',
                app_id: 'app-1',
                node_ids: ['n1', 'n2'],
            }),
        });
        expect(resp.status).toBe(200);

        const body = (await resp.json()) as {
            session_id: string;
            nanoclaw_ws_url: string;
            preview: { node_count: number };
        };

        expect(body.session_id).toBeTruthy();
        expect(body.nanoclaw_ws_url).toContain('ws://');
        expect(body.preview.node_count).toBe(2);

        await closeServer(server);
    });
});

describe('nanoclaw-compat-bridge', () => {
    it('supports bridge and jsonrpc request formats with streaming events', async () => {
        const sessionStore = new Map();
        const server = createNanoClawCompatBridge(sessionStore);
        await new Promise<void>((resolve) => server.listen(0, resolve));
        const { port } = server.address() as AddressInfo;
        const ws = new WebSocket(`ws://127.0.0.1:${port}`);

        await new Promise<void>((resolve, reject) => {
            ws.once('open', () => resolve());
            ws.once('error', (error) => reject(error));
        });

        const frames: Array<Record<string, unknown>> = [];
        ws.on('message', (buffer) => {
            frames.push(JSON.parse(buffer.toString()) as Record<string, unknown>);
        });

        ws.send(
            JSON.stringify({
                jsonrpc: '2.0',
                id: '1',
                method: 'agent.request',
                params: { message: 'hello world' },
            }),
        );

        await waitFor(() => frames.some((frame) => frame.type === 'event' && frame.event === 'message_end'));
        expect(frames.some((frame) => frame.type === 'response' && frame.id === '1')).toBe(true);
        expect(frames.some((frame) => frame.type === 'event' && frame.event === 'tool_use_start')).toBe(true);
        expect(frames.some((frame) => frame.type === 'event' && frame.event === 'tool_result')).toBe(true);

        ws.send(
            JSON.stringify({
                type: 'request',
                id: '2',
                method: 'sessions.list',
                params: { limit: 1 },
            }),
        );

        await waitFor(() => frames.some((frame) => frame.type === 'response' && frame.id === '2'));
        const listFrame = frames.find((frame) => frame.type === 'response' && frame.id === '2');
        expect(Array.isArray(listFrame?.result)).toBe(true);

        ws.close();
        await closeServer(server);
    });
});
