import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

interface NodeDetailsProps {
    appId: string;
}

export function NodeDetails({ appId }: NodeDetailsProps) {
    const { id } = useParams<{ id: string }>();
    const [node, setNode] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [executing, setExecuting] = useState(false);
    const [executionResult, setExecutionResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [execError, setExecError] = useState<string | null>(null);

    useEffect(() => {
        if (!id || !appId) return;
        
        const fetchNode = async () => {
            setLoading(true);
            setError(null);
            setExecutionResult(null);
            try {
                const token = localStorage.getItem('auth_token');
                const res = await fetch(`/api/v1/apps/${appId}/nodes/${id}`, {
                    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
                });
                if (!res.ok) throw new Error(`Failed to fetch node: ${res.statusText}`);
                const data = await res.json();
                setNode(data);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchNode();
    }, [id, appId]);

    const handleExecute = async () => {
        if (!node) return;
        setExecuting(true);
        setExecutionResult(null);
        setExecError(null);

        try {
            // Workflow name usually resides in container.name or container.manifest.name
            // For MVP we assume container.name or we use the node path leaf if missing
            // Adjust based on your WorkflowDefinition schema
            const workflowName = node.container?.name || node.path.split('/').pop();
            
            const token = localStorage.getItem('auth_token');
            const res = await fetch(`/api/v1/execution/workflow/${workflowName}`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({ input: {} }) // Empty input for now
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Execution failed');
            }

            const data = await res.json();
            setExecutionResult(data);
        } catch (err: any) {
            setExecError(err.message);
        } finally {
            setExecuting(false);
        }
    };

    if (loading) return <div style={{ padding: '20px' }}>Loading node details...</div>;
    if (error) return <div style={{ padding: '20px', color: 'red' }}>Error: {error}</div>;
    if (!node) return <div style={{ padding: '20px' }}>Node not found</div>;

    const isWorkflow = node.container?.species === 'workflow' || !!node.container?.workflows?.length;

    return (
        <div style={{ padding: '24px', maxWidth: '800px' }}>
            <h2 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                {node.path}
            </h2>

            <div style={{ marginTop: '20px' }}>
                <strong>ID:</strong> <span style={{ fontFamily: 'monospace', color: '#666' }}>{node.id}</span>
            </div>
            
            <div style={{ marginTop: '10px' }}>
                <strong>Species:</strong> 
                <span style={{ 
                    marginLeft: '8px',
                    padding: '2px 6px', 
                    backgroundColor: '#e0e7ff', 
                    color: '#3730a3', 
                    borderRadius: '4px',
                    fontSize: '14px'
                }}>
                    {node.container?.species || 'generic'}
                </span>
            </div>

            {isWorkflow && (
                <div style={{ marginTop: '24px', padding: '16px', backgroundColor: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
                    <h3 style={{ marginTop: 0, color: '#166534' }}>⚡ Workflow Actions</h3>
                    <p style={{ fontSize: '14px', color: '#15803d' }}>
                        This node contains an executable workflow.
                    </p>
                    <button 
                        onClick={handleExecute}
                        disabled={executing}
                        style={{
                            padding: '8px 16px',
                            backgroundColor: executing ? '#9ca3af' : '#16a34a',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: executing ? 'not-allowed' : 'pointer',
                            fontWeight: 'bold'
                        }}
                    >
                        {executing ? 'Executing...' : 'Run Workflow'}
                    </button>

                    {executionResult && (
                        <div style={{ marginTop: '16px', backgroundColor: 'white', padding: '12px', borderRadius: '4px', border: '1px solid #ddd' }}>
                            <strong>Result:</strong>
                            <pre style={{ 
                                marginTop: '8px', 
                                backgroundColor: '#f8fafc', 
                                padding: '8px', 
                                borderRadius: '4px',
                                overflow: 'auto',
                                maxHeight: '200px'
                            }}>
                                {JSON.stringify(executionResult, null, 2)}
                            </pre>
                        </div>
                    )}

                    {execError && (
                        <div style={{ marginTop: '16px', backgroundColor: '#fef2f2', padding: '12px', borderRadius: '4px', border: '1px solid #fca5a5', color: '#991b1b' }}>
                            <strong>Execution Error:</strong> {execError}
                        </div>
                    )}
                </div>
            )}

            <div style={{ marginTop: '30px' }}>
                <h3>Container Data</h3>
                <pre style={{ 
                    backgroundColor: '#f8fafc', 
                    padding: '16px', 
                    borderRadius: '8px', 
                    overflow: 'auto',
                    fontSize: '12px',
                    border: '1px solid #e2e8f0'
                }}>
                    {JSON.stringify(node.container, null, 2)}
                </pre>
            </div>
        </div>
    );
}
