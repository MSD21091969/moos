import { cpSync, mkdirSync, rmSync } from 'node:fs';
import { resolve } from 'node:path';

const root = process.cwd();
const dist = resolve(root, 'dist');

rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });

for (const file of ['manifest.json', 'service_worker.js', 'sidepanel.html']) {
    cpSync(resolve(root, file), resolve(dist, file));
}

console.log('[extension-build] unpacked extension output -> dist');
