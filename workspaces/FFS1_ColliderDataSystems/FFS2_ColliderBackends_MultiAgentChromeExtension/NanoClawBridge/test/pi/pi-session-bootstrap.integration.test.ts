import { describe, expect, it } from "vitest";
import { ContextGrpcClient } from "../../src/grpc/context-client.js";

const RUN_INTEGRATION = process.env.RUN_PI_INTEGRATION === "1";

if (!RUN_INTEGRATION) {
    describe.skip("PI session bootstrap integration", () => {
        it("set RUN_PI_INTEGRATION=1 to run", () => {
            expect(true).toBe(true);
        });
    });
} else {
    describe("PI session bootstrap integration", () => {
        it("fetches composed context over gRPC GetBootstrap", async () => {
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
                    sessionId: `pi-int-${Date.now()}`,
                    nodeIds: [nodeId],
                    role,
                    appId,
                    inheritAncestors: true,
                });

                expect(context.session_meta.app_id).toBe(appId);
                expect(context.session_meta.role).toBe(role);
                expect(Array.isArray(context.tool_schemas)).toBe(true);
                expect(context.agents_md.length + context.soul_md.length + context.tools_md.length).toBeGreaterThan(0);
            } finally {
                client.close();
            }
        }, 20_000);
    });
}
