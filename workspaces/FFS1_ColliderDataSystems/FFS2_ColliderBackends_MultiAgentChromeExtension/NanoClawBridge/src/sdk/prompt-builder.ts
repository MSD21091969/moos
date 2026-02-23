/**
 * SDK Prompt Builder
 *
 * Composes a system prompt from structured JSON context (ComposedContext).
 * Replaces the filesystem-based approach where CLAUDE.md was written to disk.
 * Skills are injected inline as system prompt sections, not as SKILL.md files.
 */

import type { ComposedContext, ContextDelta, SkillDefinition } from "./types.js";

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Build a system prompt string from composed context.
 * Sections are separated by horizontal rules for clarity.
 */
export function buildSystemPrompt(context: ComposedContext): string {
  const sections: string[] = [];

  // Agent identity (from NodeContainer.instructions)
  if (context.agents_md.trim()) {
    sections.push(`# Agent Instructions\n\n${context.agents_md.trim()}`);
  }

  // Rules and guardrails (from NodeContainer.rules)
  if (context.soul_md.trim()) {
    sections.push(`# Rules & Guardrails\n\n${context.soul_md.trim()}`);
  }

  // Knowledge and reference docs (from NodeContainer.knowledge)
  if (context.tools_md.trim()) {
    sections.push(`# Knowledge\n\n${context.tools_md.trim()}`);
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

  const entries = invocable.map((skill) => {
    const header = `## ${skill.emoji ? `${skill.emoji} ` : ""}${skill.name}`;
    const desc = skill.description ? `\n\n${skill.description}` : "";
    const body = skill.markdown_body?.trim()
      ? `\n\n${skill.markdown_body.trim()}`
      : "";
    const toolRef = skill.tool_ref
      ? `\n\n> Invokes tool: \`${skill.tool_ref}\``
      : "";
    return `${header}${desc}${body}${toolRef}`;
  });

  return `# Available Skills\n\n${entries.join("\n\n---\n\n")}`;
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
