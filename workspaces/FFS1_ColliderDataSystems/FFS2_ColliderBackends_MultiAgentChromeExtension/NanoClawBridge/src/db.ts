/**
 * NanoClawBridge Database — SQLite session persistence via sql.js (pure JS).
 *
 * Stores session metadata so sessions survive bridge restarts and can be
 * listed/resumed via the `sessions.list` RPC method.
 *
 * Uses sql.js instead of better-sqlite3 to avoid native compilation on Windows.
 */

import initSqlJs, { type Database } from "sql.js";
import path from "node:path";
import os from "node:os";
import fs from "node:fs";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SessionRow {
  session_id: string;
  /** Claude Code session ID (for --resume) */
  claude_session_id: string | null;
  /** Workspace directory this session operates in */
  workspace_dir: string;
  /** Active | idle | completed | error */
  status: "active" | "idle" | "completed" | "error";
  /** ISO-8601 creation timestamp */
  created_at: string;
  /** ISO-8601 last activity timestamp */
  updated_at: string;
  /** Optional session-key label (e.g. the node name) */
  label: string | null;
  /** Model override */
  model: string | null;
}

// ---------------------------------------------------------------------------
// Database
// ---------------------------------------------------------------------------

export class SessionDb {
  private db!: Database;
  private dbFile: string;

  private constructor(db: Database, dbFile: string) {
    this.db = db;
    this.dbFile = dbFile;
  }

  static async create(dbPath?: string): Promise<SessionDb> {
    const dir = dbPath
      ? path.dirname(dbPath)
      : path.join(os.homedir(), ".nanoclaw");
    fs.mkdirSync(dir, { recursive: true });
    const file = dbPath ?? path.join(dir, "sessions.db");

    const SQL = await initSqlJs();

    let db: Database;
    if (fs.existsSync(file)) {
      const buffer = fs.readFileSync(file);
      db = new SQL.Database(buffer);
    } else {
      db = new SQL.Database();
    }

    const instance = new SessionDb(db, file);
    instance.migrate();
    return instance;
  }

  // -----------------------------------------------------------------------
  // CRUD
  // -----------------------------------------------------------------------

  create(row: Omit<SessionRow, "created_at" | "updated_at">): SessionRow {
    const now = new Date().toISOString();
    this.db.run(
      `INSERT INTO sessions
         (session_id, claude_session_id, workspace_dir, status, created_at, updated_at, label, model)
       VALUES
         (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        row.session_id,
        row.claude_session_id,
        row.workspace_dir,
        row.status,
        now,
        now,
        row.label,
        row.model,
      ],
    );
    this.persist();
    return { ...row, created_at: now, updated_at: now };
  }

  get(sessionId: string): SessionRow | undefined {
    const stmt = this.db.prepare("SELECT * FROM sessions WHERE session_id = ?");
    stmt.bind([sessionId]);
    if (stmt.step()) {
      const row = stmt.getAsObject() as unknown as SessionRow;
      stmt.free();
      return row;
    }
    stmt.free();
    return undefined;
  }

  list(opts?: { status?: string; limit?: number }): SessionRow[] {
    let sql = "SELECT * FROM sessions";
    const params: (string | number)[] = [];
    if (opts?.status) {
      sql += " WHERE status = ?";
      params.push(opts.status);
    }
    sql += " ORDER BY updated_at DESC";
    if (opts?.limit) {
      sql += " LIMIT ?";
      params.push(opts.limit);
    }

    const stmt = this.db.prepare(sql);
    if (params.length) stmt.bind(params);

    const rows: SessionRow[] = [];
    while (stmt.step()) {
      rows.push(stmt.getAsObject() as unknown as SessionRow);
    }
    stmt.free();
    return rows;
  }

  update(
    sessionId: string,
    fields: Partial<Pick<SessionRow, "claude_session_id" | "status" | "model" | "label">>,
  ): void {
    const sets: string[] = ["updated_at = ?"];
    const params: (string | null)[] = [new Date().toISOString()];

    for (const [key, value] of Object.entries(fields)) {
      if (value !== undefined) {
        sets.push(`${key} = ?`);
        params.push(value as string | null);
      }
    }
    params.push(sessionId);

    this.db.run(
      `UPDATE sessions SET ${sets.join(", ")} WHERE session_id = ?`,
      params,
    );
    this.persist();
  }

  delete(sessionId: string): void {
    this.db.run("DELETE FROM sessions WHERE session_id = ?", [sessionId]);
    this.persist();
  }

  close(): void {
    this.persist();
    this.db.close();
  }

  // -----------------------------------------------------------------------
  // Persistence — write DB to disk after mutations
  // -----------------------------------------------------------------------

  private persist(): void {
    const data = this.db.export();
    const buffer = Buffer.from(data);
    fs.writeFileSync(this.dbFile, buffer);
  }

  // -----------------------------------------------------------------------
  // Migration
  // -----------------------------------------------------------------------

  private migrate(): void {
    this.db.run(`
      CREATE TABLE IF NOT EXISTS sessions (
        session_id          TEXT PRIMARY KEY,
        claude_session_id   TEXT,
        workspace_dir       TEXT NOT NULL,
        status              TEXT NOT NULL DEFAULT 'idle',
        created_at          TEXT NOT NULL,
        updated_at          TEXT NOT NULL,
        label               TEXT,
        model               TEXT
      )
    `);
    this.db.run(
      "CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions (status)",
    );
    this.db.run(
      "CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions (updated_at DESC)",
    );
    this.persist();
  }
}
