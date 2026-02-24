import type { AgentEvent } from "../event-parser.js";
import type { ContextDelta, SdkSessionConfig } from "./types.js";

export interface IAgentSession {
    createSession(config: SdkSessionConfig): string;
    sendMessage(sessionId: string, message: string): AsyncGenerator<AgentEvent>;
    injectContext(sessionId: string, delta: ContextDelta): void;
    terminateSession(sessionId: string): void;
    hasHistory(sessionId: string): boolean;
}
