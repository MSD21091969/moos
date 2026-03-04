import type { AddressInfo } from 'node:net';
import { createServer } from 'node:http';
import { fetchBootstrapContext } from './bootstrap-client.js';

describe('bootstrap-client', () => {
    it('fetches context from data-server contract endpoint', async () => {
        const server = createServer((req, res) => {
            if (req.method === 'POST' && req.url === '/bootstrap') {
                res.statusCode = 200;
                res.setHeader('content-type', 'application/json');
                res.end(JSON.stringify({ system: 'test-system', messages: ['morphism:x'] }));
                return;
            }
            res.statusCode = 404;
            res.end();
        });

        await new Promise<void>((resolve) => server.listen(0, resolve));
        const { port } = server.address() as AddressInfo;

        const context = await fetchBootstrapContext(`http://127.0.0.1:${port}`, ['x']);

        expect(context.system).toBe('test-system');
        expect(context.messages).toEqual([
            {
                role: 'user',
                content: 'morphism:x',
            },
        ]);

        await new Promise<void>((resolve, reject) => {
            server.close((error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });
    });
});
