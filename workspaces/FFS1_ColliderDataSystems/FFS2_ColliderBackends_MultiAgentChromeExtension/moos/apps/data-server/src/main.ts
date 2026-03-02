import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { randomUUID } from 'node:crypto';
import { makeContainer } from '@moos/core';
import { InMemoryCategoryStore, type StoredObject } from '@moos/store';
import { WebSocketServer, type WebSocket } from 'ws';

const port = Number(process.env.PORT ?? 8000);

const readJsonBody = async <T>(req: IncomingMessage): Promise<T> => {
    const chunks: Buffer[] = [];
    for await (const chunk of req) {
        chunks.push(Buffer.from(chunk));
    }
    const payload = Buffer.concat(chunks).toString('utf-8') || '{}';
    return JSON.parse(payload) as T;
};

interface ObjectPayload {
    id: string;
    shape: StoredObject['shape'];
    properties?: Record<string, unknown>;
}

interface MorphismPayload {
    id: string;
    source: StoredObject['shape'];
    target: StoredObject['shape'];
    properties?: Record<string, unknown>;
}

interface MorphismQueryPayload {
    source: StoredObject['shape'];
    target: StoredObject['shape'];
}

type SystemRole = 'superadmin' | 'collider_admin' | 'app_admin' | 'app_user';
interface UserRecord {
    id: string;
    username: string;
    password: string;
    system_role: SystemRole;
    created_at: string;
    updated_at: string;
}

interface AppRecord {
    id: string;
    name: string;
    display_name: string;
    description: string;
    owner_id: string;
    root_node_id: string;
    config: Record<string, unknown>;
    created_at: string;
    updated_at: string;
}

interface NodeRecord {
    id: string;
    application_id: string;
    parent_id: string | null;
    path: string;
    container: Record<string, unknown>;
    metadata_: Record<string, unknown>;
    created_at: string;
    updated_at: string;
}

interface AccessRequestRecord {
    id: string;
    user_id: string;
    application_id: string;
    message: string | null;
    status: 'pending' | 'approved' | 'rejected';
    requested_at: string;
    resolved_at: string | null;
    resolved_by: string | null;
}

interface AppPermissionRecord {
    id: string;
    user_id: string;
    application_id: string;
    role: 'app_admin' | 'app_user';
    created_at: string;
}

const nowIso = (): string => new Date().toISOString();

const roleRank = (role: SystemRole): number => {
    switch (role) {
        case 'superadmin':
            return 4;
        case 'collider_admin':
            return 3;
        case 'app_admin':
            return 2;
        case 'app_user':
            return 1;
    }
};

