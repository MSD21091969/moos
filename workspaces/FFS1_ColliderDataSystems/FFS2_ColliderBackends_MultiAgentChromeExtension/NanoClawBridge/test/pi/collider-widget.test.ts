import { describe, expect, it } from "vitest";
import { buildColliderContextExtension } from "../../src/pi/extensions/collider-context.js";
import { buildColliderWidgetExtension } from "../../src/pi/extensions/collider-widget.js";
import type { ComposedContext } from "../../src/sdk/types.js";

function makeContext(): ComposedContext {
    return {
        agents_md: "Agent instructions",
        soul_md: "Rules",
        tools_md: "Knowledge",
        skills: [
            {
                name: "skill-a",
                description: "A",
                markdown_body: "A",
                user_invocable: true,
                model_invocable: true,
            },
        ],
        tool_schemas: [
            {
                type: "function",
                function: {
                    name: "list_apps",
                    description: "List apps",
                    parameters: { type: "object", properties: {} },
                },
            },
        ],
        mcp_servers: [],
        session_meta: {
            role: "superadmin",
            app_id: "app-2xz",
            composed_nodes: ["node-1"],
            username: "Sam",
        },
    };
}

describe("collider-widget extension", () => {
    it("builds footer widget content with identity and counts", () => {
        const contextState = buildColliderContextExtension({
            sessionId: "session-widget-1234",
            context: makeContext(),
        });

        const widget = buildColliderWidgetExtension(contextState);
        expect(widget.position).toBe("footer");
        expect(widget.skillCount).toBe(1);
        expect(widget.toolCount).toBe(1);
        expect(widget.content).toContain("session-");
        expect(widget.content).toContain("skills:1");
        expect(widget.content).toContain("tools:1");
    });
});
