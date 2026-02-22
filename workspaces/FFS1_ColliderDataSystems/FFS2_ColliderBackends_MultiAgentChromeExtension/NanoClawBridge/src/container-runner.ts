/**
 * NanoClawBridge Container Runner
 *
 * Spawns Claude Code CLI as a child process (no Docker on Windows) and
 * streams stdout (stream-json format) to an EventParser for real-time
 * event translation.
 *
 * Inspired by NanoClaw's container-runner.ts but adapted for:
 *   - Direct child_process (no Docker)
 *   - Claude Code's --output-format stream-json
 *   - Session resume via --resume flag
 */

import { spawn, type ChildProcess } from "node:child_process";
import { EventParser, type AgentEvent } from "./event-parser.js";
import pino from "pino";

const log = pino({ name: "container-runner" });

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface RunOptions {
  /** User message to send to Claude Code */
  message: string;
  /** Working directory (the workspace) */
  cwd: string;
  /** Path to .mcp.json for MCP server config */
  mcpConfigPath?: string;
  /** Claude Code session ID to resume */
  resumeSessionId?: string;
  /** System prompt override */
  systemPrompt?: string;
  /** Model override (e.g. "claude-sonnet-4-20250514") */
  model?: string;
  /** Callback for each parsed AgentEvent */
  onEvent: (event: AgentEvent) => void;
  /** Callback when the process exits */
  onExit: (code: number | null, claudeSessionId?: string) => void;
}

export interface RunningProcess {
  child: ChildProcess;
  parser: EventParser;
  sessionId?: string;
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------

/**
 * Spawn a Claude Code CLI process and stream parsed events back.
 *
 * Uses `claude --print --output-format stream-json` which outputs one
 * JSON object per line to stdout. The EventParser converts these into
 * AgentEvent objects matching the Chrome Extension's protocol.
 */
export function spawnClaudeCode(opts: RunOptions): RunningProcess {
  const args = buildArgs(opts);

  log.info({ cwd: opts.cwd, resume: opts.resumeSessionId ?? "new" }, "Spawning Claude Code");

  const child = spawn("claude", args, {
    cwd: opts.cwd,
    stdio: ["pipe", "pipe", "pipe"],
    shell: true,
    env: {
      ...process.env,
      // Ensure Claude Code uses the workspace dir
      CLAUDE_CODE_DISABLE_NONINTERACTIVE_CHECK: "1",
    },
  });

  const parser = new EventParser();
  let stdoutBuffer = "";
  let claudeSessionId: string | undefined;

  // Parse stdout line-by-line
  child.stdout?.on("data", (chunk: Buffer) => {
    stdoutBuffer += chunk.toString("utf8");
    const lines = stdoutBuffer.split("\n");
    // Keep the last incomplete line in the buffer
    stdoutBuffer = lines.pop() ?? "";

    for (const line of lines) {
      // Try to extract session_id from result messages
      try {
        const parsed = JSON.parse(line.trim());
        if (parsed.session_id) {
          claudeSessionId = parsed.session_id;
        }
      } catch {
        // Not JSON, skip
      }

      const events = parser.parse(line);
      for (const event of events) {
        opts.onEvent(event);
      }
    }
  });

  // Log stderr for debugging
  child.stderr?.on("data", (chunk: Buffer) => {
    const text = chunk.toString("utf8").trim();
    if (text) {
      log.warn({ stderr: text }, "Claude Code stderr");
    }
  });

  child.on("error", (err) => {
    log.error({ err }, "Claude Code process error");
    opts.onEvent({ kind: "error", message: `Process error: ${err.message}` });
    opts.onExit(1);
  });

  child.on("close", (code) => {
    // Flush remaining buffer
    if (stdoutBuffer.trim()) {
      const events = parser.parse(stdoutBuffer);
      for (const event of events) {
        opts.onEvent(event);
      }
    }
    log.info({ code, claudeSessionId }, "Claude Code process exited");
    opts.onExit(code, claudeSessionId);
  });

  return { child, parser, sessionId: claudeSessionId };
}

/**
 * Send a follow-up message to a running Claude Code process via stdin.
 */
export function sendMessage(proc: RunningProcess, message: string): void {
  if (proc.child.stdin?.writable) {
    proc.child.stdin.write(message + "\n");
  }
}

/**
 * Kill a running Claude Code process.
 */
export function killProcess(proc: RunningProcess): void {
  if (!proc.child.killed) {
    proc.child.kill("SIGTERM");
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildArgs(opts: RunOptions): string[] {
  const args: string[] = ["--print", "--output-format", "stream-json"];

  if (opts.resumeSessionId) {
    args.push("--resume", opts.resumeSessionId);
  }

  if (opts.mcpConfigPath) {
    args.push("--mcp-config", opts.mcpConfigPath);
  }

  if (opts.systemPrompt) {
    args.push("--system-prompt", opts.systemPrompt);
  }

  if (opts.model) {
    args.push("--model", opts.model);
  }

  // The user message is the final positional argument
  args.push(opts.message);

  return args;
}
