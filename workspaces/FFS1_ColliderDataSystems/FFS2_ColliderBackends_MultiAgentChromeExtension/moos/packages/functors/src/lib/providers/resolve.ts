import type { ProviderFunctor } from '../types.js';
import { AnthropicProviderFunctor } from './anthropic.js';
import { GeminiProviderFunctor } from './gemini.js';
import { OpenAiProviderFunctor } from './openai.js';

function requireEnv(name: string): string {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Missing required environment variable: ${name}`);
    }
    return value;
}

export function resolveProvider(providerName?: string): ProviderFunctor {
    const name = providerName ?? process.env.MOOS_PROVIDER ?? 'anthropic';
    const model = process.env.MOOS_MODEL;

    switch (name) {
        case 'anthropic':
            return new AnthropicProviderFunctor(
                requireEnv('ANTHROPIC_API_KEY'),
                model ?? 'claude-sonnet-4-6',
            );
        case 'gemini':
            return new GeminiProviderFunctor(
                requireEnv('GEMINI_API_KEY'),
                model ?? 'gemini-2.5-flash',
            );
        case 'openai':
            return new OpenAiProviderFunctor(
                requireEnv('OPENAI_API_KEY'),
                model ?? 'gpt-4o',
            );
        default:
            throw new Error(`Unknown provider: ${name}. Valid: anthropic, gemini, openai`);
    }
}
