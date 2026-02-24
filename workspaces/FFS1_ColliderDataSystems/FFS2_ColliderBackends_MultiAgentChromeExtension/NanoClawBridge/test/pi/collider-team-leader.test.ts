import { describe, expect, it } from "vitest";
import { buildColliderTeamLeaderExtension } from "../../src/pi/extensions/collider-team-leader.js";

describe("collider-team-leader extension", () => {
    it("enables coordinator mode for multi-node sessions", () => {
        const ext = buildColliderTeamLeaderExtension({
            sessionId: "team-session-1",
            nodeIds: ["node-a", "node-b", "node-c"],
        });

        expect(ext.enabled).toBe(true);
        expect(ext.memberCount).toBe(2);
        expect(ext.coordinatorSkill).toContain("team-coordinator");
        expect(ext.sendTask({ toNodeId: "node-b", payload: "analyze" })).toContain("mailbox.send");
        expect(ext.broadcast("sync")).toContain("mailbox.broadcast");
    });

    it("stays disabled for single-node sessions", () => {
        const ext = buildColliderTeamLeaderExtension({
            sessionId: "solo-session",
            nodeIds: ["node-only"],
        });

        expect(ext.enabled).toBe(false);
        expect(ext.memberCount).toBe(0);
        expect(ext.coordinatorSkill).toBe("");
        expect(() => ext.sendTask({ toNodeId: "node-only", payload: "x" })).toThrow(/disabled/i);
    });
});