const createSeedData = () => {
    const createdAt = nowIso();

    const sam: UserRecord = {
        id: '00000000-0000-0000-0000-000000000001',
        username: 'Sam',
        password: 'Sam',
        system_role: 'superadmin',
        created_at: createdAt,
        updated_at: createdAt,
    };

    const appAdmin: UserRecord = {
        id: '00000000-0000-0000-0000-000000000002',
        username: 'Alex',
        password: 'Alex',
        system_role: 'app_admin',
        created_at: createdAt,
        updated_at: createdAt,
    };

    const appUser: UserRecord = {
        id: '00000000-0000-0000-0000-000000000003',
        username: 'Jules',
        password: 'Jules',
        system_role: 'app_user',
        created_at: createdAt,
        updated_at: createdAt,
    };

    const appId = 'c57ab23a-4a57-4b28-a34c-9700320565ea';
    const rootNodeId = '9848b323-5e65-4179-a1d6-5b99be9f8b87';
    const app: AppRecord = {
        id: appId,
        name: 'App 2XZ',
        display_name: 'App 2XZ',
        description: 'Seeded compatibility application',
        owner_id: sam.id,
        root_node_id: rootNodeId,
        config: {},
        created_at: createdAt,
        updated_at: createdAt,
    };

    const rootNode: NodeRecord = {
        id: rootNodeId,
        application_id: appId,
        parent_id: null,
        path: 'root',
        container: {
            kind: 'workspace',
            species: 'ide',
            config: { domain: 'global' },
            skills: [{ name: 'bootstrap' }],
            tools: [{ name: 'echo_tool' }],
        },
        metadata_: {},
        created_at: createdAt,
        updated_at: createdAt,
    };

    const workflowNode: NodeRecord = {
        id: '11111111-1111-1111-1111-111111111111',
        application_id: appId,
        parent_id: rootNodeId,
        path: 'root/workflow-demo',
        container: {
            kind: 'workflow',
            species: 'workflow',
            name: 'workflow-demo',
            workflows: [{ name: 'workflow-demo' }],
            config: { domain: 'ops' },
            tools: [{ name: 'echo_tool' }],
            skills: [{ name: 'workflow_runner' }],
        },
        metadata_: {},
        created_at: createdAt,
        updated_at: createdAt,
    };

    const pendingRequest: AccessRequestRecord = {
        id: '22222222-2222-2222-2222-222222222222',
        user_id: appUser.id,
        application_id: appId,
        message: 'Please grant app access',
        status: 'pending',
        requested_at: createdAt,
        resolved_at: null,
        resolved_by: null,
    };

    const appAdminPermission: AppPermissionRecord = {
        id: '33333333-3333-3333-3333-333333333333',
        user_id: appAdmin.id,
        application_id: appId,
        role: 'app_admin',
        created_at: createdAt,
    };

    return {
        users: new Map<string, UserRecord>([
            [sam.id, sam],
            [appAdmin.id, appAdmin],
            [appUser.id, appUser],
        ]),
        apps: new Map<string, AppRecord>([[app.id, app]]),
        nodes: new Map<string, NodeRecord>([
            [rootNode.id, rootNode],
            [workflowNode.id, workflowNode],
        ]),
        accessRequests: new Map<string, AccessRequestRecord>([[pendingRequest.id, pendingRequest]]),
        appPermissions: new Map<string, AppPermissionRecord>([[appAdminPermission.id, appAdminPermission]]),
        tokens: new Map<string, string>(),
    };
};

