import { SessionManager } from './manager.js';

describe('session-manager', () => {
    it('creates and appends session history', () => {
        const manager = new SessionManager();

        const created = manager.create('s1');
        expect(created.history).toEqual([]);

        const updated = manager.append('s1', 'hello');
        expect(updated.history).toEqual(['hello']);

        const fetched = manager.get('s1');
        expect(fetched?.history).toEqual(['hello']);
    });
});
