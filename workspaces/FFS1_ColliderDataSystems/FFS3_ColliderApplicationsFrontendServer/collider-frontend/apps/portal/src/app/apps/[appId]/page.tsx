'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { NodeContainer } from '@collider-frontend/node-container';
import { api } from '../../api';
import { useAuth } from '../../AuthContext';
import type { Application, Node } from '@collider-frontend/api-client';

interface NodeInfo {
    path: string;
    display_name?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function AppDetailPage() {
    const params = useParams();
    const appId = params.appId as string;
    const { token } = useAuth();

    const [app, setApp] = useState<Application | null>(null);
    const [nodes, setNodes] = useState<NodeInfo[]>([]);
    const [selectedNode, setSelectedNode] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadApp() {
            try {
                const [appData, nodesData] = await Promise.all([
                    api.getApplication(appId),
                    api.getNodeTree(appId).catch(() => [] as Node[])
                ]);

                setApp(appData);

                const nodeList = nodesData.map((n: Node) => ({
                    path: n.path,
                    display_name: (n.node_metadata as Record<string, unknown>)?.display_name as string
                }));
                setNodes(nodeList);
                if (nodeList.length > 0) {
                    setSelectedNode(nodeList[0].path);
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load app');
            } finally {
                setLoading(false);
            }
        }

        if (appId) loadApp();
    }, [appId]);

    if (loading) {
        return <div style={{ padding: '2rem', background: '#1a1a2e', color: '#fff', minHeight: '100vh' }}>Loading...</div>;
    }

    if (error || !app) {
        return (
            <div style={{ padding: '2rem', background: '#1a1a2e', color: '#fff', minHeight: '100vh' }}>
                <p style={{ color: '#f87171' }}>{error || 'App not found'}</p>
                <Link href="/apps" style={{ color: '#3b82f6' }}>← Back to Apps</Link>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: '#1a1a2e', color: '#fff' }}>
            {/* Sidebar */}
            <aside style={{ width: '250px', borderRight: '1px solid rgba(255,255,255,0.1)', padding: '1rem' }}>
                <Link href="/apps" style={{ color: '#3b82f6', marginBottom: '1rem', display: 'block' }}>
                    ← All Apps
                </Link>

                <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>{app.display_name || app.app_id}</h2>
                <span style={{
                    display: 'inline-block',
                    padding: '0.25rem 0.5rem',
                    background: app.domain === 'FILESYST' ? '#22c55e' : app.domain === 'ADMIN' ? '#f97316' : '#3b82f6',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    marginBottom: '1rem'
                }}>
                    {app.domain || 'CLOUD'}
                </span>

                <h3 style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '0.5rem' }}>Nodes</h3>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                    {nodes.map(node => (
                        <li key={node.path}>
                            <button
                                onClick={() => setSelectedNode(node.path)}
                                style={{
                                    width: '100%',
                                    textAlign: 'left',
                                    padding: '0.5rem',
                                    background: selectedNode === node.path ? 'rgba(59,130,246,0.2)' : 'transparent',
                                    border: 'none',
                                    color: selectedNode === node.path ? '#3b82f6' : '#e2e8f0',
                                    cursor: 'pointer',
                                    borderRadius: '4px'
                                }}
                            >
                                {node.display_name || node.path}
                            </button>
                        </li>
                    ))}
                </ul>
            </aside>

            {/* Main content */}
            <main style={{ flex: 1, padding: '1rem' }}>
                {selectedNode ? (
                    <NodeContainer
                        appId={appId}
                        nodePath={selectedNode}
                        apiBaseUrl={`${API_BASE}/api/v1`}
                        token={token || undefined}
                        enableStreaming={true}
                    >
                        {(ctx) => (
                            <div style={{ padding: '1rem' }}>
                                <h3 style={{ marginBottom: '1rem' }}>Node: {selectedNode}</h3>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    marginBottom: '1rem',
                                    color: '#94a3b8',
                                    fontSize: '0.875rem'
                                }}>
                                    <span>SSE:</span>
                                    <span style={{
                                        padding: '0.125rem 0.5rem',
                                        borderRadius: '9999px',
                                        fontSize: '0.75rem',
                                        background: ctx.streamingStatus === 'connected' ? '#22c55e' :
                                                   ctx.streamingStatus === 'connecting' ? '#eab308' :
                                                   ctx.streamingStatus === 'error' ? '#ef4444' : '#64748b',
                                        color: '#fff'
                                    }}>
                                        {ctx.streamingStatus}
                                    </span>
                                </div>
                                {ctx.container && (
                                    <pre style={{
                                        padding: '1rem',
                                        background: 'rgba(0,0,0,0.3)',
                                        borderRadius: '8px',
                                        overflow: 'auto',
                                        fontSize: '0.75rem',
                                        color: '#e2e8f0'
                                    }}>
                                        {JSON.stringify(ctx.container, null, 2)}
                                    </pre>
                                )}
                            </div>
                        )}
                    </NodeContainer>
                ) : (
                    <div style={{ textAlign: 'center', color: '#64748b', marginTop: '4rem' }}>
                        Select a node to view its content
                    </div>
                )}
            </main>
        </div>
    );
}
