import type { AgentEvent } from "../event-parser.js";

export interface ShadowTrafficSample {
    sessionId: string;
    anthropicEvents: AgentEvent[];
    piEvents: AgentEvent[];
    criticalPolicyBypasses?: number;
}

export interface ShadowValidationThresholds {
    minEventParityPercent: number;
    maxTaskCompletionDeltaPercent: number;
    maxToolErrorRateDeltaPercent: number;
    maxTokenUsageDeltaPercent: number;
    maxCriticalPolicyBypasses: number;
}

export interface ShadowValidationMetrics {
    sampleCount: number;
    eventParityPercent: number;
    baselineTaskCompletionRate: number;
    piTaskCompletionRate: number;
    taskCompletionDeltaPercent: number;
    baselineToolErrorRate: number;
    piToolErrorRate: number;
    toolErrorRateDeltaPercent: number;
    baselineEstimatedTokens: number;
    piEstimatedTokens: number;
    tokenUsageDeltaPercent: number;
    criticalPolicyBypasses: number;
}

export interface ShadowValidationResult {
    metrics: ShadowValidationMetrics;
    thresholds: ShadowValidationThresholds;
    pass: boolean;
    failures: string[];
}

const DEFAULT_THRESHOLDS: ShadowValidationThresholds = {
    minEventParityPercent: 99,
    maxTaskCompletionDeltaPercent: 10,
    maxToolErrorRateDeltaPercent: 5,
    maxTokenUsageDeltaPercent: 15,
    maxCriticalPolicyBypasses: 0,
};

interface EventStats {
    eventKinds: string[];
    completed: boolean;
    hasError: boolean;
    toolErrors: number;
    estimatedTokens: number;
}

export function evaluateShadowTraffic(
    samples: ShadowTrafficSample[],
    thresholds: Partial<ShadowValidationThresholds> = {},
): ShadowValidationResult {
    const resolvedThresholds: ShadowValidationThresholds = {
        ...DEFAULT_THRESHOLDS,
        ...thresholds,
    };

    if (samples.length === 0) {
        const emptyMetrics: ShadowValidationMetrics = {
            sampleCount: 0,
            eventParityPercent: 0,
            baselineTaskCompletionRate: 0,
            piTaskCompletionRate: 0,
            taskCompletionDeltaPercent: 0,
            baselineToolErrorRate: 0,
            piToolErrorRate: 0,
            toolErrorRateDeltaPercent: 0,
            baselineEstimatedTokens: 0,
            piEstimatedTokens: 0,
            tokenUsageDeltaPercent: 0,
            criticalPolicyBypasses: 0,
        };

        return {
            metrics: emptyMetrics,
            thresholds: resolvedThresholds,
            pass: false,
            failures: ["No shadow samples available"],
        };
    }

    const baselineStats = samples.map((sample) => summarizeEvents(sample.anthropicEvents));
    const piStats = samples.map((sample) => summarizeEvents(sample.piEvents));

    const eventParityPercent = computeEventParityPercent(baselineStats, piStats);
    const baselineTaskCompletionRate = ratio(
        baselineStats.filter((stats) => stats.completed && !stats.hasError).length,
        baselineStats.length,
    );
    const piTaskCompletionRate = ratio(
        piStats.filter((stats) => stats.completed && !stats.hasError).length,
        piStats.length,
    );

    const taskCompletionDeltaPercent = percentDifference(
        baselineTaskCompletionRate,
        piTaskCompletionRate,
    );

    const baselineToolErrorRate = ratio(
        baselineStats.reduce((sum, stats) => sum + stats.toolErrors, 0),
        Math.max(1, baselineStats.reduce((sum, stats) => sum + countToolUses(stats.eventKinds), 0)),
    );
    const piToolErrorRate = ratio(
        piStats.reduce((sum, stats) => sum + stats.toolErrors, 0),
        Math.max(1, piStats.reduce((sum, stats) => sum + countToolUses(stats.eventKinds), 0)),
    );

    const toolErrorRateDeltaPercent = percentDifference(
        baselineToolErrorRate,
        piToolErrorRate,
    );

    const baselineEstimatedTokens = baselineStats.reduce(
        (sum, stats) => sum + stats.estimatedTokens,
        0,
    );
    const piEstimatedTokens = piStats.reduce((sum, stats) => sum + stats.estimatedTokens, 0);
    const tokenUsageDeltaPercent = percentDifference(
        baselineEstimatedTokens,
        piEstimatedTokens,
    );

    const criticalPolicyBypasses = samples.reduce(
        (sum, sample) => sum + (sample.criticalPolicyBypasses ?? 0),
        0,
    );

    const metrics: ShadowValidationMetrics = {
        sampleCount: samples.length,
        eventParityPercent,
        baselineTaskCompletionRate,
        piTaskCompletionRate,
        taskCompletionDeltaPercent,
        baselineToolErrorRate,
        piToolErrorRate,
        toolErrorRateDeltaPercent,
        baselineEstimatedTokens,
        piEstimatedTokens,
        tokenUsageDeltaPercent,
        criticalPolicyBypasses,
    };

    const failures: string[] = [];
    if (metrics.eventParityPercent < resolvedThresholds.minEventParityPercent) {
        failures.push(
            `Event parity ${metrics.eventParityPercent.toFixed(2)}% below threshold ${resolvedThresholds.minEventParityPercent}%`,
        );
    }
    if (metrics.taskCompletionDeltaPercent > resolvedThresholds.maxTaskCompletionDeltaPercent) {
        failures.push(
            `Task completion delta ${metrics.taskCompletionDeltaPercent.toFixed(2)}% above threshold ${resolvedThresholds.maxTaskCompletionDeltaPercent}%`,
        );
    }
    if (metrics.toolErrorRateDeltaPercent > resolvedThresholds.maxToolErrorRateDeltaPercent) {
        failures.push(
            `Tool error rate delta ${metrics.toolErrorRateDeltaPercent.toFixed(2)}% above threshold ${resolvedThresholds.maxToolErrorRateDeltaPercent}%`,
        );
    }
    if (metrics.tokenUsageDeltaPercent > resolvedThresholds.maxTokenUsageDeltaPercent) {
        failures.push(
            `Token usage delta ${metrics.tokenUsageDeltaPercent.toFixed(2)}% above threshold ${resolvedThresholds.maxTokenUsageDeltaPercent}%`,
        );
    }
    if (metrics.criticalPolicyBypasses > resolvedThresholds.maxCriticalPolicyBypasses) {
        failures.push(
            `Critical policy bypasses ${metrics.criticalPolicyBypasses} above threshold ${resolvedThresholds.maxCriticalPolicyBypasses}`,
        );
    }

    return {
        metrics,
        thresholds: resolvedThresholds,
        pass: failures.length === 0,
        failures,
    };
}

