import type { Message } from '@moos/functors';

export interface BootstrapContext {
    system: string;
    messages: Message[];
}

export const fetchBootstrapContext = async (
    dataServerBaseUrl: string,
    morphismIds: string[],
    system = 'moos-bootstrap',
): Promise<BootstrapContext> => {
    const response = await fetch(`${dataServerBaseUrl}/bootstrap`, {
        method: 'POST',
        headers: {
            'content-type': 'application/json',
        },
        body: JSON.stringify({ morphismIds, system }),
    });

    if (!response.ok) {
        return {
            system,
            messages: [],
        };
    }

    const raw = (await response.json()) as { system: string; messages: string[] };

    // Convert string messages from store into Message objects
    return {
        system: raw.system,
        messages: raw.messages.map((text): Message => ({
            role: 'user',
            content: text,
        })),
    };
};
