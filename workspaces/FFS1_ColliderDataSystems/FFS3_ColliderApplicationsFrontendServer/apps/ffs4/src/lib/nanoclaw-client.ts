/**
 * NanoClaw WebSocket RPC Client
 *
 * JSON-RPC over WebSocket for communicating with NanoClawBridge.
 * Ported from Chrome extension's nanoclaw-rpc.ts.
 */

type AgentEvent =
  | { kind: "text_delta"; text: string }
  | { kind: "tool_use_start"; name: string; args: string }
  | { kind: "tool_result"; name: string; result: string }
  | { kind: "thinking"; text: string }
  | { kind: "message_end" }
  | { kind: "error"; message: string };

type EventListener = (event: AgentEvent) => void;

export class NanoClawRpcClient {
  private ws: WebSocket | null = null;
  private url: string;
  private nextId = 1;
  private pending = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();
  private eventListeners = new Set<EventListener>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(url: string) {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => resolve();
      this.ws.onerror = (e) => reject(new Error("WebSocket error"));

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);

          // JSON-RPC response
          if (msg.id && this.pending.has(msg.id)) {
            const { resolve, reject } = this.pending.get(msg.id)!;
            this.pending.delete(msg.id);
            if (msg.error) {
              reject(new Error(msg.error.message ?? "RPC error"));
            } else {
              resolve(msg.result);
            }
            return;
          }

          // Notification (agent event stream)
          if (msg.method === "agent.event" && msg.params) {
            const agentEvent = msg.params as AgentEvent;
            for (const listener of this.eventListeners) {
              listener(agentEvent);
            }
          }
        } catch {
          // Ignore parse errors
        }
      };

      this.ws.onclose = () => {
        // Auto-reconnect after 3s
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
      };
    });
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }

  onAgentEvent(listener: EventListener): () => void {
    this.eventListeners.add(listener);
    return () => this.eventListeners.delete(listener);
  }

  async agentRequest(
    message: string,
    opts?: { sessionKey?: string; model?: string; workspaceDir?: string },
  ): Promise<void> {
    await this.rpc("agent.request", {
      message,
      sessionKey: opts?.sessionKey,
      model: opts?.model,
      workspaceDir: opts?.workspaceDir,
    });
  }

  async sessionsList(): Promise<unknown[]> {
    return (await this.rpc("sessions.list", {})) as unknown[];
  }

  async sessionsPatch(
    sessionKey: string,
    settings: { model?: string; label?: string },
  ): Promise<unknown> {
    return this.rpc("sessions.patch", { sessionKey, ...settings });
  }

  private rpc(method: string, params: Record<string, unknown>): Promise<unknown> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error("WebSocket not connected"));
        return;
      }

      const id = this.nextId++;
      this.pending.set(id, { resolve, reject });

      this.ws.send(
        JSON.stringify({ jsonrpc: "2.0", id, method, params }),
      );

      // Timeout after 120s
      setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new Error("RPC timeout"));
        }
      }, 120_000);
    });
  }
}
