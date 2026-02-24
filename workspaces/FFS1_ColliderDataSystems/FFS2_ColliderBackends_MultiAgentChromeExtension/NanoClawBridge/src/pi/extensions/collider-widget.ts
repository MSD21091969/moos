import type { ColliderContextExtensionState } from "./collider-context.js";

export interface ColliderWidgetExtensionState {
    content: string;
    position: "footer";
    skillCount: number;
    toolCount: number;
}

export function buildColliderWidgetExtension(
    contextState: ColliderContextExtensionState,
): ColliderWidgetExtensionState {
    const skillCount = contextState.skills.modelInvocable;
    const toolCount = contextState.context.tool_schemas.length;
    const nodeScope = contextState.session.nodeIds.join("/") || "none";
    const shortSessionId = contextState.session.sessionId.slice(0, 8);

    return {
        content: `[${shortSessionId}] nodes:${nodeScope} skills:${skillCount} tools:${toolCount}`,
        position: "footer",
        skillCount,
        toolCount,
    };
}
