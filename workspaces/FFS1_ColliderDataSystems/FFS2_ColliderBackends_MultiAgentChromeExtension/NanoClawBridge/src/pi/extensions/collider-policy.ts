export interface PolicyAuditEntry {
    type: "tool";
    name: string;
    at: number;
    isError: boolean;
}

export interface ColliderPolicyExtensionState {
    beforeTool: (toolName: string, input: Record<string, unknown>) => Record<string, unknown>;
    beforeBash: (command: string) => string;
    afterTool: (toolName: string, result: { isError: boolean }) => void;
    getAuditTrail: () => PolicyAuditEntry[];
}

export function buildColliderPolicyExtension(params: {
    allowedTools: string[];
}): ColliderPolicyExtensionState {
    const auditTrail: PolicyAuditEntry[] = [];
    const allowed = new Set(params.allowedTools);
    const bashDenylist = [/rm\s+-rf/i, /drop\s+table/i, /curl\s+.*api[_-]?keys?/i];

    return {
        beforeTool: (toolName, input) => {
            if (!allowed.has(toolName)) {
                throw new Error(`Policy violation: tool not allowed: ${toolName}`);
            }
            return redactSecretsObject(input);
        },
        beforeBash: (command) => {
            for (const pattern of bashDenylist) {
                if (pattern.test(command)) {
                    throw new Error("Policy violation: blocked bash command");
                }
            }
            return command;
        },
        afterTool: (toolName, result) => {
            auditTrail.push({
                type: "tool",
                name: toolName,
                at: Date.now(),
                isError: result.isError,
            });
        },
        getAuditTrail: () => [...auditTrail],
    };
}

function redactSecretsObject(value: Record<string, unknown>): Record<string, unknown> {
    const redacted = redactSecrets(value);
    if (!redacted || typeof redacted !== "object" || Array.isArray(redacted)) {
        return {};
    }
    return redacted as Record<string, unknown>;
}

function redactSecrets(value: unknown): unknown {
    if (typeof value === "string") {
        return value
            .replace(/sk-[a-zA-Z0-9_-]{16,}/g, "[REDACTED]")
            .replace(/(api[_-]?key\s*[:=]\s*)([^\s,;]+)/gi, "$1[REDACTED]");
    }

    if (Array.isArray(value)) {
        return value.map((item) => redactSecrets(item));
    }

    if (value && typeof value === "object") {
        const output: Record<string, unknown> = {};
        for (const [key, nested] of Object.entries(value as Record<string, unknown>)) {
            output[key] = redactSecrets(nested);
        }
        return output;
    }

    return value;
}