export const createDataServer = () => {
    const db = new InMemoryCategoryStore();
    const state = createSeedData();

    const sendJsonWithCors = (res: ServerResponse, statusCode: number, body: unknown): void => {
        res.statusCode = statusCode;
        res.setHeader('content-type', 'application/json');
        res.setHeader('access-control-allow-origin', '*');
        res.setHeader('access-control-allow-methods', 'GET,POST,PATCH,DELETE,OPTIONS');
        res.setHeader('access-control-allow-headers', 'Content-Type,Authorization');
        res.end(JSON.stringify(body));
    };

    const parseBearer = (req: IncomingMessage): string | null => {
        const auth = req.headers.authorization;
        if (!auth || !auth.startsWith('Bearer ')) {
            return null;
        }
        return auth.slice('Bearer '.length).trim();
    };

    const getCurrentUser = (req: IncomingMessage): UserRecord | null => {
        const token = parseBearer(req);
        if (!token) {
            return null;
        }
        const userId = state.tokens.get(token);
        if (!userId) {
            return null;
        }
        return state.users.get(userId) ?? null;
    };

    const requireAuth = (req: IncomingMessage, res: ServerResponse): UserRecord | null => {
        const user = getCurrentUser(req);
        if (!user) {
            sendJsonWithCors(res, 401, {
                detail: 'Could not validate credentials',
            });
            return null;
        }
        return user;
    };

    const requireRole = (
        req: IncomingMessage,
        res: ServerResponse,
        requiredRole: SystemRole,
    ): UserRecord | null => {
        const user = requireAuth(req, res);
        if (!user) {
            return null;
        }
        if (roleRank(user.system_role) < roleRank(requiredRole)) {
            sendJsonWithCors(res, 403, {
                detail: `Requires ${requiredRole} role or higher`,
            });
            return null;
        }
        return user;
    };

    const toUserResponse = (user: UserRecord) => ({
        id: user.id,
        username: user.username,
        role: user.system_role,
        system_role: user.system_role,
        created_at: user.created_at,
        updated_at: user.updated_at,
    });

    const toAppResponse = (app: AppRecord) => ({
        id: app.id,
        name: app.name,
        display_name: app.display_name,
        description: app.description,
        owner_id: app.owner_id,
        root_node_id: app.root_node_id,
        config: app.config,
        created_at: app.created_at,
        updated_at: app.updated_at,
    });

    const canManageAppRequests = (user: UserRecord, appId: string): boolean => {
        if (user.system_role === 'superadmin' || user.system_role === 'collider_admin') {
            return true;
        }

        const app = state.apps.get(appId);
        if (app && app.owner_id === user.id) {
            return true;
        }

        return [...state.appPermissions.values()].some(
            (permission) =>
                permission.application_id === appId &&
                permission.user_id === user.id &&
                permission.role === 'app_admin',
        );
    };

    const buildTreeForApp = (applicationId: string): unknown[] => {
        const appNodes = [...state.nodes.values()]
            .filter((node) => node.application_id === applicationId)
            .sort((left, right) => left.path.localeCompare(right.path));

        const byParent = new Map<string | null, NodeRecord[]>();
        for (const node of appNodes) {
            const list = byParent.get(node.parent_id) ?? [];
            list.push(node);
            byParent.set(node.parent_id, list);
        }

        const makeNode = (node: NodeRecord): unknown => ({
            id: node.id,
            path: node.path,
            container: node.container,
            metadata_: node.metadata_,
            children: (byParent.get(node.id) ?? []).map((child) => makeNode(child)),
        });

        return (byParent.get(null) ?? []).map((node) => makeNode(node));
    };

    const resolvePath = (req: IncomingMessage): string => {
        const url = req.url ?? '/';
        return url.split('?')[0] ?? '/';
    };

    return createServer(async (req, res) => {
        try {
            const path = resolvePath(req);

            if (req.method === 'OPTIONS') {
                sendJsonWithCors(res, 204, {});
                return;
            }

            if (req.method === 'GET' && req.url === '/health') {
                sendJsonWithCors(res, 200, { status: 'ok', service: 'data-server' });
                return;
            }

            if (
                req.method === 'POST' &&
                (path === '/api/v1/auth/login' || path === '/api/v1/users/login')
            ) {
                const payload = await readJsonBody<{ username?: string; password?: string }>(req);
                const username = payload.username ?? '';
                const password = payload.password ?? '';
                const user = [...state.users.values()].find(
                    (candidate) => candidate.username === username && candidate.password === password,
                );

                if (!user) {
                    sendJsonWithCors(res, 401, {
                        detail: 'Incorrect username or password',
                    });
                    return;
                }

                const token = randomUUID();
                state.tokens.set(token, user.id);
                sendJsonWithCors(res, 200, {
                    access_token: token,
                    token_type: 'bearer',
                    user: toUserResponse(user),
                });
                return;
            }

            if (req.method === 'GET' && path === '/api/v1/users/me') {
                const user = requireAuth(req, res);
                if (!user) {
                    return;
                }
                sendJsonWithCors(res, 200, toUserResponse(user));
                return;
            }

            if (req.method === 'GET' && (path === '/api/v1/users' || path === '/api/v1/users/')) {
                const user = requireRole(req, res, 'collider_admin');
                if (!user) {
                    return;
                }
                sendJsonWithCors(res, 200, [...state.users.values()].map((entry) => toUserResponse(entry)));
                return;
            }

            const assignRoleMatch = path.match(/^\/api\/v1\/users\/([^/]+)\/assign-role$/);
            if (req.method === 'POST' && assignRoleMatch) {
                const actingUser = requireRole(req, res, 'collider_admin');
                if (!actingUser) {
                    return;
                }

                const userId = assignRoleMatch[1];
                const targetUser = state.users.get(userId);
                if (!targetUser) {
                    sendJsonWithCors(res, 404, { detail: 'User not found' });
                    return;
                }

                const payload = await readJsonBody<{ system_role?: SystemRole }>(req);
                const requestedRole = payload.system_role;
                if (!requestedRole) {
                    sendJsonWithCors(res, 400, { detail: 'system_role is required' });
                    return;
                }

                if (
                    actingUser.system_role === 'collider_admin' &&
                    (requestedRole === 'collider_admin' || requestedRole === 'superadmin')
                ) {
                    sendJsonWithCors(res, 403, {
                        detail: 'COLLIDER_ADMIN can only assign APP_ADMIN or APP_USER roles',
                    });
                    return;
                }

                targetUser.system_role = requestedRole;
                targetUser.updated_at = nowIso();
                sendJsonWithCors(res, 200, {
                    message: `User ${targetUser.username} assigned role ${requestedRole}`,
                });
                return;
            }

            if (req.method === 'GET' && (path === '/api/v1/apps' || path === '/api/v1/apps/')) {
                const user = requireAuth(req, res);
                if (!user) {
                    return;
                }
                sendJsonWithCors(res, 200, [...state.apps.values()].map((entry) => toAppResponse(entry)));
                return;
            }

            const appMatch = path.match(/^\/api\/v1\/apps\/([^/]+)$/);
            if (req.method === 'GET' && appMatch) {
                const user = requireAuth(req, res);
                if (!user) {
                    return;
                }
                const appId = appMatch[1];
                const app = state.apps.get(appId);
                if (!app) {
                    sendJsonWithCors(res, 404, { detail: 'Application not found' });
                    return;
                }
                sendJsonWithCors(res, 200, toAppResponse(app));
                return;
            }

            const appTreeMatch = path.match(/^\/api\/v1\/apps\/([^/]+)\/nodes\/tree$/);
            if (req.method === 'GET' && appTreeMatch) {
                const user = requireAuth(req, res);
                if (!user) {
                    return;
                }
                const appId = appTreeMatch[1];
                if (!state.apps.has(appId)) {
                    sendJsonWithCors(res, 404, { detail: 'Application not found' });
                    return;
                }
                sendJsonWithCors(res, 200, buildTreeForApp(appId));
                return;
            }

            const nodeDetailMatch = path.match(/^\/api\/v1\/apps\/([^/]+)\/nodes\/([^/]+)$/);
            if (req.method === 'GET' && nodeDetailMatch) {
                const user = requireAuth(req, res);
                if (!user) {
                    return;
                }
                const appId = nodeDetailMatch[1];
                const nodeId = nodeDetailMatch[2];
                const node = state.nodes.get(nodeId);
                if (!node || node.application_id !== appId) {
                    sendJsonWithCors(res, 404, { detail: 'Node not found' });
                    return;
                }
                sendJsonWithCors(res, 200, {
                    id: node.id,
                    application_id: node.application_id,
                    parent_id: node.parent_id,
                    path: node.path,
                    container: node.container,
                    metadata_: node.metadata_,
                    created_at: node.created_at,
                    updated_at: node.updated_at,
                });
                return;
            }

            const pendingRequestsMatch = path.match(/^\/api\/v1\/apps\/([^/]+)\/pending-requests$/);
            if (req.method === 'GET' && pendingRequestsMatch) {
                const user = requireAuth(req, res);
                if (!user) {
                    return;
                }
                const appId = pendingRequestsMatch[1];

                if (!canManageAppRequests(user, appId)) {
                    sendJsonWithCors(res, 403, { detail: 'Not authorized' });
                    return;
                }

                const pending = [...state.accessRequests.values()].filter(
                    (entry) => entry.application_id === appId && entry.status === 'pending',
                );
                sendJsonWithCors(res, 200, pending);
                return;
            }

            const approveMatch = path.match(/^\/api\/v1\/apps\/([^/]+)\/requests\/([^/]+)\/approve$/);
            if (req.method === 'POST' && approveMatch) {
                const user = requireAuth(req, res);
                if (!user) {
                    return;
                }
                const appId = approveMatch[1];
                const requestId = approveMatch[2];

                if (!canManageAppRequests(user, appId)) {
                    sendJsonWithCors(res, 403, { detail: 'Not authorized' });
                    return;
                }

                const requestEntry = state.accessRequests.get(requestId);
                if (!requestEntry || requestEntry.application_id !== appId) {
                    sendJsonWithCors(res, 404, { detail: 'Request not found' });
                    return;
                }
                if (requestEntry.status !== 'pending') {
                    sendJsonWithCors(res, 400, { detail: 'Request already processed' });
                    return;
                }
                requestEntry.status = 'approved';
                requestEntry.resolved_at = nowIso();
                requestEntry.resolved_by = user.id;

                const approvalPayload = await readJsonBody<{ role?: 'app_admin' | 'app_user' }>(req);
                const grantedRole = approvalPayload.role ?? 'app_user';
                const permissionId = randomUUID();
                state.appPermissions.set(permissionId, {
                    id: permissionId,
                    user_id: requestEntry.user_id,
                    application_id: appId,
                    role: grantedRole,
                    created_at: nowIso(),
                });

                sendJsonWithCors(res, 200, { message: 'Access granted' });
                return;
            }

            const rejectMatch = path.match(/^\/api\/v1\/apps\/([^/]+)\/requests\/([^/]+)\/reject$/);
            if (req.method === 'POST' && rejectMatch) {
                const user = requireAuth(req, res);
                if (!user) {
                    return;
                }
                const appId = rejectMatch[1];
                const requestId = rejectMatch[2];

                if (!canManageAppRequests(user, appId)) {
                    sendJsonWithCors(res, 403, { detail: 'Not authorized' });
                    return;
                }

                const requestEntry = state.accessRequests.get(requestId);
                if (!requestEntry || requestEntry.application_id !== appId) {
                    sendJsonWithCors(res, 404, { detail: 'Request not found' });
                    return;
                }
                if (requestEntry.status !== 'pending') {
                    sendJsonWithCors(res, 400, { detail: 'Request already processed' });
                    return;
                }
                requestEntry.status = 'rejected';
                requestEntry.resolved_at = nowIso();
                requestEntry.resolved_by = user.id;
                sendJsonWithCors(res, 200, { message: 'Access denied' });
                return;
            }

            const workflowMatch = path.match(/^\/(api\/v1\/)?execution\/workflow\/([^/]+)$/);
            if (req.method === 'POST' && workflowMatch) {
                const user = requireAuth(req, res);
                if (!user) {
                    return;
                }
                const workflowName = workflowMatch[2];
                const payload = await readJsonBody<Record<string, unknown>>(req);
                sendJsonWithCors(res, 200, {
                    success: true,
                    workflow: workflowName,
                    executed_by: user.username,
                    input: payload,
                    timestamp: nowIso(),
                    result: {
                        status: 'ok',
                        message: `Workflow ${workflowName} executed in compatibility mode`,
                    },
                });
                return;
            }

            if (req.method === 'POST' && req.url === '/objects') {
                const payload = await readJsonBody<ObjectPayload>(req);
                db.upsertObject({
                    id: payload.id,
                    shape: payload.shape,
                    properties: payload.properties ?? {},
                });
                sendJsonWithCors(res, 201, { id: payload.id, stored: true });
                return;
            }

            if (req.method === 'POST' && req.url === '/morphisms') {
                const payload = await readJsonBody<MorphismPayload>(req);
                db.upsertMorphism({
                    id: payload.id,
                    source: payload.source,
                    target: payload.target,
                    container: makeContainer(payload.id, {
                        inputs: payload.source.inputs,
                        outputs: payload.target.outputs,
                    }),
                    properties: payload.properties ?? {},
                });
                sendJsonWithCors(res, 201, { id: payload.id, stored: true });
                return;
            }

            if (req.method === 'GET' && req.url?.startsWith('/morphisms')) {
                sendJsonWithCors(res, 200, { ids: db.listMorphismIds() });
                return;
            }

            if (req.method === 'POST' && req.url === '/morphisms/query') {
                const payload = await readJsonBody<MorphismQueryPayload>(req);
                const matches = db.findMorphismsByInterface(payload.source, payload.target);
                sendJsonWithCors(res, 200, {
                    ids: matches.map((entry) => entry.id),
                });
                return;
            }

            if (req.method === 'POST' && req.url === '/compose') {
                const payload = await readJsonBody<{ morphismIds: string[] }>(req);
                const composition = db.composeMorphismChain(payload.morphismIds ?? []);
                sendJsonWithCors(res, 200, {
                    valid: composition.valid,
                    missingIds: composition.missingIds,
                    composedId: composition.container.id,
                    inputs: composition.container.interface.inputs,
                    outputs: composition.container.interface.outputs,
                    wiringCount: composition.container.wiring.length,
                });
                return;
            }

            if (req.method === 'POST' && req.url === '/bootstrap') {
                const payload = await readJsonBody<{ morphismIds: string[]; system?: string }>(req);
                const context = db.composeBootstrapContext(payload.morphismIds ?? [], payload.system);
                sendJsonWithCors(res, 200, context);
                return;
            }

            sendJsonWithCors(res, 404, { error: 'not_found' });
        } catch (error) {
            sendJsonWithCors(res, 500, {
                error: 'internal_error',
                message: error instanceof Error ? error.message : 'unknown',
            });
        }
    });
};

