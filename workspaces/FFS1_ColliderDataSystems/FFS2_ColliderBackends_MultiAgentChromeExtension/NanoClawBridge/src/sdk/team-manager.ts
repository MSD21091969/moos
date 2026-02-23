/**
 * Team Manager — Multi-agent orchestration for Collider workspaces
 *
 * When a ContextSet contains multiple node_ids, instead of merging everything
 * into one flat context, the TeamManager spawns an agent team where:
 *   - Each node becomes a teammate with its own isolated bootstrap context
 *   - A leader agent gets the merged high-level context from all nodes
 *   - Communication flows through a mailbox pattern
 *
 * This maps directly to the workspace-as-application model: each workspace
 * node is a first-class agent identity, and teams are formed by selecting
 * multiple nodes in the FFS4 graph.
 */

import { AnthropicAgent } from "./anthropic-agent.js";
import { ContextGrpcClient } from "../grpc/context-client.js";
import type { ComposedContext } from "./types.js";
import type { AgentEvent } from "../event-parser.js";
import pino from "pino";

const log = pino({ name: "team-manager" });

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TeamConfig {
  teamId: string;
  nodeIds: string[];
  leaderNodeId?: string;
  role: string;
  appId: string;
  model?: string;
}

export interface AgentTeam {
  id: string;
  leaderId: string;
  memberIds: string[];
  nodeMap: Map<string, string>;   // nodeId → sessionId
  mailbox: TeamMessage[];
  status: "idle" | "running" | "completed" | "error";
}

export interface TeamMessage {
  id: string;
  from: string;       // sessionId of sender
  to: string;         // sessionId of recipient (or "all" for broadcast)
  content: string;
  timestamp: number;
  read: boolean;
}

export interface TeamStatus {
  teamId: string;
  status: AgentTeam["status"];
  leader: { sessionId: string; nodeId: string };
  members: Array<{ sessionId: string; nodeId: string }>;
  mailboxSize: number;
  unreadCount: number;
}

// ---------------------------------------------------------------------------
// Team Manager
// ---------------------------------------------------------------------------

export class TeamManager {
  private agent: AnthropicAgent;
  private grpcClient: ContextGrpcClient | null;
  private teams = new Map<string, AgentTeam>();
  private messageCounter = 0;

  constructor(agent: AnthropicAgent, grpcClient?: ContextGrpcClient) {
    this.agent = agent;
    this.grpcClient = grpcClient ?? null;
  }

  // -----------------------------------------------------------------------
  // Team Lifecycle
  // -----------------------------------------------------------------------

  /**
   * Create a team from multiple nodes.
   * Each node gets its own SDK session with isolated context.
   * The leader session gets merged context from all nodes.
   */
  async createTeam(config: TeamConfig): Promise<AgentTeam> {
    const { teamId, nodeIds, role, appId } = config;

    if (nodeIds.length < 2) {
      throw new Error("A team requires at least 2 nodes");
    }

    log.info({ teamId, nodeIds, role }, "Creating agent team");

    // Fetch individual bootstraps for each node
    const bootstraps: ComposedContext[] = [];
    for (const nodeId of nodeIds) {
      const ctx = await this.fetchContext(`${teamId}-${nodeId}`, [nodeId], role, appId);
      bootstraps.push(ctx);
    }

    // Fetch merged leader context (all nodes combined)
    const leaderCtx = await this.fetchContext(`${teamId}-leader`, nodeIds, role, appId);

    // Create leader session
    this.agent.createSession({
      sessionId: `${teamId}-leader`,
      context: leaderCtx,
      model: config.model,
    });

    // Create member sessions
    const nodeMap = new Map<string, string>();
    for (let i = 0; i < nodeIds.length; i++) {
      const sessionId = `${teamId}-${nodeIds[i]}`;
      this.agent.createSession({
        sessionId,
        context: bootstraps[i],
        model: config.model,
      });
      nodeMap.set(nodeIds[i], sessionId);
    }

    const team: AgentTeam = {
      id: teamId,
      leaderId: `${teamId}-leader`,
      memberIds: nodeIds.map((n) => `${teamId}-${n}`),
      nodeMap,
      mailbox: [],
      status: "idle",
    };

    this.teams.set(teamId, team);

    log.info(
      { teamId, leader: team.leaderId, members: team.memberIds.length },
      "Agent team created",
    );

    return team;
  }

