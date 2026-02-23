/**
 * NanoClawBridge Session Manager
 *
 * Maps session IDs to running Claude Code processes and SQLite state.
 * Handles session creation, message routing, resume, idle timeout, and cleanup.
 */

import path from "node:path";
import crypto from "node:crypto";
import { SessionDb, type SessionRow } from "./db.js";
import {
  spawnClaudeCode,
  killProcess,
  type RunningProcess,
  type RunOptions,
} from "./container-runner.js";
import { AnthropicAgent } from "./sdk/anthropic-agent.js";
import { ContextGrpcClient } from "./grpc/context-client.js";
import { ContextSubscriber } from "./sse/context-subscriber.js";
import type { ComposedContext } from "./sdk/types.js";
import type { AgentEvent } from "./event-parser.js";
import pino from "pino";

const log = pino({ name: "session-manager" });

const USE_SDK_AGENT = process.env.USE_SDK_AGENT === "true";
const USE_GRPC_CONTEXT = process.env.USE_GRPC_CONTEXT === "true";
const GRPC_CONTEXT_ADDRESS = process.env.GRPC_CONTEXT_ADDRESS ?? "localhost:50051";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SessionConfig {
  workspaceDir: string;
  mcpConfigPath?: string;
  systemPrompt?: string;
  model?: string;
  label?: string;
  idleTimeoutMs?: number;
  /** When USE_SDK_AGENT=true, context is delivered as JSON instead of files. */
  composedContext?: ComposedContext;
}

interface ActiveSession {
  row: SessionRow;
  process: RunningProcess | null;
  config: SessionConfig;
  idleTimer: ReturnType<typeof setTimeout> | null;
  eventListeners: Set<(event: AgentEvent) => void>;
}

// ---------------------------------------------------------------------------
// Manager
// ---------------------------------------------------------------------------

export class SessionManager {
  private db!: SessionDb;
  private active = new Map<string, ActiveSession>();
  private defaultIdleTimeoutMs: number;
  private sdkAgent: AnthropicAgent | null = null;
  private grpcClient: ContextGrpcClient | null = null;
  private contextSubscribers = new Map<string, ContextSubscriber>();

  private constructor(idleTimeoutMinutes: number) {
    this.defaultIdleTimeoutMs = idleTimeoutMinutes * 60_000;
    if (USE_SDK_AGENT) {
      this.sdkAgent = new AnthropicAgent();
      log.info("SDK agent mode enabled");
    }
    if (USE_GRPC_CONTEXT) {
      this.grpcClient = new ContextGrpcClient(GRPC_CONTEXT_ADDRESS);
      log.info({ address: GRPC_CONTEXT_ADDRESS }, "gRPC context client enabled");
    }
  }

  static async create(opts?: { dbPath?: string; idleTimeoutMinutes?: number }): Promise<SessionManager> {
    const mgr = new SessionManager(opts?.idleTimeoutMinutes ?? 30);
    mgr.db = await SessionDb.create(opts?.dbPath);
    return mgr;
  }

  // -----------------------------------------------------------------------
  // Session lifecycle
  // -----------------------------------------------------------------------

  /**
   * Create a new session or get an existing one by sessionKey.
   */
  getOrCreate(sessionKey: string, config: SessionConfig): SessionRow {
    let row = this.db.get(sessionKey);
    if (row) {
      // Update config if needed
      if (config.model) {
        this.db.update(sessionKey, { model: config.model });
        row = this.db.get(sessionKey)!;
      }
      return row;
    }

    row = this.db.create({
      session_id: sessionKey,
      claude_session_id: null,
      workspace_dir: config.workspaceDir,
      status: "idle",
      label: config.label ?? null,
      model: config.model ?? null,
    });

    return row;
  }

  /**
   * Send a message to a session, spawning Claude Code if needed.
   * Routes to SDK agent or CLI based on USE_SDK_AGENT flag.
   * Returns a function to unsubscribe from events.
   */
  sendMessage(
    sessionKey: string,
    message: string,
    config: SessionConfig,
    onEvent: (event: AgentEvent) => void,
  ): () => void {
    if (USE_SDK_AGENT && this.sdkAgent && (config.composedContext || USE_GRPC_CONTEXT)) {
      return this.sendMessageSdk(sessionKey, message, config, onEvent);
    }
    return this.sendMessageCli(sessionKey, message, config, onEvent);
  }

