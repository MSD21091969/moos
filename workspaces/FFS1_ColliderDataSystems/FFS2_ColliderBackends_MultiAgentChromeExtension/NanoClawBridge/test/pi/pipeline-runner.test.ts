import { describe, expect, it } from "vitest";
import { PiAdapter } from "../../src/pi/pi-adapter.js";
import { PipelineRunner } from "../../src/pi/pipeline-runner.js";
import type { ComposedContext } from "../../src/sdk/types.js";

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

describe("pipeline-runner", () => {
    it("runs steps sequentially and collects outputs", async () => {
        const runner = new PipelineRunner(new PiAdapter());

        const result = await runner.run({
            pipelineId: "pipe-1",
            context: makeContext(),
            steps: [
                { id: "one", prompt: "hello" },
                { id: "two", prompt: "world" },
            ],
        });

        expect(result.pipelineId).toBe("pipe-1");
        expect(result.steps).toHaveLength(2);
        expect(result.steps[0].id).toBe("one");
        expect(result.steps[0].hadError).toBe(false);
    });

    it("stops pipeline after error step", async () => {
        const runner = new PipelineRunner(new PiAdapter());

        const result = await runner.run({
            pipelineId: "pipe-err",
            context: makeContext(),
            steps: [
                { id: "bad", prompt: "/tool unknown {}" },
                { id: "after", prompt: "should not run" },
            ],
        });

        expect(result.steps).toHaveLength(1);
        expect(result.steps[0].hadError).toBe(true);
    });
});
