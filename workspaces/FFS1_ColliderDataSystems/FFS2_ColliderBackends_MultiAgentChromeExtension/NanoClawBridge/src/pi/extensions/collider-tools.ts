import crypto from "node:crypto";
import { ToolExecutor } from "../../sdk/tool-executor.js";
import type { ComposedContext, ToolSchema } from "../../sdk/types.js";

export interface ColliderToolsExtensionState {
    toolNames: string[];
    executeTool: (
        toolName: string,
        input: Record<string, unknown>,
    ) => Promise<{ name: string; result: string; isError: boolean }>;
}

export function buildColliderToolsExtension(params: {
    context: ComposedContext;
    authToken?: string;
}): ColliderToolsExtensionState {
    const dataServerUrl = process.env.COLLIDER_DATA_SERVER_URL ?? "http://localhost:8000";
    const executor = new ToolExecutor({
        mcpUrl: dataServerUrl,
        authToken: params.authToken,
    });

    executor.setToolSchemas(params.context.tool_schemas);
    const toolNames = params.context.tool_schemas.map((schema) => schema.function.name);

    return {
        toolNames,
        executeTool: async (toolName, input) => {
            ensureKnownTool(toolName, params.context.tool_schemas);
            const result = await executor.execute({
                id: crypto.randomUUID(),
                name: toolName,
                input,
            });
            return {
                name: toolName,
                result: result.content,
                isError: !!result.is_error,
            };
        },
    };
}

function ensureKnownTool(toolName: string, schemas: ToolSchema[]): void {
    const known = schemas.some((schema) => schema.function.name === toolName);
    if (!known) {
        throw new Error(`Unknown PI tool: ${toolName}`);
    }
}
