export interface NodeContainer {
  manifest: Record<string, unknown>;
  instructions: string[];
  rules: string[];
  skills: string[];
  tools: Record<string, unknown>[];
  knowledge: string[];
  workflows: Record<string, unknown>[];
  configs: Record<string, unknown>;
}

export function emptyContainer(): NodeContainer {
  return {
    manifest: {},
    instructions: [],
    rules: [],
    skills: [],
    tools: [],
    knowledge: [],
    workflows: [],
    configs: {},
  };
}
