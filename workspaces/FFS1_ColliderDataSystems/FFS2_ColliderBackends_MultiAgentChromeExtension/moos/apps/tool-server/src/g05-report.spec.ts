import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import type { AddressInfo } from 'node:net';
import { createToolServer } from './main.js';

interface G05Report {
    reportId: 'TOOL-TEST-REPORT-v1';
    generatedAt: string;
    sampleSizes: {
        conformanceCalls: number;
        availabilityCalls: number;
        isolationCalls: number;
    };
    thresholds: {
        toolSuccessRateMin: number;
        mcpAvailabilityMin: number;
        p95LatencyMsMax: number;
        isolationEscapesMax: number;
    };
    metrics: {
        toolSuccessRate: number;
        mcpAvailability: number;
        p95LatencyMs: number;
        isolationEscapes: number;
    };
    pass: {
        toolSuccessRate: boolean;
        mcpAvailability: boolean;
        p95Latency: boolean;
        isolationEscapes: boolean;
        overall: boolean;
    };
}

const percentile = (values: number[], p: number): number => {
    if (values.length === 0) {
        return 0;
    }

    const sorted = [...values].sort((a, b) => a - b);
    const index = Math.max(0, Math.ceil(sorted.length * p) - 1);
    return sorted[index];
};

describe('tool-server g05 conformance evidence', () => {
    it('produces TOOL-TEST-REPORT-v1 and enforces gate thresholds', async () => {
        const conformanceCalls = Number(process.env.G05_CONFORMANCE_CALLS ?? 400);
        const availabilityCalls = Number(process.env.G05_AVAILABILITY_CALLS ?? 200);
        const isolationCalls = Number(process.env.G05_ISOLATION_CALLS ?? 100);

        const toolSuccessRateMin = Number(process.env.G05_TOOL_SUCCESS_RATE_MIN ?? 0.99);
        const mcpAvailabilityMin = Number(process.env.G05_MCP_AVAILABILITY_MIN ?? 0.995);
        const p95LatencyMsMax = Number(process.env.G05_P95_LATENCY_MAX_MS ?? 1500);
        const isolationEscapesMax = Number(process.env.G05_ISOLATION_ESCAPES_MAX ?? 0);

        const server = createToolServer();
        await new Promise<void>((resolve) => server.listen(0, resolve));
        const { port } = server.address() as AddressInfo;
        const base = `http://127.0.0.1:${port}`;

        let successfulConformanceCalls = 0;
        const latencies: number[] = [];

        for (let index = 0; index < conformanceCalls; index += 1) {
            const method = index % 2 === 0 ? 'tools/list' : 'tools/call';
            const startedAt = Date.now();

            const response = await fetch(`${base}/mcp/messages`, {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    id: `g05-conformance-${index}`,
                    method,
                    params:
                        method === 'tools/call'
                            ? { name: 'echo_tool', input: { seq: index } }
                            : {},
                }),
            });

            const elapsed = Date.now() - startedAt;
            latencies.push(elapsed);

            if (!response.ok) {
                continue;
            }

            const payload = (await response.json()) as {
                jsonrpc: string;
                result?: unknown;
                error?: unknown;
            };

            if (payload.jsonrpc === '2.0' && payload.error === undefined && payload.result !== undefined) {
                successfulConformanceCalls += 1;
            }
        }

        let availableResponses = 0;
        for (let index = 0; index < availabilityCalls; index += 1) {
            const response = await fetch(`${base}/mcp/messages`, {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    id: `g05-availability-${index}`,
                    method: 'tools/list',
                    params: {},
                }),
            });

            if (response.ok) {
                availableResponses += 1;
            }
        }

        let isolationEscapes = 0;
        for (let index = 0; index < isolationCalls; index += 1) {
            const response = await fetch(`${base}/execute`, {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({
                    id: `g05-isolation-${index}`,
                    name: `internal_forbidden_${index}`,
                    input: { probe: true },
                }),
            });

            const payload = (await response.json()) as {
                error?: string;
            };

            if (payload.error !== 'isolation_blocked_tool') {
                isolationEscapes += 1;
            }
        }

        const toolSuccessRate =
            conformanceCalls > 0 ? successfulConformanceCalls / conformanceCalls : 0;
        const mcpAvailability = availabilityCalls > 0 ? availableResponses / availabilityCalls : 0;
        const p95LatencyMs = percentile(latencies, 0.95);

        const report: G05Report = {
            reportId: 'TOOL-TEST-REPORT-v1',
            generatedAt: new Date().toISOString(),
            sampleSizes: {
                conformanceCalls,
                availabilityCalls,
                isolationCalls,
            },
            thresholds: {
                toolSuccessRateMin,
                mcpAvailabilityMin,
                p95LatencyMsMax,
                isolationEscapesMax,
            },
            metrics: {
                toolSuccessRate,
                mcpAvailability,
                p95LatencyMs,
                isolationEscapes,
            },
            pass: {
                toolSuccessRate: toolSuccessRate >= toolSuccessRateMin,
                mcpAvailability: mcpAvailability >= mcpAvailabilityMin,
                p95Latency: p95LatencyMs <= p95LatencyMsMax,
                isolationEscapes: isolationEscapes <= isolationEscapesMax,
                overall: false,
            },
        };

        report.pass.overall =
            report.pass.toolSuccessRate &&
            report.pass.mcpAvailability &&
            report.pass.p95Latency &&
            report.pass.isolationEscapes;

        const normalizedCwd = process.cwd().replace(/\\/g, '/');
        const reportDirectory = normalizedCwd.endsWith('/apps/tool-server')
            ? join(process.cwd(), 'reports')
            : join(process.cwd(), 'apps', 'tool-server', 'reports');
        await mkdir(reportDirectory, { recursive: true });
        await writeFile(
            join(reportDirectory, 'TOOL-TEST-REPORT-v1.json'),
            `${JSON.stringify(report, null, 2)}\n`,
            'utf-8',
        );

        await new Promise<void>((resolve, reject) => {
            server.close((error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });

        expect(report.pass.toolSuccessRate).toBe(true);
        expect(report.pass.mcpAvailability).toBe(true);
        expect(report.pass.p95Latency).toBe(true);
        expect(report.pass.isolationEscapes).toBe(true);
        expect(report.pass.overall).toBe(true);
    });
});
