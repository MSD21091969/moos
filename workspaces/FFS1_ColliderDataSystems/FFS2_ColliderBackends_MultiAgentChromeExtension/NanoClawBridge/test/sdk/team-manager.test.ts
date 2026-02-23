import { describe, it, expect, vi, beforeEach } from "vitest";
import { TeamManager } from "../../src/sdk/team-manager.js";
import type { AnthropicAgent } from "../../src/sdk/anthropic-agent.js";
import type { ContextGrpcClient } from "../../src/grpc/context-client.js";

function createMockAgent(): AnthropicAgent {
    return {
        createSession: vi.fn(),
        resumeSession: vi.fn(),
        injectContext: vi.fn(),
        terminateSession: vi.fn(),
        getHistory: vi.fn(),
        sendMessage: vi.fn().mockImplementation(async function* () {
            yield { kind: "text_delta", text: "Mock response" };
            yield { kind: "message_end" };
        })
    } as unknown as AnthropicAgent;
}

function createMockGrpcClient(): ContextGrpcClient {
    return {
        getBootstrap: vi.fn().mockResolvedValue({
            agents_md: "mock",
            soul_md: "mock",
            tools_md: "mock",
            skills: [],
            tool_schemas: [],
            mcp_servers: [],
            session_meta: { role: "test", app_id: "test", composed_nodes: [], username: "test" }
        }),
        streamContext: vi.fn(),
    } as unknown as ContextGrpcClient;
}

describe("TeamManager", () => {
    let agent: AnthropicAgent;
    let grpcClient: ContextGrpcClient;
    let manager: TeamManager;

    beforeEach(() => {
        vi.clearAllMocks();
        agent = createMockAgent();
        grpcClient = createMockGrpcClient();
        manager = new TeamManager(agent, grpcClient);
    });

    describe("Team Lifecycle", () => {
        it("should create a team with leader and members", async () => {
            const team = await manager.createTeam({
                teamId: "test-team",
                nodeIds: ["node-A", "node-B"],
                role: "admin",
                appId: "app-1",
            });

            expect(team.id).toBe("test-team");
            expect(team.leaderId).toBe("test-team-leader");
            expect(team.memberIds).toEqual(["test-team-node-A", "test-team-node-B"]);

            // Grpc should be called 3 times (1 leader + 2 members)
            expect(grpcClient.getBootstrap).toHaveBeenCalledTimes(3);

            // Agent createSession should be called 3 times
            expect(agent.createSession).toHaveBeenCalledTimes(3);
        });

        it("should dissolve a team and terminate sessions", async () => {
            await manager.createTeam({
                teamId: "test-team",
                nodeIds: ["node-A", "node-B"],
                role: "admin",
                appId: "app-1",
            });

            manager.dissolveTeam("test-team");

            // Verify terminateSession called for leader and 2 members
            expect(agent.terminateSession).toHaveBeenCalledTimes(3);

            const status = manager.getStatus("test-team");
            expect(status).toBe(null);
        });

        it("should throw if less than 2 nodes are provided", async () => {
            await expect(
                manager.createTeam({ teamId: "x", nodeIds: ["node-A"], role: "a", appId: "b" })
            ).rejects.toThrow(/requires at least 2 nodes/);
        });
    });

    describe("Task Execution and Mailbox", () => {
        beforeEach(async () => {
            await manager.createTeam({
                teamId: "team-1",
                nodeIds: ["node-1", "node-2"],
                role: "admin",
                appId: "app-1",
            });
        });

        it("should send task to leader", async () => {
            const events = [];
            const generator = manager.sendTask("team-1", "Do work");
            for await (const event of generator) {
                events.push(event);
            }
            expect(events).toHaveLength(2); // text_delta, message_end
            expect(agent.sendMessage).toHaveBeenCalledWith("team-1-leader", "Do work");
        });

        it("should send direct message to member", async () => {
            const events = [];
            const generator = manager.sendToMember("team-1", "node-2", "Direct msg");
            for await (const event of generator) {
                events.push(event);
            }
            expect(agent.sendMessage).toHaveBeenCalledWith("team-1-node-2", "Direct msg");
        });

        it("should post and retrieve mailbox messages", () => {
            // Leader posts to node-1
            const msg = manager.postMessage("team-1", "team-1-leader", "team-1-node-1", "Hello Node 1");
            expect(msg.id).toBe("msg-1");

            // Node 1 checks unread
            const unread = manager.getUnread("team-1", "team-1-node-1");
            expect(unread).toHaveLength(1);
            expect(unread[0].content).toBe("Hello Node 1");

            // Node 2 checks unread (should be 0)
            const unreadNode2 = manager.getUnread("team-1", "team-1-node-2");
            expect(unreadNode2).toHaveLength(0);

            // Node 1 reads message
            manager.markRead("team-1", [msg.id]);

            const unreadAfter = manager.getUnread("team-1", "team-1-node-1");
            expect(unreadAfter).toHaveLength(0);
        });
    });
});
