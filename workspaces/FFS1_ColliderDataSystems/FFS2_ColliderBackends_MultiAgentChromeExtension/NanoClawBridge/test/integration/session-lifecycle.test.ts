import { describe, it, expect, vi, beforeEach } from "vitest";
import { AnthropicAgent } from "../../src/sdk/anthropic-agent.js";
import type { ComposedContext } from "../../src/sdk/types.js";

// ---------------------------------------------------------------------------
// Mock Anthropic SDK
// ---------------------------------------------------------------------------
vi.mock("@anthropic-ai/sdk", () => {
    return {
        default: class MockAnthropic {
            messages = {
                stream: vi.fn().mockImplementation(() => {
                    const mockStream = {
                        on: vi.fn(),
                        [Symbol.asyncIterator]: async function* () {
                            yield { type: "content_block_delta", delta: { type: "text_delta", text: "Hello from " } };
                            yield { type: "content_block_delta", delta: { type: "text_delta", text: "mock agent!" } };
                        },
                        finalMessage: vi.fn().mockResolvedValue({
                            content: [{ type: "text", text: "Hello from mock agent!" }]
                        })
                    };
                    return mockStream;
                })
            };
        }
    };
});

function makeContext(): ComposedContext {
    return {
        agents_md: "# Agent Instructions\nYou are a mock agent.",
        soul_md: "# Soul\nBe helpful.",
        tools_md: "# Tools\nNone",
        skills: [],
        tool_schemas: [],
        mcp_servers: [],
        session_meta: {
            role: "app_user",
            app_id: "test-app",
            composed_nodes: ["node-1"],
            username: "test-user",
        },
    };
}

describe("AnthropicAgent Session Lifecycle", () => {
    let agent: AnthropicAgent;

    beforeEach(() => {
        vi.clearAllMocks();
        agent = new AnthropicAgent({ apiKey: "test-key" });
    });

    it("should create a session, send a message, capture stream, and terminate", async () => {
        const sessionId = "session-123";
        const context = makeContext();

        // 1. Establish a session
        agent.createSession({
            sessionId,
            context,
            model: "test-model"
        });

        // Verify session state
        const history1 = agent.getHistory(sessionId);
        expect(history1).toHaveLength(0); // Starts empty

        // 2. Send a mock message and capture streaming output
        const events = [];
        const messageGenerator = agent.sendMessage(sessionId, "Hi agent!");

        for await (const event of messageGenerator) {
            events.push(event);
        }

        // Ensure we collected text deltas
        const textDeltas = events.filter(e => e.kind === "text_delta");
        expect(textDeltas).toHaveLength(2);
        // Ensure we got the message_end event
        expect(events.some(e => e.kind === "message_end")).toBe(true);

        // Verify conversation history was updated
        const history2 = agent.getHistory(sessionId);
        expect(history2).toHaveLength(2); // user msg + assistant msg

        // Check user msg
        expect(history2[0].role).toBe("user");
        expect(history2[0].content).toBe("Hi agent!");

        // Check assistant msg
        expect(history2[1].role).toBe("assistant");
        expect(history2[1].content[0].type).toBe("text");
        expect(history2[1].content[0].text).toBe("Hello from mock agent!");

        // 3. Terminate session (clean up)
        agent.terminateSession(sessionId);

        // Using expect().toThrow since session should no longer exist
        expect(() => agent.getHistory(sessionId)).toThrow(/Session not found/);
    });

    it("should inject context mid-session", () => {
        const sessionId = "session-update-123";
        const context = makeContext();

        agent.createSession({
            sessionId,
            context
        });

        agent.injectContext(sessionId, {
            type: "system_prompt",
            section: "agents_md",
            content: "# UPDATED instructions",
            operation: "replace",
        });

        // Ensure it doesn't throw and stays alive
        const history = agent.getHistory(sessionId);
        expect(history).toBeDefined();

        // We cannot easily inspect the internal system prompt without hitting private properties,
        // but the success of the call shows it did not crash.
        agent.terminateSession(sessionId);
    });
});
