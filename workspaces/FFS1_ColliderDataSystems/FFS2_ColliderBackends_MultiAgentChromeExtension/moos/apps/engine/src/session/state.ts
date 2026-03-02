export interface SessionState {
    sessionId: string;
    history: string[];
}

export const createSessionState = (sessionId: string): SessionState => ({
    sessionId,
    history: [],
});

export const appendHistory = (state: SessionState, message: string): SessionState => ({
    ...state,
    history: [...state.history, message],
});
