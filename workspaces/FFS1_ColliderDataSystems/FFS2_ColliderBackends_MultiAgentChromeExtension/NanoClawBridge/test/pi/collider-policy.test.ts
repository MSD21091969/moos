import { describe, expect, it } from "vitest";
import { buildColliderPolicyExtension } from "../../src/pi/extensions/collider-policy.js";

describe("collider-policy extension", () => {
    it("blocks tools outside allowlist", () => {
        const policy = buildColliderPolicyExtension({
            allowedTools: ["list_apps"],
        });

        expect(() => policy.beforeTool("delete_app", {})).toThrow(/tool not allowed/i);
    });

    it("redacts secrets before tool execution", () => {
        const policy = buildColliderPolicyExtension({
            allowedTools: ["list_apps"],
        });

        const redacted = policy.beforeTool("list_apps", {
            token: "sk-1234567890ABCDEF1234567890",
            nested: { auth: "api_key=abc123" },
        });

        expect(JSON.stringify(redacted)).toContain("[REDACTED]");
        expect(JSON.stringify(redacted)).not.toContain("abc123");
    });

    it("blocks dangerous bash commands", () => {
        const policy = buildColliderPolicyExtension({
            allowedTools: [],
        });

        expect(() => policy.beforeBash("rm -rf /tmp/x")).toThrow(/blocked bash command/i);
    });

    it("records tool audit entries", () => {
        const policy = buildColliderPolicyExtension({
            allowedTools: ["list_apps"],
        });

        policy.afterTool("list_apps", { isError: false });

        const trail = policy.getAuditTrail();
        expect(trail).toHaveLength(1);
        expect(trail[0].name).toBe("list_apps");
        expect(trail[0].isError).toBe(false);
    });
});
