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
    const url = new URL(`/api/v1/context/stream/${this.opts.sessionId}`, baseUrl);
    url.searchParams.set("node_ids", this.opts.nodeIds.join(","));

    const headers: Record<string, string> = {
      Accept: "text/event-stream",
    };
    if (this.opts.authToken) {
      headers["Authorization"] = `Bearer ${this.opts.authToken}`;
    }

    log.info(
      { sessionId: this.opts.sessionId, nodeIds: this.opts.nodeIds },
      "Starting SSE context subscription",
    );

    try {
      const resp = await fetch(url.toString(), {
        headers,
        signal: this.controller.signal,
      });

      if (!resp.ok) {
        log.warn({ status: resp.status }, "SSE subscription failed, will retry");
        this.scheduleReconnect();
        return;
      }

      const reader = resp.body?.getReader();
      if (!reader) {
        log.warn("SSE response has no body");
        this.scheduleReconnect();
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const event of events) {
          const delta = this.parseEvent(event);
          if (delta) {
            this.opts.onDelta(delta);
          }
        }
      }
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
