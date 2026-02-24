import crypto from "node:crypto";
import type { AgentEvent } from "../event-parser.js";
import type { IAgentSession } from "../sdk/agent-session.js";
import type { ContextDelta, SdkSessionConfig, StoredMessage } from "../sdk/types.js";
import {
    applyColliderContextDelta,
    buildColliderContextExtension,
    type ColliderContextExtensionState,
} from "./extensions/collider-context.js";
import {
    buildColliderToolsExtension,
    type ColliderToolsExtensionState,
} from "./extensions/collider-tools.js";
import {
    buildColliderWidgetExtension,
    type ColliderWidgetExtensionState,
} from "./extensions/collider-widget.js";
import {
    buildColliderPolicyExtension,
    type ColliderPolicyExtensionState,
} from "./extensions/collider-policy.js";
import {
    buildColliderTeamLeaderExtension,
    type ColliderTeamLeaderExtensionState,
} from "./extensions/collider-team-leader.js";
import {
    buildColliderTeamMemberExtension,
    type ColliderTeamMemberExtensionState,
} from "./extensions/collider-team-member.js";
import { resolvePiModel } from "./model-resolver.js";

interface PiSessionState {
    id: string;
    contextState: ColliderContextExtensionState;
    toolsState: ColliderToolsExtensionState;
    widgetState: ColliderWidgetExtensionState;
    policyState: ColliderPolicyExtensionState;
    teamLeaderState: ColliderTeamLeaderExtensionState;
    teamMemberState: ColliderTeamMemberExtensionState;
    provider: string;
    model: string;
    history: StoredMessage[];
    status: "idle" | "running" | "terminated";
}

export class PiAdapter implements IAgentSession {
    private sessions = new Map<string, PiSessionState>();

    createSession(config: SdkSessionConfig): string {
        const sessionId = config.sessionId || crypto.randomUUID();
        const existing = this.sessions.get(sessionId);
        if (existing) {
            return existing.id;
        }

        const contextState = buildColliderContextExtension({
            sessionId,
            context: config.context,
        });
        const toolsState = buildColliderToolsExtension({
            context: config.context,
        });
        const policyState = buildColliderPolicyExtension({
            allowedTools: toolsState.toolNames,
        });
        const teamLeaderState = buildColliderTeamLeaderExtension({
            sessionId,
            nodeIds: contextState.session.nodeIds,
        });
        const teamMemberState = buildColliderTeamMemberExtension({
            sessionId,
            nodeIds: contextState.session.nodeIds,
        });
        const widgetState = buildColliderWidgetExtension(contextState);
        const resolvedModel = resolvePiModel(config.model);

        this.sessions.set(sessionId, {
            id: sessionId,
            contextState,
            toolsState,
            widgetState,
            policyState,
            teamLeaderState,
            teamMemberState,
            provider: resolvedModel.provider,
            model: resolvedModel.model,
            history: [],
            status: "idle",
        });

        return sessionId;
    }

