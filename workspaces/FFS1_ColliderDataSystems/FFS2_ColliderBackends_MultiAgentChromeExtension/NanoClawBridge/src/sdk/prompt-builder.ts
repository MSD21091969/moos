/**
 * SDK Prompt Builder
 *
 * Composes a system prompt from structured JSON context (ComposedContext).
 * Replaces the filesystem-based approach where CLAUDE.md was written to disk.
 * Skills are injected inline as system prompt sections, not as SKILL.md files.
 */

import type { ComposedContext, ContextDelta, SkillDefinition } from "./types.js";

const SKILL_TOKEN_BUDGET = 2000;
const MAX_FULL_SKILLS = 3;
const MIN_SUMMARY_TOKENS = 24;

export interface RankedSkillSelection {
  fullSkills: SkillDefinition[];
  summarizedSkills: SkillDefinition[];
  usedTokens: number;
  budget: number;
  maxFullSkills: number;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Build a system prompt string from composed context.
 * Sections are separated by horizontal rules for clarity.
 */
export function buildSystemPrompt(context: ComposedContext): string {
  const sections: string[] = [];

  const workspaceContext = formatWorkspaceContext(context);
  if (workspaceContext) {
    sections.push(workspaceContext);
  }

  // Skills — injected as system prompt sections, not SKILL.md files
  const skillSections = formatSkills(context.skills);
  if (skillSections) {
    sections.push(skillSections);
  }

  // Session context metadata
  sections.push(formatSessionMeta(context.session_meta));

  return sections.join("\n\n---\n\n");
}

/**
 * Apply a context delta to an existing system prompt.
 * Returns the updated prompt string.
 */
export function applyContextDelta(
  currentPrompt: string,
  context: ComposedContext,
  delta: ContextDelta,
): string {
  if (delta.type === "full_replace") {
    return buildSystemPrompt(delta.context);
  }

  // For granular deltas, rebuild from the mutated context.
  // The caller is responsible for updating context before calling this.
  return buildSystemPrompt(context);
}

/**
 * Mutate a ComposedContext in-place based on a delta.
 * Returns the same reference, modified.
 */
export function applyDeltaToContext(
  context: ComposedContext,
  delta: ContextDelta,
): ComposedContext {
  switch (delta.type) {
    case "full_replace":
      return delta.context;

    case "system_prompt": {
      const key = delta.section;
      if (delta.operation === "replace") {
        context[key] = delta.content;
      } else if (delta.operation === "append") {
        context[key] += `\n\n${delta.content}`;
      }
      return context;
    }

    case "skill": {
      const idx = context.skills.findIndex((s) => s.name === delta.skill.name);
      if (delta.operation === "remove") {
        if (idx >= 0) context.skills.splice(idx, 1);
      } else if (delta.operation === "add" || delta.operation === "update") {
        if (idx >= 0) {
          context.skills[idx] = delta.skill;
        } else {
          context.skills.push(delta.skill);
        }
      }
      return context;
    }

    case "tool_schema": {
      const name = delta.tool_schema.function.name;
      const idx = context.tool_schemas.findIndex(
        (t) => t.function.name === name,
      );
      if (delta.operation === "remove") {
        if (idx >= 0) context.tool_schemas.splice(idx, 1);
      } else if (delta.operation === "add" || delta.operation === "update") {
        if (idx >= 0) {
          context.tool_schemas[idx] = delta.tool_schema;
        } else {
          context.tool_schemas.push(delta.tool_schema);
        }
      }
      return context;
    }
  }
}

// ---------------------------------------------------------------------------
// Internal formatters
// ---------------------------------------------------------------------------

function formatSkills(skills: SkillDefinition[]): string {
  const invocable = skills.filter((s) => s.model_invocable);
  if (invocable.length === 0) return "";

  const selection = selectRankedSkills(invocable);
  const fullEntries = selection.fullSkills.map((skill) => formatFullSkill(skill));
  const summarizedSkills = selection.summarizedSkills;
  let usedTokens = selection.usedTokens;
  let summaryTokens = 0;

  const sections: string[] = [];
  if (fullEntries.length > 0) {
    sections.push(fullEntries.join("\n\n---\n\n"));
  }

  const remainingBudget = Math.max(0, selection.budget - usedTokens);
  const summarizedLines: string[] = [];

  for (const skill of summarizedSkills) {
    const tags = [skill.kind ?? "procedural", skill.scope ?? "local"];
    const versionTag = skill.version ? ` v${skill.version}` : "";
    const description = skill.description ? ` — ${skill.description}` : "";
    const line = `- **${skill.name}${versionTag}** [${tags.join(" | ")}]${description}`;
    const estimatedLineTokens = estimateTokens(`${line}\n`);

    if (summaryTokens + estimatedLineTokens > remainingBudget) {
      break;
    }

    summarizedLines.push(line);
    summaryTokens += estimatedLineTokens;
  }

  if (summaryTokens > 0 || summarizedSkills.length > 0) {
    usedTokens += summaryTokens;
  }

  const omittedSummaries = summarizedSkills.length - summarizedLines.length;

  if (summarizedSkills.length > 0) {
    if (summarizedLines.length > 0) {
      sections.push(
        `## Additional Skills (summarized)\n\n${summarizedLines.join("\n")}`,
      );
    }

    if (omittedSummaries > 0 && remainingBudget < MIN_SUMMARY_TOKENS) {
      sections.push(
        `## Additional Skills (omitted)\n\n- ${omittedSummaries} summarized skills omitted to enforce skill token budget.`,
      );
    } else if (omittedSummaries > 0) {
      sections.push(
        `## Additional Skills (omitted)\n\n- ${omittedSummaries} summarized skills omitted after token limit was reached.`,
      );
    }
  }

  sections.push(
    [
      "## Skill Selection",
      "",
      `- **Model-invocable skills**: ${invocable.length}`,
      `- **Full skills injected**: ${fullEntries.length}`,
      `- **Summarized skills**: ${summarizedLines.length}`,
      `- **Omitted summarized skills**: ${Math.max(omittedSummaries, 0)}`,
      `- **Estimated skill tokens used**: ${usedTokens}/${SKILL_TOKEN_BUDGET}`,
    ].join("\n"),
  );

  return `# Available Skills\n\n${sections.join("\n\n")}`;
}

export function selectRankedSkills(
  skills: SkillDefinition[],
  opts?: { tokenBudget?: number; maxFullSkills?: number },
): RankedSkillSelection {
  const budget = opts?.tokenBudget ?? SKILL_TOKEN_BUDGET;
  const maxFullSkills = opts?.maxFullSkills ?? MAX_FULL_SKILLS;

  const ranked = [...skills]
    .map((skill) => ({ skill, score: rankSkill(skill) }))
    .sort((left, right) => {
      if (left.score !== right.score) return right.score - left.score;
      return left.skill.name.localeCompare(right.skill.name);
    });

  const fullSkills: SkillDefinition[] = [];
  const summarizedSkills: SkillDefinition[] = [];
  let usedTokens = 0;

  for (const item of ranked) {
    const entry = formatFullSkill(item.skill);
    const estimatedTokens = estimateTokens(entry);
    const canIncludeFull =
      fullSkills.length < maxFullSkills &&
      usedTokens + estimatedTokens <= budget;

    if (canIncludeFull) {
      fullSkills.push(item.skill);
      usedTokens += estimatedTokens;
    } else {
      summarizedSkills.push(item.skill);
    }
  }

  return {
    fullSkills,
    summarizedSkills,
    usedTokens,
    budget,
    maxFullSkills,
  };
}

function formatFullSkill(skill: SkillDefinition): string {
  const tags = [skill.kind ?? "procedural", skill.scope ?? "local"];
  const versionTag = skill.version ? ` v${skill.version}` : "";
  const namespaceTag = skill.namespace ? `${skill.namespace}::` : "";
  const header = `## ${skill.emoji ? `${skill.emoji} ` : ""}${namespaceTag}${skill.name}${versionTag} [${tags.join(" | ")}]`;
  const desc = skill.description ? `\n\n${skill.description}` : "";
  const body = skill.markdown_body?.trim() ? `\n\n${skill.markdown_body.trim()}` : "";

  const details: string[] = [];
  if (skill.tool_ref) details.push(`> Invokes tool: \`${skill.tool_ref}\``);
  if (skill.source_node_path) {
    details.push(`> Source: \`${skill.source_node_path}\``);
  }
  if (skill.outputs?.length) {
    details.push(`> Outputs: ${skill.outputs.join(", ")}`);
  }

  const detailsBlock = details.length > 0 ? `\n\n${details.join("\n")}` : "";
  return `${header}${desc}${body}${detailsBlock}`;
}

function rankSkill(skill: SkillDefinition): number {
  const scopeWeight: Record<string, number> = {
    local: 40,
    composed: 30,
    inherited: 20,
    global: 10,
  };

  let score = scopeWeight[skill.scope ?? "local"] ?? 0;

  if (skill.tool_ref) score += 15;
  if (skill.exposes_tools?.length) score += 10;
  if (skill.outputs?.length) score += 5;
  if (skill.depends_on?.length) score += 3;
  if (skill.markdown_body?.trim()) score += 5;

  const versionBoost = parseVersionBoost(skill.version);
  score += versionBoost;

  return score;
}

function parseVersionBoost(version?: string): number {
  if (!version) return 0;
  const first = version.split(".")[0] ?? "0";
  const major = Number.parseInt(first.replace(/\D/g, ""), 10);
  return Number.isFinite(major) ? Math.min(major, 10) : 0;
}

function estimateTokens(text: string): number {
  // Simple approximation: 1 token ~= 4 chars for English-like markdown.
  return Math.ceil(text.length / 4);
}

export function formatWorkspaceContext(
  context: Pick<ComposedContext, "agents_md" | "soul_md" | "tools_md">,
): string {
  const blocks: string[] = [];

  if (context.agents_md.trim()) {
    blocks.push(`## Instructions\n\n${context.agents_md.trim()}`);
  }

  if (context.soul_md.trim()) {
    blocks.push(`## Rules & Guardrails\n\n${context.soul_md.trim()}`);
  }

  if (context.tools_md.trim()) {
    blocks.push(`## Knowledge\n\n${context.tools_md.trim()}`);
  }

  if (blocks.length === 0) {
    return "";
  }

  return `# Workspace Context\n\n${blocks.join("\n\n")}`;
}

function formatSessionMeta(meta: ComposedContext["session_meta"]): string {
  const lines = [
    `# Session Context`,
    ``,
    `- **Role**: ${meta.role}`,
    `- **Application**: ${meta.app_id}`,
    `- **Composed nodes**: ${meta.composed_nodes.join(", ") || "none"}`,
  ];
  if (meta.username) {
    lines.push(`- **User**: ${meta.username}`);
  }
  return lines.join("\n");
}
