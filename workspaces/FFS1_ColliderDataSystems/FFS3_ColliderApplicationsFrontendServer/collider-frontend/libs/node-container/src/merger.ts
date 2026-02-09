import type { NodeContainer } from "./types";

export class ContainerMerger {
  /**
   * Deep-merge two NodeContainers. The `override` takes precedence.
   * - Objects: deep-merged (override keys win)
   * - Arrays: concatenated, then deduplicated by `id` field if present
   */
  static merge(base: NodeContainer, override: NodeContainer): NodeContainer {
    return {
      manifest: { ...base.manifest, ...override.manifest },
      instructions: [...base.instructions, ...override.instructions],
      rules: [...base.rules, ...override.rules],
      skills: [...base.skills, ...override.skills],
      tools: ContainerMerger.mergeById(base.tools, override.tools),
      knowledge: [...base.knowledge, ...override.knowledge],
      workflows: ContainerMerger.mergeById(base.workflows, override.workflows),
      configs: ContainerMerger.deepMerge(base.configs, override.configs),
    };
  }

  /**
   * Merge arrays of objects by their `id` field. Override entries replace
   * base entries with the same id. Entries without `id` are appended.
   */
  private static mergeById(
    base: Record<string, unknown>[],
    override: Record<string, unknown>[]
  ): Record<string, unknown>[] {
    const merged = new Map<string, Record<string, unknown>>();
    let anonymousIdx = 0;

    for (const item of base) {
      const id = (item.id as string) ?? `__anon_${anonymousIdx++}`;
      merged.set(id, item);
    }

    for (const item of override) {
      const id = (item.id as string) ?? `__anon_${anonymousIdx++}`;
      const existing = merged.get(id);
      if (existing) {
        merged.set(id, { ...existing, ...item });
      } else {
        merged.set(id, item);
      }
    }

    return Array.from(merged.values());
  }

  /**
   * Deep-merge two plain objects recursively.
   */
  private static deepMerge(
    base: Record<string, unknown>,
    override: Record<string, unknown>
  ): Record<string, unknown> {
    const result: Record<string, unknown> = { ...base };
    for (const [key, value] of Object.entries(override)) {
      if (
        value !== null &&
        typeof value === "object" &&
        !Array.isArray(value) &&
        typeof result[key] === "object" &&
        result[key] !== null &&
        !Array.isArray(result[key])
      ) {
        result[key] = ContainerMerger.deepMerge(
          result[key] as Record<string, unknown>,
          value as Record<string, unknown>
        );
      } else {
        result[key] = value;
      }
    }
    return result;
  }
}
