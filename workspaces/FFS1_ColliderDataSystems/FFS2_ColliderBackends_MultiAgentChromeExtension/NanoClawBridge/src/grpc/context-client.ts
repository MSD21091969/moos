/**
 * gRPC Context Client
 *
 * Connects to the AgentRunner's ColliderContext gRPC service to fetch
 * composed context programmatically, replacing filesystem reads.
 *
 * Uses @grpc/grpc-js with dynamic proto loading (no code generation needed).
 */

import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";
import type {
  ComposedContext,
  SkillDefinition,
  ToolSchema,
  McpServerConfig,
  SessionMeta,
  ContextDelta,
} from "../sdk/types.js";
import pino from "pino";

const log = pino({ name: "grpc-context-client" });

// ---------------------------------------------------------------------------
// Proto loading
// ---------------------------------------------------------------------------

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROTO_PATH = resolve(__dirname, "../../proto/collider_graph.proto");

const packageDef = protoLoader.loadSync(PROTO_PATH, {
  keepCase: false,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});

const proto = grpc.loadPackageDefinition(packageDef) as Record<string, any>;
const colliderPkg = proto.collider ?? proto;

// ---------------------------------------------------------------------------
// Types from proto (dynamic)
// ---------------------------------------------------------------------------

interface BootstrapResponse {
  sessionId: string;
  agentsMd: string;
  soulMd: string;
  toolsMd: string;
  skills: ProtoSkill[];
  toolSchemas: ProtoToolSchema[];
  mcpServers: ProtoMcpConfig[];
  sessionMeta: ProtoSessionMeta;
}

interface ProtoSkill {
  name: string;
  description: string;
  emoji: string;
  markdownBody: string;
  toolRef: string;
  userInvocable: boolean;
  modelInvocable: boolean;
  invocationPolicy: string;
  requiresBins: string[];
  requiresEnv: string[];
}

interface ProtoToolSchema {
  name: string;
  description: string;
  parametersJson: Buffer | string;
}

interface ProtoMcpConfig {
  name: string;
  transportType: string;
  url: string;
  command: string;
  args: string[];
}

interface ProtoSessionMeta {
  role: string;
  appId: string;
  composedNodes: string[];
  username: string;
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export class ContextGrpcClient {
  private client: any;
  private address: string;

  constructor(address: string = "localhost:50051") {
    this.address = address;
    const ContextService = colliderPkg.ColliderContext;
    this.client = new ContextService(
      address,
      grpc.credentials.createInsecure(),
    );
  }

  /**
   * Fetch full composed context as a single response.
   * Returns a ComposedContext matching the SDK types.
   */
  async getBootstrap(opts: {
    sessionId: string;
    nodeIds: string[];
    role: string;
    appId: string;
    inheritAncestors?: boolean;
  }): Promise<ComposedContext> {
    return new Promise((resolve, reject) => {
      this.client.GetBootstrap(
        {
          session_id: opts.sessionId,
          node_ids: opts.nodeIds,
          role: opts.role,
          app_id: opts.appId,
          inherit_ancestors: opts.inheritAncestors ?? true,
        },
        (err: grpc.ServiceError | null, response: BootstrapResponse) => {
          if (err) {
            log.error({ err: err.message }, "GetBootstrap failed");
            reject(err);
            return;
          }

          resolve(this.convertToComposedContext(response));
        },
      );
    });
  }

  /**
   * Stream composed context as typed chunks.
   * Returns an async iterable of partial context updates.
   */
  async *streamContext(opts: {
    sessionId: string;
    nodeIds: string[];
    role: string;
    appId: string;
    inheritAncestors?: boolean;
  }): AsyncGenerator<Partial<ComposedContext>> {
    const call = this.client.StreamContext({
      session_id: opts.sessionId,
      node_ids: opts.nodeIds,
      role: opts.role,
      app_id: opts.appId,
      inherit_ancestors: opts.inheritAncestors ?? true,
    });

    for await (const chunk of call) {
      yield this.convertChunk(chunk);
    }
  }

  /**
   * Close the gRPC channel.
   */
  close(): void {
    this.client.close();
    log.info({ address: this.address }, "gRPC channel closed");
  }

  // -----------------------------------------------------------------------
  // Converters
  // -----------------------------------------------------------------------

  private convertToComposedContext(resp: BootstrapResponse): ComposedContext {
    return {
      agents_md: resp.agentsMd ?? "",
      soul_md: resp.soulMd ?? "",
      tools_md: resp.toolsMd ?? "",
      skills: (resp.skills ?? []).map(this.convertSkill),
      tool_schemas: (resp.toolSchemas ?? []).map(this.convertToolSchema),
      mcp_servers: (resp.mcpServers ?? []).map(this.convertMcpConfig),
      session_meta: this.convertSessionMeta(resp.sessionMeta),
    };
  }

  private convertSkill(s: ProtoSkill): SkillDefinition {
    return {
      name: s.name,
      description: s.description,
      emoji: s.emoji || undefined,
      markdown_body: s.markdownBody,
      tool_ref: s.toolRef || undefined,
      user_invocable: s.userInvocable,
      model_invocable: s.modelInvocable,
      invocation_policy: (s.invocationPolicy as "auto" | "confirm" | "disabled") || "auto",
      requires_bins: s.requiresBins,
      requires_env: s.requiresEnv,
    };
  }

  private convertToolSchema(t: ProtoToolSchema): ToolSchema {
    let params: Record<string, unknown> = {};
    try {
      const raw = typeof t.parametersJson === "string"
        ? t.parametersJson
        : t.parametersJson?.toString("utf-8") ?? "{}";
      params = JSON.parse(raw);
    } catch { /* empty */ }

    return {
      type: "function",
      function: {
        name: t.name,
        description: t.description,
        parameters: params,
      },
    };
  }

  private convertMcpConfig(m: ProtoMcpConfig): McpServerConfig {
    return {
      name: m.name,
      type: m.transportType as "sse" | "stdio",
      url: m.url || undefined,
      command: m.command || undefined,
      args: m.args?.length ? m.args : undefined,
    };
  }

  private convertSessionMeta(m: ProtoSessionMeta | undefined): SessionMeta {
    return {
      role: m?.role ?? "",
      app_id: m?.appId ?? "",
      composed_nodes: m?.composedNodes ?? [],
      username: m?.username || undefined,
    };
  }

  private convertChunk(chunk: any): Partial<ComposedContext> {
    const partial: Partial<ComposedContext> = {};

    if (chunk.systemPrompt) {
      const section = chunk.systemPrompt.section;
      const content = chunk.systemPrompt.content;
      if (section === "agents_md") partial.agents_md = content;
      else if (section === "soul_md") partial.soul_md = content;
      else if (section === "tools_md") partial.tools_md = content;
    } else if (chunk.skill) {
      partial.skills = [this.convertSkill(chunk.skill)];
    } else if (chunk.toolSchema) {
      partial.tool_schemas = [this.convertToolSchema(chunk.toolSchema)];
    } else if (chunk.mcpConfig) {
      partial.mcp_servers = [this.convertMcpConfig(chunk.mcpConfig)];
    } else if (chunk.sessionMeta) {
      partial.session_meta = this.convertSessionMeta(chunk.sessionMeta);
    }

    return partial;
  }
}
