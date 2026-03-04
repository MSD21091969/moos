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
  | { kind: "morphism"; morphisms: unknown[] }
  | { kind: "active_state"; nodes?: unknown; edges?: unknown }
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

          const agentEvent = this.parseAgentEvent(msg);
          if (agentEvent) {
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
    opts?: {
      sessionKey?: string;
      model?: string;
      workspaceDir?: string;
      role?: string;
      appId?: string;
      nodeIds?: string[];
    },
  ): Promise<void> {
    await this.rpc("agent.request", {
      message,
      sessionKey: opts?.sessionKey,
      model: opts?.model,
      workspaceDir: opts?.workspaceDir,
      role: opts?.role,
      appId: opts?.appId,
      nodeIds: opts?.nodeIds,
    });
  }

  async sessionCreate(): Promise<{ session_id: string; root_urn?: string }> {
    return (await this.rpc("session.create", {})) as { session_id: string; root_urn?: string };
  }

  async sessionSend(sessionId: string, text: string): Promise<void> {
    await this.rpc("session.send", { session_id: sessionId, text });
  }

  async surfaceRegister(params: { surface_id: string; urn?: string; kind?: string; name?: string }): Promise<unknown> {
    return this.rpc("surface.register", params);
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

  private parseAgentEvent(msg: Record<string, unknown>): AgentEvent | null {
    // Legacy JSON-RPC notifications: { method: "agent.event", params: AgentEvent }
    if (msg.method === "agent.event" && msg.params && typeof msg.params === "object") {
      return msg.params as AgentEvent;
    }

    // Bridge event frames: { type: "event", event: "...", data?: ..., message?: ... }
    if (msg.type !== "event" || typeof msg.event !== "string") {
      if (typeof msg.method !== "string") {
        return null;
      }

      const method = msg.method;
      const params = (msg.params as Record<string, unknown> | undefined) ?? {};

      if (method === "stream.text_delta") {
        return { kind: "text_delta", text: typeof params.text === "string" ? params.text : "" };
      }
      if (method === "stream.thinking") {
        return { kind: "thinking", text: typeof params.text === "string" ? params.text : "" };
      }
      if (method === "stream.tool_result") {
        return {
          kind: "tool_result",
          name: typeof params.tool === "string" ? params.tool : "tool",
          result: typeof params.output === "string" ? params.output : JSON.stringify(params.output ?? ""),
        };
      }
      if (method === "stream.morphism" || method === "sync.active_state_delta") {
        const envelope = params.envelope;
        return { kind: "morphism", morphisms: envelope ? this.envelopeToGraphMorphisms(envelope) : [] };
      }
      if (method === "sync.active_state") {
        return { kind: "active_state", nodes: params.nodes, edges: params.edges };
      }
      if (method === "stream.end") {
        return { kind: "message_end" };
      }
      if (method === "stream.error") {
        return {
          kind: "error",
          message: typeof params.error === "string" ? params.error : "Unknown error",
        };
      }
      return null;
    }

    switch (msg.event) {
      case "text_delta":
        return {
          kind: "text_delta",
          text: typeof msg.data === "string" ? msg.data : "",
        };
      case "tool_use_start": {
        const data = (msg.data as Record<string, unknown> | undefined) ?? {};
        return {
          kind: "tool_use_start",
          name: typeof data.name === "string" ? data.name : "",
          args: typeof data.args === "string" ? data.args : JSON.stringify(data.args ?? ""),
        };
      }
      case "tool_result": {
        const data = (msg.data as Record<string, unknown> | undefined) ?? {};
        return {
          kind: "tool_result",
          name: typeof data.name === "string" ? data.name : "",
          result:
            typeof data.result === "string"
              ? data.result
              : JSON.stringify(data.result ?? ""),
        };
      }
      case "thinking":
        return {
          kind: "thinking",
          text: typeof msg.data === "string" ? msg.data : "",
        };
      case "morphism": {
        const data = (msg.data as Record<string, unknown> | undefined) ?? {};
        const morphisms = Array.isArray(data.morphisms) ? data.morphisms : [];
        return {
          kind: "morphism",
          morphisms,
        };
      }
      case "message_end":
        return { kind: "message_end" };
      case "error":
        return {
          kind: "error",
          message: typeof msg.message === "string" ? msg.message : "Unknown error",
        };
      default:
        return null;
    }
  }

  private envelopeToGraphMorphisms(envelope: unknown): unknown[] {
    if (!envelope || typeof envelope !== "object") {
      return [];
    }
    const value = envelope as Record<string, unknown>;
    const morphismType = typeof value.type === "string" ? value.type.toUpperCase() : "";

    if (morphismType === "ADD") {
      const add = (value.add as Record<string, unknown> | undefined) ?? {};
      const container = (add.container as Record<string, unknown> | undefined) ?? {};
      const urn = typeof container.URN === "string" ? container.URN : typeof container.urn === "string" ? container.urn : "";
      const kind = typeof container.Kind === "string" ? container.Kind : typeof container.kind === "string" ? container.kind : "data";
      if (!urn) return [];
      return [{ morphism_type: "ADD_NODE_CONTAINER", node_type: kind, temp_urn: urn, properties: {} }];
    }

    if (morphismType === "LINK") {
      const link = (value.link as Record<string, unknown> | undefined) ?? {};
      const wire = (link.wire as Record<string, unknown> | undefined) ?? {};
      const source = typeof wire.from_container_urn === "string" ? wire.from_container_urn : "";
      const target = typeof wire.to_container_urn === "string" ? wire.to_container_urn : "";
      if (!source || !target) return [];
      return [{ morphism_type: "LINK_NODES", source_urn: source, target_urn: target, edge_type: "wire" }];
    }

    if (morphismType === "MUTATE") {
      const mutate = (value.mutate as Record<string, unknown> | undefined) ?? {};
      const urn = typeof mutate.urn === "string" ? mutate.urn : "";
      const kernelData = (mutate.kernel_json as Record<string, unknown> | undefined) ?? {};
      if (!urn) return [];
      return [{ morphism_type: "UPDATE_NODE_KERNEL", urn, kernel_data: kernelData }];
    }

    if (morphismType === "UNLINK") {
      const unlink = (value.unlink as Record<string, unknown> | undefined) ?? {};
      const source = typeof unlink.source_urn === "string" ? unlink.source_urn : "";
      const target = typeof unlink.target_urn === "string" ? unlink.target_urn : "";
      if (!source || !target) return [];
      return [{ morphism_type: "DELETE_EDGE", source_urn: source, target_urn: target, edge_type: "wire" }];
    }

    return [];
  }
}
