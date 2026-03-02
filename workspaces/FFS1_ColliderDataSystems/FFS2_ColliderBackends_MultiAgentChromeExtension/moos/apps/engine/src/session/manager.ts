import { appendHistory, createSessionState, type SessionState } from './state.js';

export class SessionManager {
    private readonly sessions = new Map<string, SessionState>();

    public create(sessionId: string): SessionState {
        const state = createSessionState(sessionId);
        this.sessions.set(sessionId, state);
        return state;
    }

    public append(sessionId: string, message: string): SessionState {
        const existing = this.sessions.get(sessionId) ?? this.create(sessionId);
        const updated = appendHistory(existing, message);
        this.sessions.set(sessionId, updated);
        return updated;
    }

    public get(sessionId: string): SessionState | undefined {
        return this.sessions.get(sessionId);
    }
}
