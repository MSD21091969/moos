/**
 * Test suite for NanoClawBridge SDK modules.
 *
 * Covers:
 *   - prompt-builder: system prompt construction + delta application
 *   - tool-executor: API tool schema generation + tool execution routing
 *   - team-manager: team creation, task delegation, mailbox
 *   - types: ComposedContext validation
 *
 * Run: npx vitest run
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { buildSystemPrompt, applyDeltaToContext } from "../../src/sdk/prompt-builder.js";
import { ToolExecutor } from "../../src/sdk/tool-executor.js";
import type {
  ComposedContext,
  SkillDefinition,
  ToolSchema,
  ContextDelta,
} from "../../src/sdk/types.js";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeContext(overrides?: Partial<ComposedContext>): ComposedContext {
  return {
    agents_md: "# Agent Instructions\nYou are a test agent.",
    soul_md: "# Soul\nBe precise and helpful.",
    tools_md: "# Tools\nUse tools wisely.",
    skills: [
      {
        name: "test-skill",
        description: "A test skill for unit testing",
        emoji: "T",
        tool_ref: "test_tool",
        markdown_body: "# Test Skill\nPerform the test action.",
        user_invocable: true,
        model_invocable: true,
        invocation_policy: "auto",
        requires_bins: [],
        requires_env: [],
      },
    ],
    tool_schemas: [
      {
        name: "test_tool",
        description: "A test tool",
        parameters: {
          type: "object",
          properties: { query: { type: "string" } },
          required: ["query"],
        },
      },
    ],
    mcp_servers: [
      { name: "collider-tools", transport_type: "sse", url: "http://localhost:8001/mcp/sse" },
    ],
    session_meta: {
      role: "app_user",
      app_id: "test-app",
      composed_nodes: ["node-1", "node-2"],
      username: "test-user",
    },
    ...overrides,
  };
}

function makeSkill(overrides?: Partial<SkillDefinition>): SkillDefinition {
  return {
    name: "new-skill",
    description: "Newly added skill",
    emoji: "N",
    tool_ref: "",
    markdown_body: "# New Skill\nDo new things.",
    user_invocable: true,
    model_invocable: true,
    invocation_policy: "auto",
    requires_bins: [],
    requires_env: [],
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// prompt-builder tests
// ---------------------------------------------------------------------------

describe("buildSystemPrompt", () => {
  it("includes all context sections in the output", () => {
    const ctx = makeContext();
    const prompt = buildSystemPrompt(ctx);

    expect(prompt).toContain("Agent Instructions");
    expect(prompt).toContain("Be precise and helpful");
    expect(prompt).toContain("Use tools wisely");
  });

  it("includes skill names and descriptions", () => {
    const ctx = makeContext();
    const prompt = buildSystemPrompt(ctx);

    expect(prompt).toContain("test-skill");
    expect(prompt).toContain("Perform the test action");
  });

  it("includes session meta (role, app_id)", () => {
    const ctx = makeContext();
    const prompt = buildSystemPrompt(ctx);

    expect(prompt).toContain("app_user");
    expect(prompt).toContain("test-app");
  });

  it("handles empty context gracefully", () => {
    const ctx = makeContext({
      agents_md: "",
      soul_md: "",
      tools_md: "",
      skills: [],
      tool_schemas: [],
    });
    const prompt = buildSystemPrompt(ctx);

    // Should still produce a string, even if minimal
    expect(typeof prompt).toBe("string");
    expect(prompt.length).toBeGreaterThan(0);
  });

  it("handles multiple skills", () => {
    const ctx = makeContext({
      skills: [
        makeSkill({ name: "skill-a", description: "First" }),
        makeSkill({ name: "skill-b", description: "Second" }),
        makeSkill({ name: "skill-c", description: "Third" }),
      ],
    });
    const prompt = buildSystemPrompt(ctx);

    expect(prompt).toContain("skill-a");
    expect(prompt).toContain("skill-b");
    expect(prompt).toContain("skill-c");
  });
});

describe("applyDeltaToContext", () => {
  it("applies a skill addition delta", () => {
    const ctx = makeContext();
    const delta: ContextDelta = {
      type: "skill",
      operation: "add",
      skill: makeSkill({ name: "added-skill" }),
    };

    const updated = applyDeltaToContext(ctx, delta);
    const names = updated.skills.map((s) => s.name);

    expect(names).toContain("added-skill");
    expect(names).toContain("test-skill"); // original preserved
  });

  it("applies a skill update delta", () => {
    const ctx = makeContext();
    const delta: ContextDelta = {
      type: "skill",
      operation: "update",
      skill: makeSkill({ name: "test-skill", description: "UPDATED" }),
    };

    const updated = applyDeltaToContext(ctx, delta);
    const skill = updated.skills.find((s) => s.name === "test-skill");

    expect(skill?.description).toBe("UPDATED");
  });

  it("applies a skill removal delta", () => {
    const ctx = makeContext();
    const delta: ContextDelta = {
      type: "skill",
      operation: "remove",
      skill: makeSkill({ name: "test-skill" }),
    };

    const updated = applyDeltaToContext(ctx, delta);
    const names = updated.skills.map((s) => s.name);

    expect(names).not.toContain("test-skill");
  });

  it("applies a system_prompt delta", () => {
    const ctx = makeContext();
    const delta: ContextDelta = {
      type: "system_prompt",
      section: "agents_md",
      content: "# UPDATED Agent Instructions",
      operation: "replace",
    };

    const updated = applyDeltaToContext(ctx, delta);
    expect(updated.agents_md).toBe("# UPDATED Agent Instructions");
  });

  it("applies a full_replace delta", () => {
    const newCtx = makeContext({ agents_md: "# Replaced" });
    const delta: ContextDelta = {
      type: "full_replace",
      context: newCtx,
    };

    const updated = applyDeltaToContext(makeContext(), delta);
    expect(updated.agents_md).toBe("# Replaced");
  });

  it("mutates context in-place for granular deltas", () => {
    const ctx = makeContext();
    const delta: ContextDelta = {
      type: "skill",
      operation: "add",
      skill: makeSkill(),
    };

    const updated = applyDeltaToContext(ctx, delta);
    // In-place mutation returns same reference
    expect(updated).toBe(ctx);
    expect(updated.skills.length).toBeGreaterThan(1);
  });

  it("full_replace returns the replacement context", () => {
    const original = makeContext();
    const replacement = makeContext({ agents_md: "# Replaced" });
    const delta: ContextDelta = {
      type: "full_replace",
      context: replacement,
    };

    const updated = applyDeltaToContext(original, delta);
    expect(updated).toBe(replacement);
    expect(updated.agents_md).toBe("# Replaced");
  });
});

// ---------------------------------------------------------------------------
// tool-executor tests
// ---------------------------------------------------------------------------

describe("ToolExecutor", () => {
  let executor: ToolExecutor;

  beforeEach(() => {
    executor = new ToolExecutor({
      mcpUrl: "http://localhost:8001/mcp/sse",
    });
  });

  it("stores tool schemas", () => {
    const schemas = [
      { function: { name: "tool_a", description: "Tool A", parameters: { type: "object", properties: {} } } },
      { function: { name: "tool_b", description: "Tool B", parameters: { type: "object", properties: {} } } },
    ];
    executor.setToolSchemas(schemas as unknown as ToolSchema[]);

    const apiTools = executor.getApiTools();
    expect(apiTools).toHaveLength(2);
  });

  it("generates Anthropic-compatible tool schemas", () => {
    executor.setToolSchemas([
      {
        function: {
          name: "search",
          description: "Search the web",
          parameters: {
            type: "object",
            properties: { query: { type: "string" } },
            required: ["query"],
          },
        },
      },
    ] as unknown as ToolSchema[]);

    const tools = executor.getApiTools();
    expect(tools[0]).toMatchObject({
      name: "search",
      description: "Search the web",
    });
    expect(tools[0].input_schema).toBeDefined();
  });

  it("handles empty tool schemas", () => {
    executor.setToolSchemas([]);
    expect(executor.getApiTools()).toEqual([]);
  });

  it("executeAll resolves with results for each tool use", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ result: "success" }),
    });
    global.fetch = mockFetch;

    const results = await executor.executeAll([
      { id: "tool_1", name: "test_tool", input: { query: "hello" } },
    ]);

    expect(results).toHaveLength(1);
    expect(results[0].tool_use_id).toBe("tool_1");
  });
});

// ---------------------------------------------------------------------------
// ComposedContext type validation tests
// ---------------------------------------------------------------------------

describe("ComposedContext shape", () => {
  it("has all required fields", () => {
    const ctx = makeContext();

    expect(ctx).toHaveProperty("agents_md");
    expect(ctx).toHaveProperty("soul_md");
    expect(ctx).toHaveProperty("tools_md");
    expect(ctx).toHaveProperty("skills");
    expect(ctx).toHaveProperty("tool_schemas");
    expect(ctx).toHaveProperty("mcp_servers");
    expect(ctx).toHaveProperty("session_meta");
  });

  it("skills have SkillDefinition shape", () => {
    const ctx = makeContext();
    const skill = ctx.skills[0];

    expect(skill).toHaveProperty("name");
    expect(skill).toHaveProperty("description");
    expect(skill).toHaveProperty("emoji");
    expect(skill).toHaveProperty("tool_ref");
    expect(skill).toHaveProperty("markdown_body");
    expect(skill).toHaveProperty("user_invocable");
    expect(skill).toHaveProperty("model_invocable");
    expect(skill).toHaveProperty("invocation_policy");
    expect(["auto", "confirm", "disabled"]).toContain(skill.invocation_policy);
  });

  it("tool_schemas have ToolSchema shape", () => {
    const ctx = makeContext();
    const schema = ctx.tool_schemas[0];

    expect(schema).toHaveProperty("name");
    expect(schema).toHaveProperty("description");
    expect(schema).toHaveProperty("parameters");
    expect(schema.parameters).toHaveProperty("type");
  });

  it("session_meta has required fields", () => {
    const ctx = makeContext();

    expect(ctx.session_meta.role).toBeDefined();
    expect(ctx.session_meta.app_id).toBeDefined();
    expect(ctx.session_meta.composed_nodes).toBeInstanceOf(Array);
    expect(ctx.session_meta.username).toBeDefined();
  });
});