export interface SessionRecord {
    session_id: string;
    app_id: string;
    role: string;
    node_ids: string[];
    created_at: string;
    model?: string;
    label?: string;
}

export const createAgentCompatServer = (sessionStore: Map<string, SessionRecord>) => {
    const sendJsonWithCors = (res: ServerResponse, statusCode: number, body: unknown): void => {
        res.statusCode = statusCode;
        res.setHeader('content-type', 'application/json');
        res.setHeader('access-control-allow-origin', '*');
        res.setHeader('access-control-allow-methods', 'GET,POST,PATCH,DELETE,OPTIONS');
        res.setHeader('access-control-allow-headers', 'Content-Type,Authorization');
        res.end(JSON.stringify(body));
    };

    const resolvePath = (req: IncomingMessage): string => {
        const url = req.url ?? '/';
        return url.split('?')[0] ?? '/';
    };

    return createServer(async (req, res) => {
        try {
            const path = resolvePath(req);

            if (req.method === 'OPTIONS') {
                sendJsonWithCors(res, 204, {});
                return;
            }

            if (req.method === 'GET' && path === '/health') {
                sendJsonWithCors(res, 200, { status: 'ok', service: 'agent-compat' });
                return;
            }

            if (req.method === 'POST' && path === '/agent/session') {
                const payload = await readJsonBody<{
                    role?: string;
                    app_id?: string;
                    node_ids?: string[];
                    model?: string;
                    label?: string;
                }>(req);

                const session_id = randomUUID();
                const role = payload.role ?? 'app_user';
                const app_id = payload.app_id ?? '';
                const node_ids = Array.isArray(payload.node_ids) ? payload.node_ids : [];
                const wsBase = process.env.NANOCLAW_WS_URL ?? 'ws://localhost:18789';

                sessionStore.set(session_id, {
                    session_id,
                    app_id,
                    role,
                    node_ids,
                    created_at: nowIso(),
                    model: payload.model,
                    label: payload.label,
                });

                sendJsonWithCors(res, 200, {
                    session_id,
                    nanoclaw_ws_url: wsBase,
                    preview: {
                        node_count: node_ids.length,
                        skill_count: 0,
                        tool_count: 0,
                        role,
                        vector_matches: 0,
                    },
                });
                return;
            }

            if (req.method === 'POST' && path === '/agent/root/session') {
                const payload = await readJsonBody<{ app_id?: string }>(req);
                const session_id = randomUUID();
                const wsBase = process.env.NANOCLAW_WS_URL ?? 'ws://localhost:18789';

                sessionStore.set(session_id, {
                    session_id,
                    app_id: payload.app_id ?? '',
                    role: 'superadmin',
                    node_ids: [],
                    created_at: nowIso(),
                });

                sendJsonWithCors(res, 200, {
                    session_id,
                    nanoclaw_ws_url: wsBase,
                    preview: {
                        node_count: 0,
                        skill_count: 0,
                        tool_count: 0,
                        role: 'superadmin',
                        vector_matches: 0,
                    },
                });
                return;
            }

            sendJsonWithCors(res, 404, { error: 'not_found' });
        } catch (error) {
            sendJsonWithCors(res, 500, {
                error: 'internal_error',
                message: error instanceof Error ? error.message : 'unknown',
            });
        }
    });
};

