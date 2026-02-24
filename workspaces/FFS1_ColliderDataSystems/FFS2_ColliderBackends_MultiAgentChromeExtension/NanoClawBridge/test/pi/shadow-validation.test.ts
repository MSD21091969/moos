import { describe, expect, it } from "vitest";
import {
    evaluateShadowTraffic,
    type ShadowTrafficSample,
} from "../../src/pi/shadow-validation.js";

function sample(overrides?: Partial<ShadowTrafficSample>): ShadowTrafficSample {
    return {
        sessionId: "sample-1",
        anthropicEvents: [
            { kind: "text_delta", text: "hello" },
            { kind: "message_end" },
        ],
        piEvents: [
            { kind: "text_delta", text: "hello" },
            { kind: "message_end" },
        ],
        ...overrides,
    };
}

describe("shadow-validation", () => {
    it("passes when parity and KPI deltas are within thresholds", () => {
        const result = evaluateShadowTraffic([sample()]);

        expect(result.pass).toBe(true);
        expect(result.metrics.eventParityPercent).toBe(100);
        expect(result.metrics.taskCompletionDeltaPercent).toBe(0);
        expect(result.metrics.toolErrorRateDeltaPercent).toBe(0);
        expect(result.metrics.tokenUsageDeltaPercent).toBe(0);
        expect(result.metrics.criticalPolicyBypasses).toBe(0);
    });

    it("fails when event parity and policy thresholds are violated", () => {
        const result = evaluateShadowTraffic([
            sample({
                piEvents: [
                    { kind: "error", message: "failed" },
                    { kind: "message_end" },
                ],
                criticalPolicyBypasses: 1,
            }),
        ]);

        expect(result.pass).toBe(false);
        expect(result.failures.some((failure) => failure.includes("Event parity"))).toBe(true);
        expect(result.failures.some((failure) => failure.includes("Critical policy bypasses"))).toBe(true);
    });

    it("returns explicit failure for empty sample set", () => {
        const result = evaluateShadowTraffic([]);

        expect(result.pass).toBe(false);
        expect(result.failures).toContain("No shadow samples available");
    });
});
