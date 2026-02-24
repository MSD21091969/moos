import { afterEach, describe, expect, it, vi } from "vitest";
import { PiAdapter } from "../../src/pi/pi-adapter.js";
import type { ComposedContext } from "../../src/sdk/types.js";
import type { AgentEvent } from "../../src/event-parser.js";

function makeContext(overrides?: Partial<ComposedContext>): ComposedContext {
    return {
        agents_md: "Agent instructions",
        soul_md: "Rules",
        tools_md: "Knowledge",
        skills: [],
        tool_schemas: [],
        mcp_servers: [],
        session_meta: {
            role: "superadmin",
            app_id: "app-2xz",
            composed_nodes: ["node-1"],
            username: "Sam",
        },
        ...overrides,
    };
}

async function collectEvents(stream: AsyncGenerator<AgentEvent>): Promise<AgentEvent[]> {
    const events: AgentEvent[] = [];
    for await (const event of stream) {
        events.push(event);
    }
    return events;
}

describe("PiAdapter", () => {
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("creates session, emits canonical events, and tracks history", async () => {
        const adapter = new PiAdapter();
        const sessionId = adapter.createSession({
            sessionId: "pi-session-1",
            context: makeContext(),
        });

        const events = await collectEvents(adapter.sendMessage(sessionId, "hello pi"));

        const textEvent = events.find((event) => event.kind === "text_delta");
        expect(textEvent?.kind).toBe("text_delta");
        if (textEvent?.kind === "text_delta") {
            expect(textEvent.text).toContain("PI runtime stub response");
            expect(textEvent.text).toContain("Widget:");
            expect(textEvent.text).toContain("Structured workspace prompt: enabled");
        }
        expect(events[events.length - 1]).toEqual({ kind: "message_end" });
        expect(adapter.hasHistory(sessionId)).toBe(true);
    });

    it("executes slash-tool command and emits tool events", async () => {
        const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            json: async () => ({ ok: true }),
        } as unknown as Response);

        const adapter = new PiAdapter();
        const sessionId = adapter.createSession({
            sessionId: "pi-session-tool",
            context: makeContext({
                tool_schemas: [
                    {
                        type: "function",
                        function: {
                            name: "list_apps",
                            description: "List applications",
                            parameters: { type: "object", properties: {} },
                        },
                    },
                ],
            }),
        });

        const events = await collectEvents(
            adapter.sendMessage(sessionId, '/tool list_apps {"token":"sk-1234567890ABCDEF1234567890","limit":1}'),
        );

        expect(events[0]).toMatchObject({ kind: "tool_use_start", name: "list_apps" });
        expect(events.some((event) => event.kind === "tool_result")).toBe(true);
        expect(events[events.length - 1]).toEqual({ kind: "message_end" });
        const args = JSON.parse(
            (events.find((event) => event.kind === "tool_use_start") as { kind: "tool_use_start"; args: string }).args,
        );
        expect(JSON.stringify(args)).toContain("[REDACTED]");
        expect(fetchMock).toHaveBeenCalled();
    });

    it("blocks policy-forbidden tool commands", async () => {
        const adapter = new PiAdapter();
        const sessionId = adapter.createSession({
            sessionId: "pi-session-policy-block",
            context: makeContext({
                tool_schemas: [
                    {
                        type: "function",
                        function: {
                            name: "list_apps",
                            description: "List applications",
                            parameters: { type: "object", properties: {} },
                        },
                    },
                ],
            }),
        });

        const events = await collectEvents(
            adapter.sendMessage(sessionId, '/tool delete_app {"id":"1"}'),
        );

        expect(events[0]).toMatchObject({ kind: "error" });
        expect(events[events.length - 1]).toEqual({ kind: "message_end" });
    });

    it("blocks dangerous bash commands via policy", async () => {
        const adapter = new PiAdapter();
        const sessionId = adapter.createSession({
            sessionId: "pi-session-bash-block",
            context: makeContext(),
        });

        const events = await collectEvents(
            adapter.sendMessage(sessionId, "/bash rm -rf /tmp/test"),
        );

        expect(events[0]).toMatchObject({ kind: "error" });
        expect(events[events.length - 1]).toEqual({ kind: "message_end" });
    });

    it("accepts safe bash command and emits text + message_end", async () => {
        const adapter = new PiAdapter();
        const sessionId = adapter.createSession({
            sessionId: "pi-session-bash-ok",
            context: makeContext(),
        });

        const events = await collectEvents(
            adapter.sendMessage(sessionId, "/bash echo hello"),
        );

        expect(events[0]).toMatchObject({ kind: "text_delta" });
        expect(events[events.length - 1]).toEqual({ kind: "message_end" });
    });

    it("applies context delta updates to session state", async () => {
        const adapter = new PiAdapter();
        const sessionId = adapter.createSession({
            sessionId: "pi-session-2",
            context: makeContext(),
        });

        adapter.injectContext(sessionId, {
            type: "full_replace",
            context: makeContext({
                session_meta: {
                    role: "app_user",
                    app_id: "app-changed",
                    composed_nodes: ["node-2"],
                    username: "Alex",
                },
            }),
        });

        const events = await collectEvents(adapter.sendMessage(sessionId, "check role"));
        const text = events
            .filter((event): event is Extract<AgentEvent, { kind: "text_delta" }> => event.kind === "text_delta")
            .map((event) => event.text)
            .join(" ");

        expect(text).toContain("Role: app_user");
        expect(text).toContain("Application: app-changed");
        expect(text).toContain("Structured workspace prompt: enabled");
    });

    it("enables team leader mode for multi-node sessions", async () => {
        const adapter = new PiAdapter();
        const sessionId = adapter.createSession({
            sessionId: "pi-session-team-leader",
            context: makeContext({
                session_meta: {
                    role: "superadmin",
                    app_id: "app-team",
                    composed_nodes: ["node-1", "node-2", "node-3"],
                    username: "Sam",
                },
            }),
        });

        const events = await collectEvents(adapter.sendMessage(sessionId, "team status"));
        const text = events
            .filter((event): event is Extract<AgentEvent, { kind: "text_delta" }> => event.kind === "text_delta")
            .map((event) => event.text)
            .join(" ");

        expect(text).toContain("Team leader mode");
        expect(text).toContain("Coordinator:");
    });

    it("enables team member mode for single-node sessions", async () => {
        const adapter = new PiAdapter();
        const sessionId = adapter.createSession({
            sessionId: "pi-session-team-member",
            context: makeContext({
                session_meta: {
                    role: "app_user",
                    app_id: "app-member",
                    composed_nodes: ["node-member"],
                    username: "Sam",
                },
            }),
        });

        const events = await collectEvents(adapter.sendMessage(sessionId, "member status"));
        const text = events
            .filter((event): event is Extract<AgentEvent, { kind: "text_delta" }> => event.kind === "text_delta")
            .map((event) => event.text)
            .join(" ");

        expect(text).toContain("Team member mode");
        expect(text).toContain("node-member");
    });

    it("emits error + message_end for unknown session and supports termination", async () => {
        const adapter = new PiAdapter();

        const unknownEvents = await collectEvents(adapter.sendMessage("missing-session", "hello"));
        expect(unknownEvents[0]).toMatchObject({ kind: "error" });
        expect(unknownEvents[unknownEvents.length - 1]).toEqual({ kind: "message_end" });

        const sessionId = adapter.createSession({
            sessionId: "pi-session-3",
            context: makeContext(),
        });
        adapter.terminateSession(sessionId);
        expect(adapter.hasHistory(sessionId)).toBe(false);
    });
});
