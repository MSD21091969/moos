import type { Message } from '@moos/functors';

export interface SessionState {
    sessionId: string;
    history: Message[];
}

export const createSessionState = (sessionId: string): SessionState => ({
    sessionId,
    history: [],
});

export const appendHistory = (state: SessionState, message: Message): SessionState => ({
    ...state,
    history: [...state.history, message],
});