function summarizeEvents(events: AgentEvent[]): EventStats {
    const eventKinds = events.map((event) => event.kind);

    let toolErrors = 0;
    let estimatedChars = 0;
    for (const event of events) {
        if (event.kind === "text_delta") {
            estimatedChars += event.text.length;
        } else if (event.kind === "tool_use_start") {
            estimatedChars += event.name.length + event.args.length;
        } else if (event.kind === "tool_result") {
            estimatedChars += event.name.length + event.result.length;
            if (/error|failed|denied|forbidden/i.test(event.result)) {
                toolErrors += 1;
            }
        } else if (event.kind === "thinking") {
            estimatedChars += event.text.length;
        } else if (event.kind === "error") {
            estimatedChars += event.message.length;
            toolErrors += 1;
        }
    }

    return {
        eventKinds,
        completed: eventKinds.includes("message_end"),
        hasError: eventKinds.includes("error"),
        toolErrors,
        estimatedTokens: Math.ceil(estimatedChars / 4),
    };
}

function computeEventParityPercent(
    baselineStats: EventStats[],
    piStats: EventStats[],
): number {
    let equalCount = 0;
    let totalCount = 0;

    const sampleCount = Math.min(baselineStats.length, piStats.length);
    for (let sampleIndex = 0; sampleIndex < sampleCount; sampleIndex += 1) {
        const baselineKinds = baselineStats[sampleIndex].eventKinds;
        const piKinds = piStats[sampleIndex].eventKinds;
        const maxLen = Math.max(baselineKinds.length, piKinds.length);

        for (let idx = 0; idx < maxLen; idx += 1) {
            const left = baselineKinds[idx] ?? "<missing>";
            const right = piKinds[idx] ?? "<missing>";
            if (left === right) {
                equalCount += 1;
            }
            totalCount += 1;
        }
    }

    return ratio(equalCount, totalCount) * 100;
}

function countToolUses(eventKinds: string[]): number {
    return eventKinds.filter((kind) => kind === "tool_use_start").length;
}

function ratio(numerator: number, denominator: number): number {
    if (denominator <= 0) return 0;
    return numerator / denominator;
}

function percentDifference(baseline: number, candidate: number): number {
    if (baseline === 0) {
        return candidate === 0 ? 0 : 100;
    }
    return Math.abs((candidate - baseline) / baseline) * 100;
}
