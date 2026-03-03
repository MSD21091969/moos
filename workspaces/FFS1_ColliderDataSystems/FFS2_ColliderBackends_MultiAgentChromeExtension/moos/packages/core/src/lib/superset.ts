import { z } from 'zod';

const JsonValueSchema: z.ZodType<unknown> = z.lazy(() =>
    z.union([
        z.string(),
        z.number(),
        z.boolean(),
        z.null(),
        z.array(JsonValueSchema),
        z.record(z.string(), JsonValueSchema),
    ]),
);

const BaseMorphismSchema = z.object({
    morphism_type: z.string(),
});

export const AddNodeContainerSchema = BaseMorphismSchema.extend({
    morphism_type: z.literal('ADD_NODE_CONTAINER'),
    node_type: z.string().min(1),
    temp_urn: z.string().min(1),
    properties: z.record(z.string(), JsonValueSchema).default({}),
});

export const LinkNodesSchema = BaseMorphismSchema.extend({
    morphism_type: z.literal('LINK_NODES'),
    source_urn: z.string().min(1),
    target_urn: z.string().min(1),
    edge_type: z.string().min(1),
});

export const UpdateNodeKernelSchema = BaseMorphismSchema.extend({
    morphism_type: z.literal('UPDATE_NODE_KERNEL'),
    urn: z.string().min(1),
    kernel_data: z.record(z.string(), JsonValueSchema),
});

export const DeleteEdgeSchema = BaseMorphismSchema.extend({
    morphism_type: z.literal('DELETE_EDGE'),
    source_urn: z.string().min(1),
    target_urn: z.string().min(1),
    edge_type: z.string().min(1),
});

export const GraphMorphismSchema = z.discriminatedUnion('morphism_type', [
    AddNodeContainerSchema,
    LinkNodesSchema,
    UpdateNodeKernelSchema,
    DeleteEdgeSchema,
]);

export const GraphMutationOutputSchema = z.object({
    morphisms: z.array(GraphMorphismSchema),
});

export const MutationEnvelopeSchema = z.object({
    source: z.string().min(1).optional(),
    turn: z.number().int().nonnegative().optional(),
    sessionKey: z.string().min(1).optional(),
    morphisms: z.array(GraphMorphismSchema).min(1),
});

export type GraphMorphism = z.infer<typeof GraphMorphismSchema>;
export type GraphMutationOutput = z.infer<typeof GraphMutationOutputSchema>;
export type MutationEnvelope = z.infer<typeof MutationEnvelopeSchema>;

const fencedJsonRegex = /```(?:json)?\s*([\s\S]*?)\s*```/i;

export const extractJsonCandidate = (input: string): string => {
    const trimmed = input.trim();
    const fencedMatch = trimmed.match(fencedJsonRegex);
    return (fencedMatch?.[1] ?? trimmed).trim();
};

export const parseGraphMutationOutput = (
    raw: unknown,
): GraphMutationOutput | null => {
    if (raw == null) {
        return null;
    }

    if (typeof raw === 'object') {
        const result = GraphMutationOutputSchema.safeParse(raw);
        return result.success ? result.data : null;
    }

    if (typeof raw !== 'string') {
        return null;
    }

    const candidate = extractJsonCandidate(raw);
    if (!candidate) {
        return null;
    }

    try {
        const parsed = JSON.parse(candidate) as unknown;
        const result = GraphMutationOutputSchema.safeParse(parsed);
        return result.success ? result.data : null;
    } catch {
        return null;
    }
};

export const parseMutationEnvelope = (raw: unknown): MutationEnvelope | null => {
    const result = MutationEnvelopeSchema.safeParse(raw);
    return result.success ? result.data : null;
};
