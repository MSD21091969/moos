/**
 * NanoClawBridge JSON-RPC WebSocket Client
 *
 * Connects to NanoClawBridge at ws://127.0.0.1:18789 using its JSON-RPC
 * protocol. Supports:
 *   - agent.request  → trigger an agent run with streaming events
 *   - sessions.patch → update session settings (model, thinking, etc.)
 *   - sessions.list  → list active sessions
 *
 * The Bridge protocol uses JSON frames with { type, id, method, params }
 * for requests and { type, id, result, error } for responses, plus
 * streaming events for agent runs.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Outbound JSON-RPC request */
interface RpcRequest {
  type: "request";
  id: string;
  method: string;
  params: Record<string, unknown>;
}

/** Inbound JSON-RPC response */
interface RpcResponse {
  type: "response";
  id: string;
  result?: unknown;
  error?: { message: string; code?: number };
}

/** Streaming events from agent.request */
export type AgentEvent =
  | { kind: "text_delta"; text: string }
  | { kind: "tool_use_start"; name: string; args: string }
  | { kind: "tool_result"; name: string; result: string }
  | { kind: "thinking"; text: string }
  | { kind: "message_end" }
  | { kind: "error"; message: string };

/** Connection state */
export type ConnectionState = "disconnected" | "connecting" | "connected" | "error";

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export class NanoClawRpcClient {
  private ws: WebSocket | null = null;
  private pendingRequests = new Map<string, {
    resolve: (value: unknown) => void;
    reject: (reason: Error) => void;
  }>();
  private eventListeners: ((event: AgentEvent) => void)[] = [];
  private reqCounter = 0;
  private _state: ConnectionState = "disconnected";

  constructor(private readonly wsUrl: string) { }

  get state(): ConnectionState {
    return this._state;
  }

  /** Connect to the NanoClawBridge WebSocket. */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this._state = "connecting";
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        this._state = "connected";
        resolve();
      };

      this.ws.onerror = () => {
        this._state = "error";
        reject(new Error(`Failed to connect to NanoClawBridge at ${this.wsUrl}`));
      };

      this.ws.onclose = () => {
        this._state = "disconnected";
        // Reject any pending requests
        for (const [, pending] of this.pendingRequests) {
          pending.reject(new Error("WebSocket closed"));
        }
        this.pendingRequests.clear();
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event);
      };
    });
  }

  /** Close the WebSocket connection. */
  close(): void {
    this.eventListeners = [];
    this.ws?.close();
    this.ws = null;
    this._state = "disconnected";
  }

  /** Subscribe to streaming agent events. Returns unsubscribe function. */
  onAgentEvent(listener: (event: AgentEvent) => void): () => void {
    this.eventListeners.push(listener);
    return () => {
      this.eventListeners = this.eventListeners.filter((l) => l !== listener);
    };
  }

  /**
   * Send a message to trigger an agent run.
   * Streaming events arrive via onAgentEvent listeners.
   * Returns the RPC response (acknowledgement).
   */
  async agentRequest(
    message: string,
    opts?: { sessionKey?: string; model?: string },
  ): Promise<unknown> {
    const params: Record<string, unknown> = { message };
    if (opts?.sessionKey) params.sessionKey = opts.sessionKey;
    if (opts?.model) params.model = opts.model;
    return this.rpc("agent.request", params);
  }

  /** List active sessions. */
  async sessionsList(opts?: {
    kinds?: string[];
    limit?: number;
    activeMinutes?: number;
  }): Promise<unknown> {
    return this.rpc("sessions.list", opts ?? {});
  }

  /** Patch session settings. */
  async sessionsPatch(
    sessionKey: string,
    settings: Record<string, unknown>,
  ): Promise<unknown> {
    return this.rpc("sessions.patch", { sessionKey, ...settings });
  }

  /** Send a message to another session. */
  async sessionsSend(
    sessionKey: string,
    message: string,
    timeoutSeconds?: number,
  ): Promise<unknown> {
    return this.rpc("sessions.send", {
      sessionKey,
      message,
      timeoutSeconds: timeoutSeconds ?? 0,
    });
  }

  // ---------------------------------------------------------------------------
  // Private
  // ---------------------------------------------------------------------------

  private nextId(): string {
    return `rpc-${++this.reqCounter}-${Date.now()}`;
  }

  private rpc(method: string, params: Record<string, unknown>): Promise<unknown> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error("WebSocket not connected"));
        return;
      }

      const id = this.nextId();
      const request: RpcRequest = { type: "request", id, method, params };

      this.pendingRequests.set(id, { resolve, reject });
      this.ws.send(JSON.stringify(request));

      // Timeout after 120s
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error(`RPC timeout: ${method}`));
        }
      }, 120_000);
    });
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data as string) as Record<string, unknown>;
      const type = data.type as string;

      if (type === "response") {
        this.handleResponse(data as unknown as RpcResponse);
      } else if (type === "event") {
        this.handleEvent(data);
      }
      // Ignore other frame types (keepalive, etc.)
    } catch {
      // Ignore parse errors
    }
  }

  private handleResponse(response: RpcResponse): void {
    const pending = this.pendingRequests.get(response.id);
    if (!pending) return;

    this.pendingRequests.delete(response.id);
    if (response.error) {
      pending.reject(new Error(response.error.message));
    } else {
      pending.resolve(response.result);
    }
  }

  private handleEvent(data: Record<string, unknown>): void {
    const eventType = data.event as string;
    let agentEvent: AgentEvent;

    switch (eventType) {
      case "text_delta":
      case "textDelta":
        agentEvent = {
          kind: "text_delta",
          text: (data.data as string) ?? (data.text as string) ?? "",
        };
        break;

      case "tool_use_start":
      case "toolUseStart": {
        const toolData = data.data as Record<string, string> | undefined;
        agentEvent = {
          kind: "tool_use_start",
          name: toolData?.name ?? (data.name as string) ?? "",
          args: toolData?.args ?? (data.args as string) ?? "",
        };
        break;
      }

      case "tool_result":
      case "toolResult": {
        const resultData = data.data as Record<string, string> | undefined;
        agentEvent = {
          kind: "tool_result",
          name: resultData?.name ?? (data.name as string) ?? "",
          result: resultData?.result ?? (data.result as string) ?? "",
        };
        break;
      }

      case "thinking":
        agentEvent = {
          kind: "thinking",
          text: (data.data as string) ?? (data.text as string) ?? "",
        };
        break;

      case "message_end":
      case "messageEnd":
      case "done":
      case "end":
        agentEvent = { kind: "message_end" };
        break;

      case "error":
        agentEvent = {
          kind: "error",
          message: (data.message as string) ?? (data.data as string) ?? "Unknown error",
        };
        break;

      default:
        // Unknown event type — skip
        return;
    }

    for (const listener of this.eventListeners) {
      listener(agentEvent);
    }
  }
}
