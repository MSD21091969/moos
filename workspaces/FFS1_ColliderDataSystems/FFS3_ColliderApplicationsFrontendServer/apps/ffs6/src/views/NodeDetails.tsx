import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import styles from './NodeDetails.module.css';

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

    if (loading) return <div className={styles.stateMessage}>Loading node details...</div>;
    if (error) return <div className={styles.stateError}>Error: {error}</div>;
    if (!node) return <div className={styles.stateMessage}>Node not found</div>;

    const isWorkflow = node.container?.species === 'workflow' || !!node.container?.workflows?.length;

    return (
        <div className={styles.container}>
            <h2 className={styles.title}>
                {node.path}
            </h2>

            <div className={styles.metaRowPrimary}>
                <strong>ID:</strong> <span className={styles.monoValue}>{node.id}</span>
            </div>

            <div className={styles.metaRowSecondary}>
                <strong>Species:</strong>
                <span className={styles.speciesBadge}>
                    {node.container?.species || 'generic'}
                </span>
            </div>

            {isWorkflow && (
                <div className={styles.workflowSection}>
                    <h3 className={styles.workflowTitle}>⚡ Workflow Actions</h3>
                    <p className={styles.workflowText}>
                        This node contains an executable workflow.
                    </p>
                    <button
                        onClick={handleExecute}
                        disabled={executing}
                        className={`${styles.executeButton} ${executing ? styles.executeButtonDisabled : styles.executeButtonEnabled}`}
                    >
                        {executing ? 'Executing...' : 'Run Workflow'}
                    </button>

                    {executionResult && (
                        <div className={styles.resultBox}>
                            <strong>Result:</strong>
                            <pre className={styles.resultPre}>
                                {JSON.stringify(executionResult, null, 2)}
                            </pre>
                        </div>
                    )}

                    {execError && (
                        <div className={styles.execErrorBox}>
                            <strong>Execution Error:</strong> {execError}
                        </div>
                    )}
                </div>
            )}

            <div className={styles.containerDataSection}>
                <h3>Container Data</h3>
                <pre className={styles.containerDataPre}>
                    {JSON.stringify(node.container, null, 2)}
                </pre>
            </div>
        </div>
    );
}