  // -----------------------------------------------------------------------
  // SDK agent path (USE_SDK_AGENT=true)
  // -----------------------------------------------------------------------

  private sendMessageSdk(
    sessionKey: string,
    message: string,
    config: SessionConfig,
    onEvent: (event: AgentEvent) => void,
  ): () => void {
    const row = this.getOrCreate(sessionKey, config);
    let session = this.active.get(sessionKey);

    if (!session) {
      session = {
        row,
        process: null,
        config,
        idleTimer: null,
        eventListeners: new Set(),
      };
      this.active.set(sessionKey, session);
    }

    session.eventListeners.add(onEvent);
    this.clearIdleTimer(session);
    this.db.update(sessionKey, { status: "active" });

    // Run the SDK agentic loop asynchronously
    const agent = this.sdkAgent!;
    const grpcClient = this.grpcClient;
    const broadcast = (event: AgentEvent) => {
      for (const listener of session!.eventListeners) {
        listener(event);
      }
    };

    (async () => {
      try {
        // Fetch context via gRPC if not provided directly
        let context = config.composedContext;
        if (!context && grpcClient) {
          try {
            context = await grpcClient.getBootstrap({
              sessionId: sessionKey,
              nodeIds: [],
              role: "app_user",
              appId: "",
            });
          } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            broadcast({ kind: "error", message: `gRPC context fetch failed: ${msg}` });
            broadcast({ kind: "message_end" });
            return;
          }
        }
        if (!context) {
          broadcast({ kind: "error", message: "No context available (neither direct nor via gRPC)" });
          broadcast({ kind: "message_end" });
          return;
        }

        // Create SDK session if this is the first message
        if (!session!.process && !agent.getHistory(sessionKey).length) {
          agent.createSession({
            sessionId: sessionKey,
            context,
            model: config.model ?? undefined,
          });

          // Start SSE delta subscription for live context updates
          if (USE_GRPC_CONTEXT && context.session_meta?.composed_nodes?.length) {
            const subscriber = new ContextSubscriber({
              sessionId: sessionKey,
              nodeIds: context.session_meta.composed_nodes,
              onDelta: (delta) => {
                this.injectContext(sessionKey, delta);
              },
            });
            this.contextSubscribers.set(sessionKey, subscriber);
            subscriber.start().catch((err: unknown) => {
              log.warn({ err }, "SSE context subscription failed");
            });
          }
        }

        for await (const event of agent.sendMessage(sessionKey, message)) {
          broadcast(event);
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        broadcast({ kind: "error", message: msg });
        broadcast({ kind: "message_end" });
      } finally {
        this.db.update(sessionKey, { status: "idle" });
        if (session) {
          this.startIdleTimer(session);
        }
      }
    })();

    return () => {
      session?.eventListeners.delete(onEvent);
    };
  }

  // -----------------------------------------------------------------------
  // CLI path (USE_SDK_AGENT=false) — original implementation
  // -----------------------------------------------------------------------

  private sendMessageCli(
    sessionKey: string,
    message: string,
    config: SessionConfig,
    onEvent: (event: AgentEvent) => void,
  ): () => void {
    const row = this.getOrCreate(sessionKey, config);
    let session = this.active.get(sessionKey);

    if (!session) {
      session = {
        row,
        process: null,
        config,
        idleTimer: null,
        eventListeners: new Set(),
      };
      this.active.set(sessionKey, session);
    }

    session.eventListeners.add(onEvent);
    this.clearIdleTimer(session);

    // Determine workspace-level .mcp.json path
    const mcpConfig =
      config.mcpConfigPath ??
      path.join(config.workspaceDir, ".mcp.json");

    const runOpts: RunOptions = {
      message,
      cwd: config.workspaceDir,
      mcpConfigPath: mcpConfig,
      resumeSessionId: row.claude_session_id ?? undefined,
      systemPrompt: config.systemPrompt,
      model: config.model ?? row.model ?? undefined,
      onEvent: (event) => {
        for (const listener of session!.eventListeners) {
          listener(event);
        }
      },
      onExit: (code, claudeSessionId) => {
        if (claudeSessionId && session) {
          session.row.claude_session_id = claudeSessionId;
          this.db.update(sessionKey, {
            claude_session_id: claudeSessionId,
            status: "idle",
          });
        } else {
          this.db.update(sessionKey, {
            status: code === 0 ? "idle" : "error",
          });
        }
        if (session) {
          session.process = null;
          this.startIdleTimer(session);
        }
      },
    };

    this.db.update(sessionKey, { status: "active" });
    session.process = spawnClaudeCode(runOpts);

    // Return unsubscribe function
    return () => {
      session?.eventListeners.delete(onEvent);
    };
  }

