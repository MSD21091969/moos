export interface BootstrapContext {
    system: string;
    messages: string[];
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

    return (await response.json()) as BootstrapContext;
};
