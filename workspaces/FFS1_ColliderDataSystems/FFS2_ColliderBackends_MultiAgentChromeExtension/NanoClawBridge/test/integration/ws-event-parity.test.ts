import { describe, expect, it } from "vitest";
import { WsBridge } from "../../src/ws-bridge.js";
import type { AgentEvent } from "../../src/event-parser.js";

function toFrame(event: AgentEvent): Record<string, unknown> {
    const bridge = Object.create(WsBridge.prototype) as {
        agentEventToFrame: (value: AgentEvent) => Record<string, unknown>;
    };
    return bridge.agentEventToFrame(event);
}

describe("WS Event Parity", () => {
    it("maps every canonical AgentEvent to stable websocket event frames", () => {
        const cases: Array<{ input: AgentEvent; expected: Record<string, unknown> }> = [
            {
                input: { kind: "text_delta", text: "hello" },
                expected: { type: "event", event: "text_delta", data: "hello" },
            },
            {
                input: { kind: "tool_use_start", name: "list_apps", args: '{"limit":1}' },
                expected: {
                    type: "event",
                    event: "tool_use_start",
                    data: { name: "list_apps", args: '{"limit":1}' },
                },
            },
            {
                input: { kind: "tool_result", name: "list_apps", result: "ok" },
                expected: {
                    type: "event",
                    event: "tool_result",
                    data: { name: "list_apps", result: "ok" },
                },
            },
            {
                input: { kind: "thinking", text: "hmm" },
                expected: { type: "event", event: "thinking", data: "hmm" },
            },
            {
                input: { kind: "message_end" },
                expected: { type: "event", event: "message_end" },
            },
            {
                input: { kind: "error", message: "boom" },
                expected: { type: "event", event: "error", message: "boom" },
            },
        ];

        for (const testCase of cases) {
            expect(toFrame(testCase.input)).toEqual(testCase.expected);
        }
    });

    it("preserves event-name contract used by frontend consumers", () => {
        const names = [
            toFrame({ kind: "text_delta", text: "x" }).event,
            toFrame({ kind: "tool_use_start", name: "tool", args: "{}" }).event,
            toFrame({ kind: "tool_result", name: "tool", result: "ok" }).event,
            toFrame({ kind: "thinking", text: "..." }).event,
            toFrame({ kind: "message_end" }).event,
            toFrame({ kind: "error", message: "fail" }).event,
        ];

        expect(names).toEqual([
            "text_delta",
            "tool_use_start",
            "tool_result",
            "thinking",
            "message_end",
            "error",
        ]);
    });
});