    async *sendMessage(sessionId: string, message: string): AsyncGenerator<AgentEvent> {
        const session = this.sessions.get(sessionId);
        if (!session || session.status === "terminated") {
            yield { kind: "error", message: `PI session not found: ${sessionId}` };
            yield { kind: "message_end" };
            return;
        }

        if (session.status === "running") {
            yield { kind: "error", message: "PI session is already processing a message" };
            yield { kind: "message_end" };
            return;
        }

        session.status = "running";
        session.history.push({ role: "user", content: message });

        try {
            const bashRequest = parseBashRequest(message);
            if (bashRequest) {
                const command = session.policyState.beforeBash(bashRequest.command);
                const text = `PI runtime stub bash accepted: ${command}`;
                yield { kind: "text_delta", text };
                session.history.push({ role: "assistant", content: text });
                yield { kind: "message_end" };
                return;
            }

            const toolRequest = parseToolRequest(message);
            if (toolRequest) {
                const policySafeInput = session.policyState.beforeTool(
                    toolRequest.name,
                    toolRequest.input,
                );

                yield {
                    kind: "tool_use_start",
                    name: toolRequest.name,
                    args: JSON.stringify(policySafeInput),
                };

                const toolResult = await session.toolsState.executeTool(
                    toolRequest.name,
                    policySafeInput,
                );

                session.policyState.afterTool(toolRequest.name, {
                    isError: toolResult.isError,
                });

                yield {
                    kind: "tool_result",
                    name: toolResult.name,
                    result: toolResult.result,
                };

                session.history.push({
                    role: "assistant",
                    content: toolResult.result,
                });

                yield { kind: "message_end" };
                return;
            }

            const nodeScope = session.contextState.session.nodeIds.join(", ") || "none";
            const text = [
                `PI runtime stub response (${session.provider}/${session.model}).`,
                `Role: ${session.contextState.session.role}.`,
                `Application: ${session.contextState.session.appId}.`,
                `Nodes: ${nodeScope}.`,
                `Structured workspace prompt: ${session.contextState.prompt.workspace ? "enabled" : "disabled"}.`,
                ...(session.teamLeaderState.enabled
                    ? [
                        `Team leader mode: ${session.teamLeaderState.memberCount} members.`,
                        `Coordinator: ${session.teamLeaderState.coordinatorSkill}.`,
                    ]
                    : []),
                ...(session.teamMemberState.enabled
                    ? [
                        `Team member mode: node=${session.teamMemberState.nodeId}.`,
                    ]
                    : []),
                `Widget: ${session.widgetState.content}.`,
                `Message received: ${message}`,
            ].join(" ");

            yield { kind: "text_delta", text };

            session.history.push({ role: "assistant", content: text });
            yield { kind: "message_end" };
        } catch (error) {
            const err = error instanceof Error ? error.message : String(error);
            yield { kind: "error", message: err };
            yield { kind: "message_end" };
        } finally {
            session.status = "idle";
        }
    }

    injectContext(sessionId: string, delta: ContextDelta): void {
        const session = this.getSession(sessionId);
        session.contextState = applyColliderContextDelta(session.contextState, delta);
        session.widgetState = buildColliderWidgetExtension(session.contextState);
    }

    terminateSession(sessionId: string): void {
        const session = this.sessions.get(sessionId);
        if (!session) return;
        session.status = "terminated";
        this.sessions.delete(sessionId);
    }

    hasHistory(sessionId: string): boolean {
        const session = this.sessions.get(sessionId);
        return !!session && session.history.length > 0;
    }

    private getSession(sessionId: string): PiSessionState {
        const session = this.sessions.get(sessionId);
        if (!session || session.status === "terminated") {
            throw new Error(`PI session not found: ${sessionId}`);
        }
        return session;
    }
}

function parseToolRequest(
    message: string,
): { name: string; input: Record<string, unknown> } | null {
    const trimmed = message.trim();
    if (!trimmed.startsWith("/tool ")) {
        return null;
    }

    const firstSpace = trimmed.indexOf(" ");
    const secondSpace = trimmed.indexOf(" ", firstSpace + 1);
    const name = secondSpace > 0
        ? trimmed.slice(firstSpace + 1, secondSpace).trim()
        : trimmed.slice(firstSpace + 1).trim();

    if (!name) {
        throw new Error("Invalid tool command. Use: /tool <name> <json-args>");
    }

    if (secondSpace < 0) {
        return { name, input: {} };
    }

    const rawInput = trimmed.slice(secondSpace + 1).trim();
    if (!rawInput) {
        return { name, input: {} };
    }

    let parsed: unknown;
    try {
        parsed = JSON.parse(rawInput);
    } catch {
        throw new Error("Tool args must be valid JSON object");
    }

    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("Tool args must be a JSON object");
    }

    return { name, input: parsed as Record<string, unknown> };
}

function parseBashRequest(message: string): { command: string } | null {
    const trimmed = message.trim();
    if (!trimmed.startsWith("/bash ")) {
        return null;
    }

    const command = trimmed.slice(6).trim();
    if (!command) {
        throw new Error("Invalid bash command. Use: /bash <command>");
    }

    return { command };
}
