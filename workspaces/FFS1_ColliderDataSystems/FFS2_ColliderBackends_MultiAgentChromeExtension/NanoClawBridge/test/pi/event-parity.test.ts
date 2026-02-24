import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AnthropicAgent } from "../../src/sdk/anthropic-agent.js";
import { PiAdapter } from "../../src/pi/pi-adapter.js";
import type { AgentEvent } from "../../src/event-parser.js";
import type { ComposedContext } from "../../src/sdk/types.js";

let mockMode: "text" | "tool" = "text";
let streamCallCount = 0;

vi.mock("@anthropic-ai/sdk", () => {
    function buildStreamForText() {
        return {
            on: vi.fn(),
            [Symbol.asyncIterator]: async function* () {
                yield {
                    type: "content_block_delta",
                    delta: { type: "text_delta", text: "hello" },
                };
            },
            finalMessage: vi.fn().mockResolvedValue({
                content: [{ type: "text", text: "hello" }],
            }),
        };
    }

    function buildStreamForToolTurn(turn: number) {
        if (turn === 1) {
            return {
                on: vi.fn(),
                [Symbol.asyncIterator]: async function* () {
                    yield {
                        type: "content_block_start",
                        content_block: {
                            type: "tool_use",
                            id: "tool-1",
                            name: "list_apps",
                            input: {},
                        },
                    };
                },
                finalMessage: vi.fn().mockResolvedValue({
                    content: [
                        {
                            type: "tool_use",
                            id: "tool-1",
                            name: "list_apps",
                            input: {},
                        },
                    ],
                }),
            };
        }

        return {
            on: vi.fn(),
            [Symbol.asyncIterator]: async function* () {
                yield {
                    type: "content_block_delta",
                    delta: { type: "text_delta", text: "done" },
                };
            },
            finalMessage: vi.fn().mockResolvedValue({
                content: [{ type: "text", text: "done" }],
            }),
        };
    }

    return {
        default: class MockAnthropic {
            messages = {
                stream: vi.fn().mockImplementation(() => {
                    streamCallCount += 1;
                    if (mockMode === "tool") {
                        return buildStreamForToolTurn(streamCallCount);
                    }
                    return buildStreamForText();
                }),
            };
        },
    };
});

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

async function collectKinds(stream: AsyncGenerator<AgentEvent>): Promise<string[]> {
    const kinds: string[] = [];
    for await (const event of stream) {
        kinds.push(event.kind);
    }
    return kinds;
}

describe("PI vs Anthropic event parity", () => {
    beforeEach(() => {
        mockMode = "text";
        streamCallCount = 0;
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("emits matching text/message-end event classes for text-only flows", async () => {
        const anthropic = new AnthropicAgent({ apiKey: "test-key" });
        const pi = new PiAdapter();

        anthropic.createSession({
            sessionId: "anth-text",
            context: makeContext(),
        });
        pi.createSession({
            sessionId: "pi-text",
            context: makeContext(),
        });

        const anthKinds = await collectKinds(anthropic.sendMessage("anth-text", "hello"));
        const piKinds = await collectKinds(pi.sendMessage("pi-text", "hello"));

        expect(anthKinds).toContain("text_delta");
        expect(anthKinds[anthKinds.length - 1]).toBe("message_end");

        expect(piKinds).toContain("text_delta");
        expect(piKinds[piKinds.length - 1]).toBe("message_end");
    });

    it("emits matching tool/message-end event classes for tool flows", async () => {
        mockMode = "tool";

        const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            json: async () => ({ ok: true }),
        } as unknown as Response);

        const toolContext = makeContext({
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
        });

        const anthropic = new AnthropicAgent({ apiKey: "test-key" });
        const pi = new PiAdapter();

        anthropic.createSession({
            sessionId: "anth-tool",
            context: toolContext,
        });
        pi.createSession({
            sessionId: "pi-tool",
            context: toolContext,
        });

        const anthKinds = await collectKinds(anthropic.sendMessage("anth-tool", "use list_apps"));
        const piKinds = await collectKinds(pi.sendMessage("pi-tool", "/tool list_apps {}"));

        for (const expectedKind of ["tool_use_start", "tool_result", "message_end"]) {
            expect(anthKinds).toContain(expectedKind);
            expect(piKinds).toContain(expectedKind);
        }

        expect(fetchMock).toHaveBeenCalled();
    });
});
