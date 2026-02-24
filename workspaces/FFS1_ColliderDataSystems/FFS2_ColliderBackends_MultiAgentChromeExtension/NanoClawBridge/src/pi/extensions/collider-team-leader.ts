export interface TeamTaskDispatch {
    toNodeId: string;
    payload: string;
}

export interface ColliderTeamLeaderExtensionState {
    enabled: boolean;
    nodeIds: string[];
    memberCount: number;
    coordinatorSkill: string;
    sendTask: (dispatch: TeamTaskDispatch) => string;
    broadcast: (payload: string) => string;
}

export function buildColliderTeamLeaderExtension(params: {
    sessionId: string;
    nodeIds: string[];
}): ColliderTeamLeaderExtensionState {
    const nodeIds = [...params.nodeIds];
    const enabled = nodeIds.length > 1;

    return {
        enabled,
        nodeIds,
        memberCount: Math.max(nodeIds.length - 1, 0),
        coordinatorSkill: enabled
            ? buildCoordinatorSkill(params.sessionId, nodeIds)
            : "",
        sendTask: ({ toNodeId, payload }) => {
            if (!enabled) {
                throw new Error("Team leader extension is disabled for single-node sessions");
            }
            if (!nodeIds.includes(toNodeId)) {
                throw new Error(`Unknown team node: ${toNodeId}`);
            }
            return `mailbox.send(to=${toNodeId}): ${payload}`;
        },
        broadcast: (payload) => {
            if (!enabled) {
                throw new Error("Team leader extension is disabled for single-node sessions");
            }
            return `mailbox.broadcast(nodes=${nodeIds.join(",")}): ${payload}`;
        },
    };
}

function buildCoordinatorSkill(sessionId: string, nodeIds: string[]): string {
    return [
        "team-coordinator",
        `session=${sessionId}`,
        `nodes=${nodeIds.join(",")}`,
        "rules=delegate to the most relevant node, collect responses, summarize outcome",
    ].join(" | ");
}
