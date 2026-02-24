/**
 * SSE Context Subscriber
 *
 * Subscribes to DataServer's SSE endpoint for live NodeContainer
 * mutation events. When a node is updated, the subscriber emits
 * a ContextDelta that can be injected into the SDK agent mid-session.
 *
 * This enables hot-reload of agent context without restarting sessions.
 */

import type { ContextDelta } from "../sdk/types.js";
import pino from "pino";

const log = pino({ name: "sse-context-subscriber" });

type DeltaCallback = (delta: ContextDelta) => void;

interface SubscriptionOptions {
  /** DataServer base URL. */
  dataServerUrl?: string;
  /** Session ID to scope the subscription. */
  sessionId: string;
  /** Node IDs to watch for changes. */
  nodeIds: string[];
  /** Callback invoked when a context delta is received. */
  onDelta: DeltaCallback;
  /** Auth token for the DataServer. */
  authToken?: string;
}

export class ContextSubscriber {
  private controller: AbortController | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private opts: SubscriptionOptions;

  constructor(opts: SubscriptionOptions) {
    this.opts = opts;
  }

  /**
   * Start the SSE subscription.
   * Reconnects automatically on disconnect.
   */
  async start(): Promise<void> {
    this.stop();
    this.controller = new AbortController();

    const baseUrl =
      this.opts.dataServerUrl ?? process.env.COLLIDER_DATA_SERVER_URL ?? "http://localhost:8000";

    const headers: Record<string, string> = {
      Accept: "text/event-stream",
    };
    if (this.opts.authToken) {
      headers["Authorization"] = `Bearer ${this.opts.authToken}`;
    }

    const primaryUrl = new URL(`/api/v1/context/stream/${this.opts.sessionId}`, baseUrl);
    primaryUrl.searchParams.set("node_ids", this.opts.nodeIds.join(","));

    // Compatibility fallback for deployments exposing only generic SSE stream.
    const fallbackUrl = new URL("/api/v1/sse/", baseUrl);

    log.info(
      { sessionId: this.opts.sessionId, nodeIds: this.opts.nodeIds },
      "Starting SSE context subscription",
    );

    try {
      const endpoint = await this.selectEndpoint(
        [primaryUrl.toString(), fallbackUrl.toString()],
        headers,
      );

      if (!endpoint) {
        log.warn("No compatible SSE endpoint available, will retry");
        this.scheduleReconnect();
        return;
      }

      await this.consumeStream(endpoint, headers);
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      log.warn({ err: (err as Error).message }, "SSE connection lost");
    }

    this.scheduleReconnect();
  }

  /**
   * Stop the SSE subscription.
   */
  stop(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.controller) {
      this.controller.abort();
      this.controller = null;
    }
    log.info("SSE context subscription stopped");
  }

  // -----------------------------------------------------------------------
  // Internal
  // -----------------------------------------------------------------------

  private scheduleReconnect(): void {
    this.reconnectTimer = setTimeout(() => {
      log.info("Reconnecting SSE context subscription");
      this.start();
    }, 5000);
  }

  private async selectEndpoint(
    endpoints: string[],
    headers: Record<string, string>,
  ): Promise<string | null> {
    for (const endpoint of endpoints) {
      const resp = await fetch(endpoint, {
        headers,
        signal: this.controller?.signal,
      });
      if (resp.ok) {
        resp.body?.cancel();
        return endpoint;
      }
      log.debug({ endpoint, status: resp.status }, "SSE endpoint not available");
    }
    return null;
  }

  private async consumeStream(
    endpoint: string,
    headers: Record<string, string>,
  ): Promise<void> {
    const resp = await fetch(endpoint, {
      headers,
      signal: this.controller?.signal,
    });

    if (!resp.ok) {
      log.warn({ endpoint, status: resp.status }, "SSE subscription failed");
      return;
    }

    const reader = resp.body?.getReader();
    if (!reader) {
      log.warn({ endpoint }, "SSE response has no body");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const event of events) {
        const delta = this.parseEvent(event);
        if (delta) {
          this.opts.onDelta(delta);
        }
      }
    }
  }

  private parseEvent(raw: string): ContextDelta | null {
    const lines = raw.split("\n");
    let eventType = "";
    let data = "";

    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventType = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        data += line.slice(5).trim();
      }
    }

    if (!data) return null;

    try {
      const parsed = JSON.parse(data);

      // Map SSE event types to ContextDelta
      switch (eventType) {
        case "node_updated":
        case "context_delta":
          return parsed as ContextDelta;

        case "skill_changed":
          return {
            type: "skill",
            operation: parsed.operation ?? "update",
            skill: parsed.skill,
          };

        case "tool_changed":
          return {
            type: "tool_schema",
            operation: parsed.operation ?? "update",
            tool_schema: parsed.tool_schema,
          };

        case "full_refresh":
          return {
            type: "full_replace",
            context: parsed.context,
          };

        default:
          log.debug({ eventType }, "Unknown SSE event type");
          return null;
      }
    } catch {
      log.debug("Failed to parse SSE event data");
      return null;
    }
  }
}
