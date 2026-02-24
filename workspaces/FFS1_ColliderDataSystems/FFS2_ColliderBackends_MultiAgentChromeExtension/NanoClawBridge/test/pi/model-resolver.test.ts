import { afterEach, describe, expect, it } from "vitest";
import { resolvePiModel } from "../../src/pi/model-resolver.js";

const originalEnv = {
    COLLIDER_AGENT_PROVIDER: process.env.COLLIDER_AGENT_PROVIDER,
    COLLIDER_AGENT_MODEL: process.env.COLLIDER_AGENT_MODEL,
};

describe("resolvePiModel", () => {
    afterEach(() => {
        process.env.COLLIDER_AGENT_PROVIDER = originalEnv.COLLIDER_AGENT_PROVIDER;
        process.env.COLLIDER_AGENT_MODEL = originalEnv.COLLIDER_AGENT_MODEL;
    });

    it("resolves gemini defaults", () => {
        process.env.COLLIDER_AGENT_PROVIDER = "gemini";
        delete process.env.COLLIDER_AGENT_MODEL;

        const result = resolvePiModel();
        expect(result.provider).toBe("gemini");
        expect(result.model).toBe("gemini-2.5-flash");
    });

    it("resolves anthropic with override", () => {
        process.env.COLLIDER_AGENT_PROVIDER = "anthropic";
        const result = resolvePiModel("claude-custom");

        expect(result.provider).toBe("anthropic");
        expect(result.model).toBe("claude-custom");
    });

    it("throws for unsupported provider", () => {
        process.env.COLLIDER_AGENT_PROVIDER = "unknown-provider";
        expect(() => resolvePiModel()).toThrow(/Unsupported COLLIDER_AGENT_PROVIDER/i);
    });
});
