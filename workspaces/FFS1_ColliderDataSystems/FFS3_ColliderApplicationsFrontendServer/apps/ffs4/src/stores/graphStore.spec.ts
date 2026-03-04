/**
 * graphStore.spec.ts — Comprehensive tests for Zustand graph state
 *
 * Covers: applyMorphisms (ADD_NODE_CONTAINER, LINK_NODES, UPDATE_NODE_KERNEL,
 * DELETE_EDGE), setActiveState, reset, duplicate handling, edge cases.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { useGraphStore } from "./graphStore";

function getState() {
    return useGraphStore.getState();
}

function act(fn: () => void) {
    fn();
}

beforeEach(() => {
    act(() => getState().reset());
});

// ---------------------------------------------------------------------------
// ADD_NODE_CONTAINER
// ---------------------------------------------------------------------------

describe("ADD_NODE_CONTAINER", () => {
    it("adds a new node to an empty graph", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:moos:test:1",
                    properties: { label: "Node 1" },
                },
            ])
        );

        const { nodes } = getState();
        expect(nodes).toHaveLength(1);
        expect(nodes[0].id).toBe("urn:moos:test:1");
        expect(nodes[0].data.label).toBe("Node 1");
        expect(nodes[0].data.domain).toBe("data");
        expect(nodes[0].data.hasContainer).toBe(true);
    });

    it("uses thought as label fallback", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "agent",
                    temp_urn: "urn:moos:test:2",
                    properties: { thought: "My reasoning node" },
                },
            ])
        );

        expect(getState().nodes[0].data.label).toBe("My reasoning node");
    });

    it("uses URN as label when no properties", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:moos:test:3",
                },
            ])
        );

        expect(getState().nodes[0].data.label).toBe("urn:moos:test:3");
    });

    it("rejects duplicate node URNs (idempotent)", () => {
        const morphism = {
            morphism_type: "ADD_NODE_CONTAINER" as const,
            node_type: "data",
            temp_urn: "urn:moos:dup:1",
            properties: { label: "First" },
        };

        act(() => getState().applyMorphisms([morphism]));
        act(() => getState().applyMorphisms([morphism]));

        expect(getState().nodes).toHaveLength(1);
        expect(getState().nodes[0].data.label).toBe("First");
    });

    it("adds multiple nodes in a single batch", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:a",
                    properties: { label: "A" },
                },
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "agent",
                    temp_urn: "urn:b",
                    properties: { label: "B" },
                },
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "tool",
                    temp_urn: "urn:c",
                    properties: { label: "C" },
                },
            ])
        );

        expect(getState().nodes).toHaveLength(3);
    });

    it("initializes skillCount and toolCount to zero", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:moos:init:1",
                },
            ])
        );

        const node = getState().nodes[0];
        expect(node.data.skillCount).toBe(0);
        expect(node.data.toolCount).toBe(0);
        expect(node.data.isSelected).toBe(false);
    });
});

// ---------------------------------------------------------------------------
// LINK_NODES
// ---------------------------------------------------------------------------

describe("LINK_NODES", () => {
    it("creates an edge between nodes", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:src",
                },
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:tgt",
                },
                {
                    morphism_type: "LINK_NODES",
                    source_urn: "urn:src",
                    target_urn: "urn:tgt",
                    edge_type: "data_flow",
                },
            ])
        );

        const { edges } = getState();
        expect(edges).toHaveLength(1);
        expect(edges[0].source).toBe("urn:src");
        expect(edges[0].target).toBe("urn:tgt");
        expect(edges[0].data?.edge_type).toBe("data_flow");
    });

    it("rejects duplicate edges (idempotent)", () => {
        const add = [
            {
                morphism_type: "ADD_NODE_CONTAINER" as const,
                node_type: "data",
                temp_urn: "urn:a",
            },
            {
                morphism_type: "ADD_NODE_CONTAINER" as const,
                node_type: "data",
                temp_urn: "urn:b",
            },
        ];
        const link = {
            morphism_type: "LINK_NODES" as const,
            source_urn: "urn:a",
            target_urn: "urn:b",
            edge_type: "dep",
        };

        act(() => getState().applyMorphisms([...add, link]));
        act(() => getState().applyMorphisms([link]));

        expect(getState().edges).toHaveLength(1);
    });

    it("allows different edge types between same nodes", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "LINK_NODES",
                    source_urn: "urn:x",
                    target_urn: "urn:y",
                    edge_type: "flow",
                },
                {
                    morphism_type: "LINK_NODES",
                    source_urn: "urn:x",
                    target_urn: "urn:y",
                    edge_type: "control",
                },
            ])
        );

        expect(getState().edges).toHaveLength(2);
    });
});

// ---------------------------------------------------------------------------
// UPDATE_NODE_KERNEL
// ---------------------------------------------------------------------------

describe("UPDATE_NODE_KERNEL", () => {
    it("updates existing node data", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:upd",
                    properties: { label: "Original" },
                },
            ])
        );
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "UPDATE_NODE_KERNEL",
                    urn: "urn:upd",
                    kernel_data: { label: "Updated", emoji: "🔄" },
                },
            ])
        );

        const node = getState().nodes[0];
        expect(node.data.label).toBe("Updated");
        expect(node.data.emoji).toBe("🔄");
        // Verify non-updated fields preserved
        expect(node.data.domain).toBe("data");
    });

    it("no-ops for unknown URN", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:exists",
                },
            ])
        );
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "UPDATE_NODE_KERNEL",
                    urn: "urn:missing",
                    kernel_data: { label: "X" },
                },
            ])
        );

        expect(getState().nodes).toHaveLength(1);
        expect(getState().nodes[0].data.label).toBe("urn:exists");
    });
});

// ---------------------------------------------------------------------------
// DELETE_EDGE
// ---------------------------------------------------------------------------

describe("DELETE_EDGE", () => {
    it("removes an edge between two nodes", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "LINK_NODES",
                    source_urn: "urn:a",
                    target_urn: "urn:b",
                    edge_type: "flow",
                },
            ])
        );
        expect(getState().edges).toHaveLength(1);

        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "DELETE_EDGE",
                    source_urn: "urn:a",
                    target_urn: "urn:b",
                    edge_type: "flow",
                },
            ])
        );
        expect(getState().edges).toHaveLength(0);
    });

    it("no-ops when edge does not exist", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "DELETE_EDGE",
                    source_urn: "urn:ghost",
                    target_urn: "urn:ghost2",
                    edge_type: "x",
                },
            ])
        );
        expect(getState().edges).toHaveLength(0);
    });

    it("removes all edges matching source/target regardless of type", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "LINK_NODES",
                    source_urn: "urn:x",
                    target_urn: "urn:y",
                    edge_type: "flow",
                },
                {
                    morphism_type: "LINK_NODES",
                    source_urn: "urn:x",
                    target_urn: "urn:y",
                    edge_type: "control",
                },
            ])
        );
        expect(getState().edges).toHaveLength(2);

        // DELETE_EDGE matches on source + target only (per implementation)
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "DELETE_EDGE",
                    source_urn: "urn:x",
                    target_urn: "urn:y",
                    edge_type: "flow",
                },
            ])
        );
        // Implementation deletes ALL edges between source/target
        expect(getState().edges).toHaveLength(0);
    });
});

// ---------------------------------------------------------------------------
// setActiveState
// ---------------------------------------------------------------------------

describe("setActiveState", () => {
    it("replaces all nodes and edges", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:old",
                },
            ])
        );
        expect(getState().nodes).toHaveLength(1);

        act(() =>
            getState().setActiveState(
                [{ id: "urn:new", type: "nodeCard", position: { x: 0, y: 0 }, data: {} }],
                [{ id: "e-1", source: "urn:new", target: "urn:new" }]
            )
        );

        expect(getState().nodes).toHaveLength(1);
        expect(getState().nodes[0].id).toBe("urn:new");
        expect(getState().edges).toHaveLength(1);
    });

    it("handles empty arrays", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:temp",
                },
            ])
        );
        act(() => getState().setActiveState([], []));

        expect(getState().nodes).toHaveLength(0);
        expect(getState().edges).toHaveLength(0);
    });
});

// ---------------------------------------------------------------------------
// reset
// ---------------------------------------------------------------------------

describe("reset", () => {
    it("clears all state", () => {
        act(() => {
            getState().setLoading(true);
            getState().setError("some error");
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:reset",
                },
            ]);
        });

        act(() => getState().reset());

        const state = getState();
        expect(state.nodes).toHaveLength(0);
        expect(state.edges).toHaveLength(0);
        expect(state.loading).toBe(false);
        expect(state.error).toBeNull();
    });
});

// ---------------------------------------------------------------------------
// Mixed morphism sequences
// ---------------------------------------------------------------------------

describe("mixed morphism sequences", () => {
    it("handles ADD → LINK → UPDATE → DELETE in one batch", () => {
        act(() =>
            getState().applyMorphisms([
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "data",
                    temp_urn: "urn:n1",
                    properties: { label: "N1" },
                },
                {
                    morphism_type: "ADD_NODE_CONTAINER",
                    node_type: "agent",
                    temp_urn: "urn:n2",
                    properties: { label: "N2" },
                },
                {
                    morphism_type: "LINK_NODES",
                    source_urn: "urn:n1",
                    target_urn: "urn:n2",
                    edge_type: "depends",
                },
                {
                    morphism_type: "UPDATE_NODE_KERNEL",
                    urn: "urn:n1",
                    kernel_data: { label: "N1 Updated" },
                },
                {
                    morphism_type: "DELETE_EDGE",
                    source_urn: "urn:n1",
                    target_urn: "urn:n2",
                    edge_type: "depends",
                },
            ])
        );

        const { nodes, edges } = getState();
        expect(nodes).toHaveLength(2);
        expect(nodes[0].data.label).toBe("N1 Updated");
        expect(edges).toHaveLength(0);
    });
});

// ---------------------------------------------------------------------------
// Edge cases
// ---------------------------------------------------------------------------

describe("edge cases", () => {
    it("ignores unknown morphism types", () => {
        act(() =>
            getState().applyMorphisms([
                { morphism_type: "UNKNOWN_OP", data: {} },
            ])
        );

        expect(getState().nodes).toHaveLength(0);
        expect(getState().edges).toHaveLength(0);
    });

    it("ignores objects without morphism_type", () => {
        act(() => getState().applyMorphisms([{ foo: "bar" }, null, 42, "string"]));

        expect(getState().nodes).toHaveLength(0);
        expect(getState().edges).toHaveLength(0);
    });

    it("handles empty morphism array", () => {
        act(() => getState().applyMorphisms([]));

        expect(getState().nodes).toHaveLength(0);
        expect(getState().edges).toHaveLength(0);
    });

    it("setLoading and setError work independently", () => {
        act(() => getState().setLoading(true));
        expect(getState().loading).toBe(true);

        act(() => getState().setError("test error"));
        expect(getState().error).toBe("test error");
        expect(getState().loading).toBe(true);
    });
});
