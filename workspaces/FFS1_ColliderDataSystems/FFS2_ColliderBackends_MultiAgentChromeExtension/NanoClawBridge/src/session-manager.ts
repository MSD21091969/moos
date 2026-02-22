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
import type { AgentEvent } from "./event-parser.js";
import pino from "pino";

const log = pino({ name: "session-manager" });

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

  private constructor(idleTimeoutMinutes: number) {
    this.defaultIdleTimeoutMs = idleTimeoutMinutes * 60_000;
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
   * Returns a function to unsubscribe from events.
   */
  sendMessage(
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
    this.db.delete(sessionKey);
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
      this.active.delete(key);
    }
    this.db.close();
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
