import { describe, expect, it } from "vitest";
import {
    buildSystemPrompt,
    formatWorkspaceContext,
    selectRankedSkills,
} from "../../src/sdk/prompt-builder.js";
import type { ComposedContext } from "../../src/sdk/types.js";

describe("Prompt Builder Parity", () => {
    it("SDK system prompt contains same sections as legacy workspace files", () => {
        const context: ComposedContext = {
            session_id: "test-session",
            agents_md: "You are a test agent.",
            soul_md: "Be helpful.",
            tools_md: "Here is some tool reference data.",
            skills: [
                {
                    name: "calculate",
                    description: "Perform math",
                    emoji: "🧮",
                    markdown_body: "Use standard operators.",
                    tool_ref: "math_tool",
                    user_invocable: true,
                    model_invocable: true,
                    invocation_policy: "auto",
                },
            ],
            tool_schemas: [],
            mcp_servers: [],
            session_meta: {
                role: "tester",
                app_id: "test-app",
                composed_nodes: ["node1"],
                username: "Sam",
            },
        };

        const prompt = buildSystemPrompt(context);

        // Assert overall structure
        expect(prompt).toContain("# Workspace Context");
        expect(prompt).toContain("## Instructions\n\nYou are a test agent.");
        expect(prompt).toContain("## Rules & Guardrails\n\nBe helpful.");
        expect(prompt).toContain("## Knowledge\n\nHere is some tool reference data.");

        // Assert skill injection
        expect(prompt).toContain("# Available Skills");
        expect(prompt).toContain("## 🧮 calculate");
        expect(prompt).toContain("Perform math");
        expect(prompt).toContain("Use standard operators.");
        expect(prompt).toContain("> Invokes tool: `math_tool`");

        // Assert session meta
        expect(prompt).toContain("# Session Context");
        expect(prompt).toContain("- **Role**: tester");
        expect(prompt).toContain("- **Application**: test-app");
        expect(prompt).toContain("- **Composed nodes**: node1");
        expect(prompt).toContain("- **User**: Sam");
    });

    it("enforces top-N full skill selection within token budget", () => {
        const makeSkill = (index: number, markdown = "") => ({
            name: `skill-${index}`,
            description: `Skill ${index}`,
            markdown_body: markdown || `Body ${index}`,
            user_invocable: true,
            model_invocable: true,
            invocation_policy: "auto" as const,
            tool_ref: `tool-${index}`,
            scope: "local" as const,
        });

        const selection = selectRankedSkills(
            [
                makeSkill(1, "x".repeat(800)),
                makeSkill(2, "x".repeat(800)),
                makeSkill(3, "x".repeat(800)),
                makeSkill(4, "x".repeat(800)),
            ],
            { tokenBudget: 900, maxFullSkills: 3 },
        );

        expect(selection.fullSkills.length).toBeLessThanOrEqual(3);
        expect(selection.usedTokens).toBeLessThanOrEqual(900);
        expect(selection.summarizedSkills.length).toBeGreaterThan(0);
    });

    it("omits summarized overflow when budget is reached", () => {
        const makeLongSkill = (index: number) => ({
            name: `long-skill-${index}`,
            description: "Long skill for budget pressure",
            markdown_body: `Body ${index} ${"x".repeat(6000)}`,
            user_invocable: true,
            model_invocable: true,
            invocation_policy: "auto" as const,
            scope: "local" as const,
            tool_ref: `tool-${index}`,
        });

        const skills = Array.from({ length: 60 }, (_, index) => makeLongSkill(index + 1));

        const prompt = buildSystemPrompt({
            session_id: "test-session",
            agents_md: "Agent",
            soul_md: "Rules",
            tools_md: "Knowledge",
            skills,
            tool_schemas: [],
            mcp_servers: [],
            session_meta: {
                role: "tester",
                app_id: "test-app",
                composed_nodes: ["node1"],
                username: "Sam",
            },
        });

        expect(prompt).toContain("## Additional Skills (omitted)");
        expect(prompt).toContain("Omitted summarized skills");
    });

    it("ignores skills that are not model_invocable", () => {
        const context: ComposedContext = {
            session_id: "test-session",
            agents_md: "",
            soul_md: "",
            tools_md: "",
            skills: [
                {
                    name: "hidden_skill",
                    description: "Not for models",
                    emoji: "",
                    markdown_body: "Secret",
                    tool_ref: "",
                    user_invocable: true,
                    model_invocable: false,
                    invocation_policy: "auto",
                }
            ],
            tool_schemas: [],
            mcp_servers: [],
            session_meta: {
                role: "tester",
                app_id: "test-app",
                composed_nodes: [],
                username: "Sam",
            },
        };

        const prompt = buildSystemPrompt(context);
        expect(prompt).not.toContain("hidden_skill");
        expect(prompt).not.toContain("Available Skills");
    });

    it("returns empty workspace context block when source sections are empty", () => {
        const workspaceSection = formatWorkspaceContext({
            agents_md: "",
            soul_md: "",
            tools_md: "",
        });

        expect(workspaceSection).toBe("");
    });
});
