/**
 * NanoClawBridge WebSocket Bridge
 *
 * Accepts JSON-RPC frames from the Chrome Extension over WebSocket and
 * routes them to the SessionManager / ContainerRunner.
 *
 * Protocol (same as the Chrome Extension already speaks):
 *
 *   Request:  { type: "request",  id, method, params }
 *   Response: { type: "response", id, result?, error? }
 *   Event:    { type: "event",    event, ...data }
 *
 * Supported methods:
 *   - agent.request  → spawn/resume Claude Code, stream events back
 *   - sessions.list  → list sessions from DB
 *   - sessions.patch → update session settings (model, label)
 *   - sessions.send  → alias for agent.request on a specific session
 */

import { WebSocketServer, WebSocket } from "ws";
import type { IncomingMessage } from "node:http";
import type { Server as HttpServer } from "node:http";
import { SessionManager, makeSessionKey, type SessionConfig } from "./session-manager.js";
import type { AgentEvent } from "./event-parser.js";
import pino from "pino";

const log = pino({ name: "ws-bridge" });

// ---------------------------------------------------------------------------
// JSON-RPC Types
// ---------------------------------------------------------------------------

interface RpcRequest {
  type: "request";
  id: string;
  method: string;
  params: Record<string, unknown>;
}

interface RpcResponse {
  type: "response";
  id: string;
  result?: unknown;
  error?: { message: string; code?: number };
}

interface RpcEvent {
  type: "event";
  event: string;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Bridge
// ---------------------------------------------------------------------------

export class WsBridge {
  private wss: WebSocketServer;
  private sessions: SessionManager;
  private defaultWorkspaceDir: string;
  private mcpUrl: string;

  constructor(opts: {
    server: HttpServer;
    sessions: SessionManager;
    defaultWorkspaceDir: string;
    mcpUrl: string;
  }) {
    this.sessions = opts.sessions;
    this.defaultWorkspaceDir = opts.defaultWorkspaceDir;
    this.mcpUrl = opts.mcpUrl;

    this.wss = new WebSocketServer({ server: opts.server });
    this.wss.on("connection", (ws, req) => this.onConnection(ws, req));

    log.info("WebSocket bridge ready");
  }

  // -----------------------------------------------------------------------
  // Connection handling
  // -----------------------------------------------------------------------

  private onConnection(ws: WebSocket, req: IncomingMessage): void {
    const clientIp = req.socket.remoteAddress;
    log.info({ clientIp }, "Client connected");

    // Track event unsubscribers for cleanup
    const unsubscribers: (() => void)[] = [];

    ws.on("message", (data) => {
      try {
        const msg = JSON.parse(data.toString()) as RpcRequest;
        if (msg.type !== "request" || !msg.id || !msg.method) {
          this.sendError(ws, msg.id ?? "?", "Invalid request frame");
          return;
        }
        this.handleRequest(ws, msg, unsubscribers);
      } catch {
        this.sendError(ws, "?", "Failed to parse message");
      }
    });

    ws.on("close", () => {
      log.info({ clientIp }, "Client disconnected");
      for (const unsub of unsubscribers) unsub();
    });

    ws.on("error", (err) => {
      log.error({ err, clientIp }, "WebSocket error");
    });
  }

  // -----------------------------------------------------------------------
  // Request routing
  // -----------------------------------------------------------------------

  private handleRequest(
    ws: WebSocket,
    req: RpcRequest,
    unsubscribers: (() => void)[],
  ): void {
    switch (req.method) {
      case "agent.request":
        this.handleAgentRequest(ws, req, unsubscribers);
        break;
      case "sessions.list":
        this.handleSessionsList(ws, req);
        break;
      case "sessions.patch":
        this.handleSessionsPatch(ws, req);
        break;
      case "sessions.send":
        this.handleAgentRequest(ws, req, unsubscribers);
        break;
      default:
        this.sendError(ws, req.id, `Unknown method: ${req.method}`);
    }
  }

  // -----------------------------------------------------------------------
  // agent.request / sessions.send
  // -----------------------------------------------------------------------

  private handleAgentRequest(
    ws: WebSocket,
    req: RpcRequest,
    unsubscribers: (() => void)[],
  ): void {
    const message = req.params.message as string | undefined;
    if (!message) {
      this.sendError(ws, req.id, "Missing required param: message");
      return;
    }

    const sessionKey =
      (req.params.sessionKey as string) ??
      makeSessionKey({ workspaceDir: this.defaultWorkspaceDir });

    const config: SessionConfig = {
      workspaceDir: (req.params.workspaceDir as string) ?? this.defaultWorkspaceDir,
      model: req.params.model as string | undefined,
      label: req.params.label as string | undefined,
    };

    // Acknowledge the request immediately
    this.sendResponse(ws, req.id, { status: "streaming", sessionKey });

    // Subscribe to events and forward to WebSocket
    const onEvent = (event: AgentEvent) => {
      if (ws.readyState !== WebSocket.OPEN) return;

      const frame = this.agentEventToFrame(event);
      ws.send(JSON.stringify(frame));
    };

    const unsub = this.sessions.sendMessage(sessionKey, message, config, onEvent);
    unsubscribers.push(unsub);
  }

  // -----------------------------------------------------------------------
  // sessions.list
  // -----------------------------------------------------------------------

  private handleSessionsList(ws: WebSocket, req: RpcRequest): void {
    const rows = this.sessions.list({
      limit: (req.params.limit as number) ?? 50,
    });
    this.sendResponse(ws, req.id, rows);
  }

  // -----------------------------------------------------------------------
  // sessions.patch
  // -----------------------------------------------------------------------

  private handleSessionsPatch(ws: WebSocket, req: RpcRequest): void {
    const sessionKey = req.params.sessionKey as string;
    if (!sessionKey) {
      this.sendError(ws, req.id, "Missing required param: sessionKey");
      return;
    }
    const updated = this.sessions.patch(sessionKey, {
      model: req.params.model as string | undefined,
      label: req.params.label as string | undefined,
    });
    if (!updated) {
      this.sendError(ws, req.id, `Session not found: ${sessionKey}`);
      return;
    }
    this.sendResponse(ws, req.id, updated);
  }

  // -----------------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------------

  /** Convert AgentEvent → JSON-RPC event frame matching Chrome Extension expectations. */
  private agentEventToFrame(event: AgentEvent): RpcEvent {
    switch (event.kind) {
      case "text_delta":
        return { type: "event", event: "text_delta", data: event.text };
      case "tool_use_start":
        return {
          type: "event",
          event: "tool_use_start",
          data: { name: event.name, args: event.args },
        };
      case "tool_result":
        return {
          type: "event",
          event: "tool_result",
          data: { name: event.name, result: event.result },
        };
      case "thinking":
        return { type: "event", event: "thinking", data: event.text };
      case "message_end":
        return { type: "event", event: "message_end" };
      case "error":
        return { type: "event", event: "error", message: event.message };
    }
  }

  private sendResponse(ws: WebSocket, id: string, result: unknown): void {
    if (ws.readyState !== WebSocket.OPEN) return;
    const frame: RpcResponse = { type: "response", id, result };
    ws.send(JSON.stringify(frame));
  }

  private sendError(ws: WebSocket, id: string, message: string): void {
    if (ws.readyState !== WebSocket.OPEN) return;
    const frame: RpcResponse = { type: "response", id, error: { message } };
    ws.send(JSON.stringify(frame));
  }

  /** Graceful shutdown. */
  close(): void {
    this.wss.close();
  }
}