  /**
   * Dissolve a team — terminate all member sessions.
   */
  dissolveTeam(teamId: string): void {
    const team = this.teams.get(teamId);
    if (!team) return;

    this.agent.terminateSession(team.leaderId);
    for (const memberId of team.memberIds) {
      this.agent.terminateSession(memberId);
    }

    this.teams.delete(teamId);
    log.info({ teamId }, "Agent team dissolved");
  }

  // -----------------------------------------------------------------------
  // Task Execution
  // -----------------------------------------------------------------------

  /**
   * Send a task to the team leader.
   * The leader can delegate to members via the mailbox.
   */
  async *sendTask(teamId: string, task: string): AsyncGenerator<AgentEvent> {
    const team = this.teams.get(teamId);
    if (!team) {
      yield { kind: "error", message: `Team not found: ${teamId}` };
      return;
    }

    team.status = "running";

    try {
      for await (const event of this.agent.sendMessage(team.leaderId, task)) {
        yield event;
      }
    } catch (err) {
      team.status = "error";
      throw err;
    }

    team.status = "idle";
  }

  /**
   * Send a message directly to a specific team member.
   */
  async *sendToMember(
    teamId: string,
    nodeId: string,
    message: string,
  ): AsyncGenerator<AgentEvent> {
    const team = this.teams.get(teamId);
    if (!team) {
      yield { kind: "error", message: `Team not found: ${teamId}` };
      return;
    }

    const sessionId = team.nodeMap.get(nodeId);
    if (!sessionId) {
      yield { kind: "error", message: `Node ${nodeId} not in team ${teamId}` };
      return;
    }

    for await (const event of this.agent.sendMessage(sessionId, message)) {
      yield event;
    }
  }

  // -----------------------------------------------------------------------
  // Mailbox
  // -----------------------------------------------------------------------

  /**
   * Post a message to the team mailbox.
   */
  postMessage(teamId: string, from: string, to: string, content: string): TeamMessage {
    const team = this.teams.get(teamId);
    if (!team) throw new Error(`Team not found: ${teamId}`);

    const msg: TeamMessage = {
      id: `msg-${++this.messageCounter}`,
      from,
      to,
      content,
      timestamp: Date.now(),
      read: false,
    };

    team.mailbox.push(msg);
    return msg;
  }

  /**
   * Get unread messages for a specific member.
   */
  getUnread(teamId: string, sessionId: string): TeamMessage[] {
    const team = this.teams.get(teamId);
    if (!team) return [];

    return team.mailbox.filter(
      (m) => !m.read && (m.to === sessionId || m.to === "all"),
    );
  }

  /**
   * Mark messages as read.
   */
  markRead(teamId: string, messageIds: string[]): void {
    const team = this.teams.get(teamId);
    if (!team) return;

    const idSet = new Set(messageIds);
    for (const msg of team.mailbox) {
      if (idSet.has(msg.id)) msg.read = true;
    }
  }

  // -----------------------------------------------------------------------
  // Status
  // -----------------------------------------------------------------------

  /**
   * Get team status.
   */
  getStatus(teamId: string): TeamStatus | null {
    const team = this.teams.get(teamId);
    if (!team) return null;

    const leaderNodeId = [...team.nodeMap.entries()]
      .find(([, sid]) => sid === team.leaderId)?.[0] ?? "merged";

    return {
      teamId: team.id,
      status: team.status,
      leader: { sessionId: team.leaderId, nodeId: leaderNodeId },
      members: [...team.nodeMap.entries()].map(([nodeId, sessionId]) => ({
        sessionId,
        nodeId,
      })),
      mailboxSize: team.mailbox.length,
      unreadCount: team.mailbox.filter((m) => !m.read).length,
    };
  }

  /**
   * List all active teams.
   */
  listTeams(): TeamStatus[] {
    return [...this.teams.keys()]
      .map((id) => this.getStatus(id))
      .filter((s): s is TeamStatus => s !== null);
  }

  // -----------------------------------------------------------------------
  // Internal
  // -----------------------------------------------------------------------

  private async fetchContext(
    sessionId: string,
    nodeIds: string[],
    role: string,
    appId: string,
  ): Promise<ComposedContext> {
    if (this.grpcClient) {
      return this.grpcClient.getBootstrap({ sessionId, nodeIds, role, appId });
    }
    throw new Error("gRPC client required for team context fetching");
  }
}
