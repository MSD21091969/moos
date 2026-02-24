export type PiModelProvider = "gemini" | "anthropic" | "ollama";

export interface ResolvedPiModel {
    provider: PiModelProvider;
    model: string;
    apiKey?: string;
    baseUrl?: string;
}

const DEFAULT_MODELS: Record<PiModelProvider, string> = {
    gemini: "gemini-2.5-flash",
    anthropic: "claude-sonnet-4-6",
    ollama: "llama3",
};

export function resolvePiModel(modelOverride?: string): ResolvedPiModel {
    const rawProvider = (process.env.COLLIDER_AGENT_PROVIDER ?? "gemini").toLowerCase();
    const provider = toProvider(rawProvider);

    const model = modelOverride ?? process.env.COLLIDER_AGENT_MODEL ?? DEFAULT_MODELS[provider];

    switch (provider) {
        case "gemini":
            return {
                provider,
                model,
                apiKey: process.env.GEMINI_API_KEY,
            };

        case "anthropic":
            return {
                provider,
                model,
                apiKey: process.env.ANTHROPIC_API_KEY,
            };

        case "ollama":
            return {
                provider,
                model,
                baseUrl: process.env.OLLAMA_BASE_URL ?? "http://localhost:11434",
            };
    }
}

function toProvider(value: string): PiModelProvider {
    if (value === "gemini" || value === "anthropic" || value === "ollama") {
        return value;
    }
    throw new Error(`Unsupported COLLIDER_AGENT_PROVIDER: ${value}`);
}