export const createNanoClawCompatBridge = (sessionStore: Map<string, SessionRecord>) => {
    const server = createServer((req, res) => {
        if (req.url === '/health' && req.method === 'GET') {
            res.statusCode = 200;
            res.setHeader('content-type', 'application/json');
            res.end(JSON.stringify({ status: 'ok', service: 'nanoclaw-compat' }));
            return;
        }
        res.statusCode = 404;
        res.end('not_found');
    });

    const wss = new WebSocketServer({ server });

    const sendResponse = (
        ws: WebSocket,
        id: string | number | null,
        result?: unknown,
        error?: { message: string; code?: number },
    ) => {
        ws.send(
            JSON.stringify({
                type: 'response',
                id,
                ...(error ? { error } : { result }),
            }),
        );
    };

    const sendEvent = (ws: WebSocket, event: string, payload: Record<string, unknown> = {}) => {
        ws.send(
            JSON.stringify({
                type: 'event',
                event,
                ...payload,
            }),
        );
    };

    wss.on('connection', (ws: WebSocket) => {
        ws.on('message', (buffer: Buffer) => {
            try {
                const raw = JSON.parse(buffer.toString()) as Record<string, unknown>;

                const isBridgeRequest = raw.type === 'request' && typeof raw.method === 'string';
                const isJsonRpcRequest = typeof raw.method === 'string' && raw.params !== undefined;

                if (!isBridgeRequest && !isJsonRpcRequest) {
                    sendResponse(ws, null, undefined, { message: 'Invalid request frame' });
                    return;
                }

                const id = (raw.id as string | number | null | undefined) ?? null;
                const method = raw.method as string;
                const params = (raw.params as Record<string, unknown> | undefined) ?? {};

                if (method === 'sessions.list') {
                    const limit =
                        typeof params.limit === 'number' && Number.isFinite(params.limit)
                            ? Math.max(1, Math.min(200, Math.trunc(params.limit)))
                            : 50;
                    sendResponse(ws, id, [...sessionStore.values()].slice(0, limit));
                    return;
                }

                if (method === 'sessions.patch') {
                    const sessionKey = typeof params.sessionKey === 'string' ? params.sessionKey : '';
                    if (!sessionKey || !sessionStore.has(sessionKey)) {
                        sendResponse(ws, id, undefined, { message: `Session not found: ${sessionKey}` });
                        return;
                    }

                    const existing = sessionStore.get(sessionKey)!;
                    const updated: SessionRecord = {
                        ...existing,
                        model: typeof params.model === 'string' ? params.model : existing.model,
                        label: typeof params.label === 'string' ? params.label : existing.label,
                    };
                    sessionStore.set(sessionKey, updated);
                    sendResponse(ws, id, updated);
                    return;
                }

                if (method === 'sessions.send' || method === 'agent.request') {
                    const text = typeof params.message === 'string' ? params.message : '';
                    if (text.trim().length === 0) {
                        sendResponse(ws, id, undefined, { message: 'Missing required param: message' });
                        sendEvent(ws, 'error', { message: 'Missing required param: message' });
                        return;
                    }

                    const sessionKey =
                        typeof params.sessionKey === 'string' && params.sessionKey.length > 0
                            ? params.sessionKey
                            : randomUUID();

                    if (!sessionStore.has(sessionKey)) {
                        sessionStore.set(sessionKey, {
                            session_id: sessionKey,
                            app_id: typeof params.appId === 'string' ? params.appId : '',
                            role: typeof params.role === 'string' ? params.role : 'app_user',
                            node_ids: Array.isArray(params.nodeIds)
                                ? params.nodeIds.filter((value): value is string => typeof value === 'string')
                                : [],
                            created_at: nowIso(),
                            model: typeof params.model === 'string' ? params.model : undefined,
                        });
                    }

                    sendResponse(ws, id, { status: 'streaming', sessionKey });
                    sendEvent(ws, 'thinking', { data: 'Processing request in MOOS compatibility mode' });
                    sendEvent(ws, 'tool_use_start', {
                        data: {
                            name: 'compat_echo_tool',
                            args: JSON.stringify({ message: text }),
                        },
                    });
                    sendEvent(ws, 'tool_result', {
                        data: {
                            name: 'compat_echo_tool',
                            result: JSON.stringify({ echoed: text }),
                        },
                    });
                    sendEvent(ws, 'text_delta', { data: `MOOS: ${text}` });
                    sendEvent(ws, 'message_end');
                    return;
                }

                sendResponse(ws, id, undefined, { message: `Unknown method: ${method}` });
            } catch {
                sendResponse(ws, null, undefined, { message: 'Failed to parse message' });
            }
        });
    });

    return server;
};

const server = createDataServer();
const sessionStore = new Map<string, SessionRecord>();
const agentCompatServer = createAgentCompatServer(sessionStore);
const nanoclawCompatServer = createNanoClawCompatBridge(sessionStore);

if (process.env.NODE_ENV !== 'test') {
    server.listen(port, () => {
        console.log(`[moos-data-server] listening on :${port}`);
    });

    const agentPort = Number(process.env.AGENT_COMPAT_PORT ?? 8004);
    agentCompatServer.listen(agentPort, () => {
        console.log(`[moos-agent-compat] listening on :${agentPort}`);
    });

    const wsPort = Number(process.env.NANOCLAW_COMPAT_PORT ?? 18789);
    nanoclawCompatServer.listen(wsPort, () => {
        console.log(`[moos-nanoclaw-compat] listening on :${wsPort}`);
    });
}
