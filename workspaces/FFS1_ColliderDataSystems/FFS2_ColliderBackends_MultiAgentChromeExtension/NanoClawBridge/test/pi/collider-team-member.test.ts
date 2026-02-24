import { describe, expect, it } from "vitest";
import { buildColliderTeamMemberExtension } from "../../src/pi/extensions/collider-team-member.js";

describe("collider-team-member extension", () => {
    it("enables member mode for single-node sessions", () => {
        const ext = buildColliderTeamMemberExtension({
            sessionId: "member-session-1",
            nodeIds: ["node-a"],
        });

        expect(ext.enabled).toBe(true);
        expect(ext.nodeId).toBe("node-a");
        expect(ext.reportResult("done")).toContain("mailbox.report");
    });

    it("disables member mode for multi-node sessions", () => {
        const ext = buildColliderTeamMemberExtension({
            sessionId: "leader-session-1",
            nodeIds: ["node-a", "node-b"],
        });

        expect(ext.enabled).toBe(false);
        expect(ext.nodeId).toBeUndefined();
        expect(() => ext.reportResult("x")).toThrow(/disabled/i);
    });
});
