export interface ColliderTeamMemberExtensionState {
    enabled: boolean;
    nodeId?: string;
    reportResult: (payload: string) => string;
}

export function buildColliderTeamMemberExtension(params: {
    sessionId: string;
    nodeIds: string[];
}): ColliderTeamMemberExtensionState {
    const nodeIds = [...params.nodeIds];
    const enabled = nodeIds.length === 1;

    return {
        enabled,
        nodeId: enabled ? nodeIds[0] : undefined,
        reportResult: (payload) => {
            if (!enabled) {
                throw new Error("Team member extension is disabled for multi-node sessions");
            }
            return `mailbox.report(session=${params.sessionId}, node=${nodeIds[0]}): ${payload}`;
        },
    };
}
