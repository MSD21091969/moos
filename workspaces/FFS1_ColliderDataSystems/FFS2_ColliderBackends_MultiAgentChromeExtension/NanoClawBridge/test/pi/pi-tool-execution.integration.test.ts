import { describe, expect, it } from "vitest";
import { ContextGrpcClient } from "../../src/grpc/context-client.js";
import { PiAdapter } from "../../src/pi/pi-adapter.js";
import type { AgentEvent } from "../../src/event-parser.js";

const RUN_INTEGRATION = process.env.RUN_PI_INTEGRATION === "1";

async function collectEvents(stream: AsyncGenerator<AgentEvent>): Promise<AgentEvent[]> {
    const events: AgentEvent[] = [];
    for await (const event of stream) {
        events.push(event);
    }
    return events;
}

if (!RUN_INTEGRATION) {
    describe.skip("PI tool execution integration", () => {
        it("set RUN_PI_INTEGRATION=1 to run", () => {
            expect(true).toBe(true);
        });
    });
} else {
    describe("PI tool execution integration", () => {
        it("executes one real Collider tool via DataServer route", async () => {
            const grpcAddress = process.env.GRPC_CONTEXT_ADDRESS ?? "localhost:50051";
            const appId =
                process.env.PI_INTEGRATION_APP_ID ??
                "c57ab23a-4a57-4b28-a34c-9700320565ea";
            const nodeId =
                process.env.PI_INTEGRATION_NODE_ID ??
                "9848b323-5e65-4179-a1d6-5b99be9f8b87";
            const role = process.env.PI_INTEGRATION_ROLE ?? "superadmin";

            const client = new ContextGrpcClient(grpcAddress);
            try {
                const context = await client.getBootstrap({
                    sessionId: `pi-int-tool-${Date.now()}`,
                    nodeIds: [nodeId],
                    role,
                    appId,
                    inheritAncestors: true,
                });

                expect(context.tool_schemas.length).toBeGreaterThan(0);
                const toolName = context.tool_schemas[0].function.name;

                const adapter = new PiAdapter();
                const sessionId = adapter.createSession({
                    sessionId: `pi-tool-${Date.now()}`,
                    context,
                });

                const events = await collectEvents(
                    adapter.sendMessage(sessionId, `/tool ${toolName} {}`),
                );

                expect(events[0]).toMatchObject({ kind: "tool_use_start", name: toolName });
                expect(events.some((event) => event.kind === "tool_result")).toBe(true);
                expect(events[events.length - 1]).toEqual({ kind: "message_end" });
            } finally {
                client.close();
            }
        }, 25_000);
    });
}
