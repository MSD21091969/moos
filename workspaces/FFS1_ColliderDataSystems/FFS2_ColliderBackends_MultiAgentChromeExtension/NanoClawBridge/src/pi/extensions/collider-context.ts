import {
    applyDeltaToContext,
    buildSystemPrompt,
    formatWorkspaceContext,
    selectRankedSkills,
} from "../../sdk/prompt-builder.js";
import type { ComposedContext, ContextDelta, SkillDefinition } from "../../sdk/types.js";

export interface SessionIdentityMetadata {
    sessionId: string;
    role: string;
    appId: string;
    nodeIds: string[];
    username?: string;
}

export interface ColliderContextExtensionState {
    session: SessionIdentityMetadata;
    workspace: {
        instructions: string;
        rules: string;
        knowledge: string;
    };
    skills: {
        modelInvocable: number;
        full: SkillDefinition[];
        summarized: SkillDefinition[];
        usedTokens: number;
        budget: number;
        maxFullSkills: number;
    };
    prompt: {
        workspace: string;
        system: string;
    };
    context: ComposedContext;
}

export function buildColliderContextExtension(params: {
    sessionId: string;
    context: ComposedContext;
}): ColliderContextExtensionState {
    const context = cloneContext(params.context);
    const modelInvocable = context.skills.filter((skill) => skill.model_invocable);
    const selection = selectRankedSkills(modelInvocable);
    const workspacePrompt = formatWorkspaceContext(context);
    const systemPrompt = buildSystemPrompt(context);

    return {
        session: {
            sessionId: params.sessionId,
            role: context.session_meta.role,
            appId: context.session_meta.app_id,
            nodeIds: [...context.session_meta.composed_nodes],
            username: context.session_meta.username,
        },
        workspace: {
            instructions: context.agents_md,
            rules: context.soul_md,
            knowledge: context.tools_md,
        },
        skills: {
            modelInvocable: modelInvocable.length,
            full: selection.fullSkills,
            summarized: selection.summarizedSkills,
            usedTokens: selection.usedTokens,
            budget: selection.budget,
            maxFullSkills: selection.maxFullSkills,
        },
        prompt: {
            workspace: workspacePrompt,
            system: systemPrompt,
        },
        context,
    };
}

export function applyColliderContextDelta(
    state: ColliderContextExtensionState,
    delta: ContextDelta,
): ColliderContextExtensionState {
    const nextContext = applyDeltaToContext(cloneContext(state.context), delta);
    return buildColliderContextExtension({
        sessionId: state.session.sessionId,
        context: nextContext,
    });
}

function cloneContext(context: ComposedContext): ComposedContext {
    return {
        agents_md: context.agents_md,
        soul_md: context.soul_md,
        tools_md: context.tools_md,
        skills: context.skills.map((skill) => ({ ...skill })),
        tool_schemas: context.tool_schemas.map((schema) => ({
            ...schema,
            function: {
                ...schema.function,
                parameters: schema.function.parameters,
            },
        })),
        mcp_servers: context.mcp_servers.map((server) => ({
            ...server,
            args: server.args ? [...server.args] : undefined,
        })),
        session_meta: {
            role: context.session_meta.role,
            app_id: context.session_meta.app_id,
            composed_nodes: [...context.session_meta.composed_nodes],
            username: context.session_meta.username,
        },
    };
}
