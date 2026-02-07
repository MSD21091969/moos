/**
 * NodeContainer Component
 *
 * A React component that renders the content for a node in the Collider system.
 * Handles automatic context loading via SSE streaming.
 */
import React, { useEffect } from 'react';
import { useContainer } from './use-container';
import { useSSE, type SSEEvent } from './use-sse';
import styles from './node-container.module.css';

export interface NodeContainerProps {
  /** Application ID */
  appId: string;
  /** Node path (e.g., "/dashboard") */
  nodePath: string;
  /** API base URL */
  apiBaseUrl?: string;
  /** Authorization token */
  token?: string;
  /** Children to render with container context */
  children?: React.ReactNode | ((ctx: NodeContainerContext) => React.ReactNode);
  /** Loading component */
  loading?: React.ReactNode;
  /** Error component */
  error?: (error: Error) => React.ReactNode;
  /** Enable SSE streaming for real-time updates */
  enableStreaming?: boolean;
  /** Custom className */
  className?: string;
}

export interface NodeContainerContext {
  /** The resolved container data with inheritance applied */
  container: ResolvedContainer | null;
  /** Loading state */
  isLoading: boolean;
  /** Error state */
  error: Error | null;
  /** Refetch container data */
  refetch: () => void;
  /** SSE connection status */
  streamingStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
  /** Last SSE event */
  lastEvent: SSEEvent | null;
}

export interface ResolvedContainer {
  manifest: Record<string, unknown>;
  instructions: string[];
  rules: string[];
  skills: string[];
  tools: ToolDefinition[];
  knowledge: string[];
  workflows: WorkflowDefinition[];
  configs: Record<string, unknown>;
}

export interface ToolDefinition {
  id: string;
  name: string;
  description?: string;
  parameters?: Record<string, unknown>;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description?: string;
  steps: unknown[];
}

/**
 * NodeContainer - Main component for rendering node content
 */
export function NodeContainer({
  appId,
  nodePath,
  apiBaseUrl = 'http://localhost:8000/api/v1',
  token,
  children,
  loading = <DefaultLoading />,
  error: errorComponent,
  enableStreaming = false,
  className,
}: NodeContainerProps): React.ReactElement {
  const containerState = useContainer({
    appId,
    nodePath,
    apiBaseUrl,
    token,
  });

  const sseState = useSSE({
    url: enableStreaming ? `${apiBaseUrl}/sse/subscribe?app_id=${appId}&path=${encodeURIComponent(nodePath)}` : null,
    token,
  });

  // Combine into context
  const context: NodeContainerContext = {
    container: containerState.container,
    isLoading: containerState.isLoading,
    error: containerState.error,
    refetch: containerState.refetch,
    streamingStatus: sseState.status,
    lastEvent: sseState.lastEvent,
  };

  // Refetch when SSE update event is received
  useEffect(() => {
    if (sseState.lastEvent?.type === 'container_updated') {
      containerState.refetch();
    }
  }, [sseState.lastEvent, containerState]);

  // Render states
  if (containerState.isLoading) {
    return <div className={className}>{loading}</div>;
  }

  if (containerState.error) {
    return (
      <div className={className}>
        {errorComponent ? (
          errorComponent(containerState.error)
        ) : (
          <DefaultError error={containerState.error} />
        )}
      </div>
    );
  }

  // Render children with context
  return (
    <div className={`${styles['container']} ${className || ''}`} data-node-path={nodePath} data-app-id={appId}>
      {typeof children === 'function' ? children(context) : children}
    </div>
  );
}

// Default loading component
function DefaultLoading(): React.ReactElement {
  return (
    <div className={styles['loading']}>
      <div className={styles['spinner']} />
      <p>Loading container...</p>
    </div>
  );
}

// Default error component
function DefaultError({ error }: { error: Error }): React.ReactElement {
  return (
    <div className={styles['error']}>
      <h3>Error Loading Container</h3>
      <p>{error.message}</p>
    </div>
  );
}

export default NodeContainer;