  /**
   * List sessions.
   */
  list(opts?: { status?: string; limit?: number }): SessionRow[] {
    return this.db.list(opts);
  }

  /**
   * Patch session settings (model, label).
   */
  patch(
    sessionKey: string,
    settings: { model?: string; label?: string },
  ): SessionRow | undefined {
    const row = this.db.get(sessionKey);
    if (!row) return undefined;

    this.db.update(sessionKey, settings);

    const session = this.active.get(sessionKey);
    if (session && settings.model) {
      session.config.model = settings.model;
    }

    return this.db.get(sessionKey);
  }

  /**
   * Kill and remove a session.
   */
  destroy(sessionKey: string): void {
    const session = this.active.get(sessionKey);
    if (session) {
      this.clearIdleTimer(session);
      if (session.process) {
        killProcess(session.process);
      }
      this.active.delete(sessionKey);
    }
    // Terminate SDK session if active
    if (this.sdkAgent) {
      try { this.sdkAgent.terminateSession(sessionKey); } catch { /* noop */ }
    }
    // Stop context subscriber for this session
    const subscriber = this.contextSubscribers.get(sessionKey);
    if (subscriber) {
      subscriber.stop();
      this.contextSubscribers.delete(sessionKey);
    }
    this.db.delete(sessionKey);
  }

  /**
   * Inject a context delta into an active SDK session.
   * No-op when running in CLI mode.
   */
  injectContext(
    sessionKey: string,
    delta: import("./sdk/types.js").ContextDelta,
  ): void {
    if (!this.sdkAgent) return;
    this.sdkAgent.injectContext(sessionKey, delta);
    log.info({ sessionKey, deltaType: delta.type }, "Context delta injected");
  }

  /**
   * Graceful shutdown — kill all active processes and close the DB.
   */
  shutdown(): void {
    for (const [key, session] of this.active) {
      this.clearIdleTimer(session);
      if (session.process) {
        killProcess(session.process);
      }
      if (this.sdkAgent) {
        try { this.sdkAgent.terminateSession(key); } catch { /* noop */ }
      }
      this.active.delete(key);
    }
    this.db.close();
    // Close gRPC client and all context subscribers
    if (this.grpcClient) {
      this.grpcClient.close();
    }
    for (const sub of this.contextSubscribers.values()) {
      sub.stop();
    }
    this.contextSubscribers.clear();
  }

  // -----------------------------------------------------------------------
  // Idle timeout
  // -----------------------------------------------------------------------

  private startIdleTimer(session: ActiveSession): void {
    const timeout = session.config.idleTimeoutMs ?? this.defaultIdleTimeoutMs;
    session.idleTimer = setTimeout(() => {
      log.info({ session_id: session.row.session_id }, "Session idle timeout — cleaning up");
      this.active.delete(session.row.session_id);
    }, timeout);
  }

  private clearIdleTimer(session: ActiveSession): void {
    if (session.idleTimer) {
      clearTimeout(session.idleTimer);
      session.idleTimer = null;
    }
  }
}

/**
 * Generate a session key from components.
 */
export function makeSessionKey(parts: {
  workspaceDir?: string;
  nodeId?: string;
}): string {
  if (parts.nodeId) return parts.nodeId;
  if (parts.workspaceDir) return `ws-${path.basename(parts.workspaceDir)}`;
  return `session-${crypto.randomUUID().slice(0, 8)}`;
}
