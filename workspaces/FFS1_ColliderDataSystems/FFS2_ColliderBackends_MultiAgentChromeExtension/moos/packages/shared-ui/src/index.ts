import React from 'react';

type SurfaceDetail = {
    label: string;
    value: string;
};

type SurfaceShellProps = {
    product: string;
    title: string;
    subtitle: string;
    details: SurfaceDetail[];
};

type PeerDiagnostics = {
    link: string;
    ageLabel: string;
    health: string;
};

type SurfaceSyncApi = {
    getJourneyProbe: (morphismIds: string[]) => Promise<{
        status: string;
        health: string;
        compose: string;
        bootstrap: string;
    }>;
    getDataServerHealth: () => Promise<{ status: string }>;
    getBootstrapPreview: (morphismIds: string[]) => Promise<{
        status: string;
        messageCount: number;
    }>;
};

type StartSurfaceSyncOptions = {
    selfSurface: string;
    selfStatus: string;
    phase: string;
    peerSurface: string;
    apiBaseUrl?: string;
    staleThresholdValue?: string;
    onPeerDiagnostics: (diagnostics: PeerDiagnostics) => void;
    buildApiStatus: (api: SurfaceSyncApi) => Promise<string>;
    onApiStatus: (status: string) => void;
};

const createApi = (apiBaseUrl?: string): SurfaceSyncApi => {
    const base = (apiBaseUrl && apiBaseUrl.trim().length > 0 ? apiBaseUrl : 'http://127.0.0.1:8000').replace(/\/$/, '');

    return {
        async getJourneyProbe() {
            try {
                const health = await fetch(`${base}/health`);
                return {
                    status: health.ok ? 'ok' : 'error',
                    health: health.ok ? 'ok' : 'error',
                    compose: 'n/a',
                    bootstrap: 'n/a',
                };
            } catch {
                return {
                    status: 'unavailable',
                    health: 'unavailable',
                    compose: 'unavailable',
                    bootstrap: 'unavailable',
                };
            }
        },

        async getDataServerHealth() {
            try {
                const response = await fetch(`${base}/health`);
                if (!response.ok) {
                    return { status: 'error' };
                }
                const payload = (await response.json()) as { status?: string };
                return { status: payload.status ?? 'ok' };
            } catch {
                return { status: 'unavailable' };
            }
        },

        async getBootstrapPreview(morphismIds: string[]) {
            try {
                const response = await fetch(`${base}/bootstrap`, {
                    method: 'POST',
                    headers: { 'content-type': 'application/json' },
                    body: JSON.stringify({ morphismIds, system: 'surface-sync' }),
                });
                if (!response.ok) {
                    return { status: 'error', messageCount: 0 };
                }
                const payload = (await response.json()) as { messages?: unknown[] };
                return {
                    status: 'ok',
                    messageCount: Array.isArray(payload.messages) ? payload.messages.length : 0,
                };
            } catch {
                return { status: 'unavailable', messageCount: 0 };
            }
        },
    };
};

export const startSurfaceSync = (options: StartSurfaceSyncOptions): (() => void) => {
    const staleThresholdSeconds = Number(options.staleThresholdValue ?? 30);
    const safeThreshold = Number.isFinite(staleThresholdSeconds) && staleThresholdSeconds > 0 ? staleThresholdSeconds : 30;
    const startedAt = Date.now();
    const api = createApi(options.apiBaseUrl);

    const tick = async (): Promise<void> => {
        const ageSeconds = Math.floor((Date.now() - startedAt) / 1000);
        options.onPeerDiagnostics({
            link: 'online',
            ageLabel: `${ageSeconds}s`,
            health: ageSeconds > safeThreshold ? 'stale' : 'fresh',
        });

        try {
            const status = await options.buildApiStatus(api);
            options.onApiStatus(status);
        } catch {
            options.onApiStatus('unavailable');
        }
    };

    void tick();
    const timer = setInterval(() => {
        void tick();
    }, 4000);

    return () => {
        clearInterval(timer);
    };
};

export const SurfaceShell = ({ product, title, subtitle, details }: SurfaceShellProps): React.ReactElement => {
    return React.createElement(
        'div',
        {
            style: {
                fontFamily: 'system-ui, sans-serif',
                padding: '20px',
                color: '#111827',
            },
        },
        React.createElement('div', { style: { fontSize: '12px', color: '#6b7280', textTransform: 'uppercase' } }, product),
        React.createElement('h1', { style: { margin: '8px 0 4px 0', fontSize: '22px' } }, title),
        React.createElement('p', { style: { margin: '0 0 16px 0', color: '#4b5563' } }, subtitle),
        React.createElement(
            'div',
            {
                style: {
                    display: 'grid',
                    gap: '8px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    padding: '12px',
                    background: '#f9fafb',
                },
            },
            ...details.map((detail) =>
                React.createElement(
                    'div',
                    {
                        key: detail.label,
                        style: {
                            display: 'flex',
                            justifyContent: 'space-between',
                            gap: '12px',
                            fontSize: '13px',
                        },
                    },
                    React.createElement('span', { style: { color: '#6b7280' } }, detail.label),
                    React.createElement('span', { style: { fontWeight: 600 } }, detail.value),
                ),
            ),
        ),
    );
};
