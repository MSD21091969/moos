import type { ToolExecutionResult } from '@moos/core';
import type { ToolUse } from '@moos/functors';

export interface ToolRegistryEntry {
    name: string;
    description: string;
    execute: (input: unknown) => Promise<unknown>;
}

export interface RuntimeToolDefinition {
    name: string;
    description?: string;
    mode?: 'echo' | 'sum_numbers';
}

export class ToolRegistry {
    private readonly tools = new Map<string, ToolRegistryEntry>();

    public register(entry: ToolRegistryEntry): void {
        this.tools.set(entry.name, entry);
    }

    public registerRuntime(definition: RuntimeToolDefinition): void {
        const mode = definition.mode ?? 'echo';

        if (mode === 'sum_numbers') {
            this.register({
                name: definition.name,
                description: definition.description ?? 'Runtime-registered sum tool.',
                execute: async (input) => {
                    const values =
                        typeof input === 'object' && input !== null && 'values' in input
                            ? (input as { values?: unknown }).values
                            : undefined;
                    const numbers = Array.isArray(values)
                        ? values.filter((value): value is number => typeof value === 'number')
                        : [];
                    const sum = numbers.reduce((acc, value) => acc + value, 0);

                    return { sum };
                },
            });
            return;
        }

        this.register({
            name: definition.name,
            description: definition.description ?? 'Runtime-registered echo tool.',
            execute: async (input) => ({ echoed: input }),
        });
    }

    public list(): Array<Pick<ToolRegistryEntry, 'name' | 'description'>> {
        return [...this.tools.values()].map((tool) => ({
            name: tool.name,
            description: tool.description,
        }));
    }

    public has(name: string): boolean {
        return this.tools.has(name);
    }

    public async execute(toolUse: ToolUse): Promise<ToolExecutionResult> {
        const tool = this.tools.get(toolUse.name);
        if (!tool) {
            return {
                output: null,
                error: 'unknown_tool',
            };
        }

        const output = await tool.execute(toolUse.input);
        return { output };
    }
}

export const createDefaultRegistry = (): ToolRegistry => {
    const registry = new ToolRegistry();

    registry.register({
        name: 'echo_tool',
        description: 'Returns the input payload as-is.',
        execute: async (input) => ({
            echoed: input,
        }),
    });

    registry.register({
        name: 'sum_numbers',
        description: 'Sums numeric values from an input list.',
        execute: async (input) => {
            const values =
                typeof input === 'object' && input !== null && 'values' in input
                    ? (input as { values?: unknown }).values
                    : undefined;
            const numbers = Array.isArray(values)
                ? values.filter((value): value is number => typeof value === 'number')
                : [];
            const sum = numbers.reduce((acc, value) => acc + value, 0);

            return { sum };
        },
    });

    return registry;
};
