/**
 * NanoClawBridge — Main entry point
 *
 * Starts an HTTP server with WebSocket upgrade on :18789 (configurable).
 * The WebSocket bridge accepts JSON-RPC frames from the Chrome Extension
 * and routes them to Claude Code CLI sessions.
 */

import http from "node:http";
import path from "node:path";
import os from "node:os";
import pino from "pino";
import { SessionManager } from "./session-manager.js";
import { WsBridge } from "./ws-bridge.js";

const log = pino({ name: "nanoclaw-bridge" });

// ---------------------------------------------------------------------------
// Config from environment
// ---------------------------------------------------------------------------

const PORT = parseInt(process.env.NANOCLAWBRIDGE_PORT ?? "18789", 10);
const WORKSPACE_DIR =
  process.env.NANOCLAW_WORKSPACE_DIR ??
  path.join(os.homedir(), ".nanoclaw", "workspaces", "collider");
const MCP_URL =
  process.env.COLLIDER_MCP_URL ?? "http://localhost:8001/mcp/sse";
const IDLE_TIMEOUT_MINUTES = parseInt(
  process.env.SESSION_IDLE_TIMEOUT_MINUTES ?? "30",
  10,
);

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  log.info(
    {
      port: PORT,
      workspaceDir: WORKSPACE_DIR,
      mcpUrl: MCP_URL,
      idleTimeoutMinutes: IDLE_TIMEOUT_MINUTES,
    },
    "Starting NanoClawBridge",
  );

  // Verify ANTHROPIC_API_KEY is set
  if (!process.env.ANTHROPIC_API_KEY) {
    log.warn("ANTHROPIC_API_KEY not set — Claude Code CLI may fail");
  }

  // Session manager with SQLite persistence (async init)
  const sessions = await SessionManager.create({
    idleTimeoutMinutes: IDLE_TIMEOUT_MINUTES,
  });

  // HTTP server (minimal — only serves health check)
  const server = http.createServer((req, res) => {
    if (req.url === "/health" && req.method === "GET") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "ok", service: "NanoClawBridge" }));
      return;
    }
    res.writeHead(404);
    res.end("Not Found");
  });

  // WebSocket bridge on the same server
  const bridge = new WsBridge({
    server,
    sessions,
    defaultWorkspaceDir: WORKSPACE_DIR,
    mcpUrl: MCP_URL,
  });

  // Start listening
  server.listen(PORT, () => {
    log.info(`NanoClawBridge listening on ws://127.0.0.1:${PORT}`);
  });

  // Graceful shutdown
  const shutdown = (signal: string) => {
    log.info({ signal }, "Shutting down");
    bridge.close();
    sessions.shutdown();
    server.close(() => {
      log.info("Server closed");
      process.exit(0);
    });
    // Force exit after 5s
    setTimeout(() => process.exit(1), 5000);
  };

  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
