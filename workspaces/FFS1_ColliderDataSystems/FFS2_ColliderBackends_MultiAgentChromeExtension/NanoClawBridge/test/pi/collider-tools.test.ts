import { afterEach, describe, expect, it, vi } from "vitest";
import { buildColliderToolsExtension } from "../../src/pi/extensions/collider-tools.js";
import type { ComposedContext } from "../../src/sdk/types.js";

function makeContext(): ComposedContext {
    return {
        agents_md: "",
        soul_md: "",
        tools_md: "",
        skills: [],
        tool_schemas: [
            {
                type: "function",
                function: {
                    name: "list_apps",
                    description: "List apps",
                    parameters: {
                        type: "object",
                        properties: {},
                    },
                },
            },
        ],
        mcp_servers: [],
        session_meta: {
            role: "superadmin",
            app_id: "app-1",
            composed_nodes: ["node-1"],
            username: "Sam",
        },
    };
}

describe("collider-tools extension", () => {
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("registers tools and executes via DataServer endpoint", async () => {
        const fetchMock = vi
            .spyOn(globalThis, "fetch")
            .mockResolvedValue({
                ok: true,
                json: async () => ({ apps: [] }),
            } as unknown as Response);

        const extension = buildColliderToolsExtension({
            context: makeContext(),
        });

        expect(extension.toolNames).toContain("list_apps");

        const result = await extension.executeTool("list_apps", {});
        expect(result.name).toBe("list_apps");
        expect(result.isError).toBe(false);
        expect(result.result).toContain("apps");
        expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("rejects unknown tools", async () => {
        const extension = buildColliderToolsExtension({
            context: makeContext(),
        });

        await expect(extension.executeTool("unknown_tool", {})).rejects.toThrow(/Unknown PI tool/i);
    });
});
