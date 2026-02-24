import { describe, expect, it } from "vitest";
import {
    applyColliderContextDelta,
    buildColliderContextExtension,
} from "../../src/pi/extensions/collider-context.js";
import type { ComposedContext } from "../../src/sdk/types.js";

function makeSkill(index: number, markdownLength = 0) {
    const suffix = "x".repeat(markdownLength);
    return {
        name: `skill-${index}`,
        description: `Skill ${index}`,
        markdown_body: `Body ${index}${suffix}`,
        user_invocable: true,
        model_invocable: true,
        invocation_policy: "auto" as const,
        requires_bins: [],
        requires_env: [],
        scope: "local" as const,
        tool_ref: `tool-${index}`,
    };
}

function makeContext(overrides?: Partial<ComposedContext>): ComposedContext {
    return {
        agents_md: "Agent instructions",
        soul_md: "Rules",
        tools_md: "Knowledge",
        skills: [makeSkill(1), makeSkill(2), makeSkill(3), makeSkill(4)],
        tool_schemas: [],
        mcp_servers: [],
        session_meta: {
            role: "superadmin",
            app_id: "app-2xz",
            composed_nodes: ["node-a", "node-b"],
            username: "Sam",
        },
        ...overrides,
    };
}

describe("collider-context extension", () => {
    it("applies existing skill ranking policy and summarizes overflow", () => {
        const context = makeContext();
        const state = buildColliderContextExtension({
            sessionId: "session-1",
            context,
        });

        expect(state.skills.modelInvocable).toBe(4);
        expect(state.skills.full.length).toBeLessThanOrEqual(3);
        expect(state.skills.summarized.length).toBe(1);
        expect(state.session.sessionId).toBe("session-1");
        expect(state.session.nodeIds).toEqual(["node-a", "node-b"]);
        expect(state.prompt.workspace).toContain("# Workspace Context");
        expect(state.prompt.system).toContain("# Session Context");
    });

    it("updates extension state with context deltas", () => {
        const base = buildColliderContextExtension({
            sessionId: "session-1",
            context: makeContext({ skills: [makeSkill(1), makeSkill(2)] }),
        });

        const updated = applyColliderContextDelta(base, {
            type: "skill",
            operation: "add",
            skill: makeSkill(99),
        });

        expect(updated.skills.modelInvocable).toBe(3);
        expect(updated.context.skills.some((skill) => skill.name === "skill-99")).toBe(true);
        expect(updated.prompt.workspace).toContain("# Workspace Context");
    });
});
