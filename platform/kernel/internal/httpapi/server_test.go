package httpapi

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"

	"moos/platform/kernel/internal/core"
	"moos/platform/kernel/internal/shell"
)

func TestServerProjectionEndpoints(t *testing.T) {
	registry, err := shell.LoadRegistry(filepath.Join("..", "..", "..", "..", ".agent", "knowledge_base", "superset", "ontology.json"))
	if err != nil {
		t.Fatalf("load registry failed: %v", err)
	}
	runtime, err := shell.NewRuntimeWithConfig(shell.RuntimeConfig{Store: shell.LogStore{Path: filepath.Join(t.TempDir(), "morphism-log.jsonl")}, Registry: registry})
	if err != nil {
		t.Fatalf("new runtime failed: %v", err)
	}
	for _, envelope := range []core.Envelope{
		{Type: core.MorphismAdd, Actor: "actor:test", Add: &core.AddPayload{URN: "urn:a", Kind: "Node"}},
		{Type: core.MorphismAdd, Actor: "actor:test", Add: &core.AddPayload{URN: "urn:b", Kind: "Node"}},
		{Type: core.MorphismLink, Actor: "actor:test", Link: &core.LinkPayload{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in"}},
	} {
		if _, err := runtime.Apply(envelope); err != nil {
			t.Fatalf("apply failed: %v", err)
		}
	}

	server := New(runtime)

	t.Run("runtime explorer page", func(t *testing.T) {
		request := httptest.NewRequest(http.MethodGet, "/explorer", nil)
		response := httptest.NewRecorder()
		server.Handler().ServeHTTP(response, request)

		if response.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d", response.Code)
		}
		if !strings.Contains(response.Body.String(), "mo:os Runtime Explorer") {
			t.Fatalf("expected explorer markup, got %s", response.Body.String())
		}
	})

	t.Run("explorer demo example endpoint", func(t *testing.T) {
		request := httptest.NewRequest(http.MethodGet, "/hydration/examples/explorer-demo", nil)
		response := httptest.NewRecorder()
		server.Handler().ServeHTTP(response, request)

		if response.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d: %s", response.Code, response.Body.String())
		}
		if !strings.Contains(response.Body.String(), "urn:moos:demo:explorer:ingress") {
			t.Fatalf("expected explorer demo payload, got %s", response.Body.String())
		}
	})

	t.Run("state snapshot", func(t *testing.T) {
		request := httptest.NewRequest(http.MethodGet, "/state", nil)
		response := httptest.NewRecorder()
		server.Handler().ServeHTTP(response, request)

		if response.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d", response.Code)
		}
		var payload map[string]any
		if err := json.Unmarshal(response.Body.Bytes(), &payload); err != nil {
			t.Fatalf("unmarshal failed: %v", err)
		}
		if _, ok := payload["graph"]; !ok {
			t.Fatalf("expected graph in response: %s", response.Body.String())
		}
	})

	t.Run("filtered node list", func(t *testing.T) {
		request := httptest.NewRequest(http.MethodGet, "/state/nodes?kind=Node", nil)
		response := httptest.NewRecorder()
		server.Handler().ServeHTTP(response, request)

		if response.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d", response.Code)
		}
		var payload struct {
			Nodes []core.Node `json:"nodes"`
		}
		if err := json.Unmarshal(response.Body.Bytes(), &payload); err != nil {
			t.Fatalf("unmarshal failed: %v", err)
		}
		if len(payload.Nodes) != 2 {
			t.Fatalf("expected 2 nodes, got %d", len(payload.Nodes))
		}
	})

	t.Run("outgoing traversal", func(t *testing.T) {
		request := httptest.NewRequest(http.MethodGet, "/state/traversal/outgoing/urn:a", nil)
		response := httptest.NewRecorder()
		server.Handler().ServeHTTP(response, request)

		if response.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d", response.Code)
		}
		var payload struct {
			URN   string      `json:"urn"`
			Wires []core.Wire `json:"wires"`
		}
		if err := json.Unmarshal(response.Body.Bytes(), &payload); err != nil {
			t.Fatalf("unmarshal failed: %v", err)
		}
		if payload.URN != "urn:a" || len(payload.Wires) != 1 {
			t.Fatalf("unexpected outgoing payload: %+v", payload)
		}
		if payload.Wires[0].TargetURN != "urn:b" {
			t.Fatalf("expected outgoing target urn:b, got %+v", payload.Wires[0])
		}
	})

	t.Run("atomic program execution", func(t *testing.T) {
		request := httptest.NewRequest(http.MethodPost, "/programs", strings.NewReader(`{"actor":"actor:test","envelopes":[{"type":"ADD","add":{"urn":"urn:c","kind":"Node"}},{"type":"MUTATE","mutate":{"urn":"urn:c","expected_version":1,"payload":{"status":"programmed"}}}]}`))
		request.Header.Set("Content-Type", "application/json")
		response := httptest.NewRecorder()
		server.Handler().ServeHTTP(response, request)

		if response.Code != http.StatusAccepted {
			t.Fatalf("expected 202, got %d: %s", response.Code, response.Body.String())
		}
		node, ok := runtime.Node("urn:c")
		if !ok || node.Version != 2 {
			t.Fatalf("expected program-created node at version 2, got %+v", node)
		}
	})

	t.Run("semantic registry endpoint", func(t *testing.T) {
		request := httptest.NewRequest(http.MethodGet, "/semantics/registry", nil)
		response := httptest.NewRecorder()
		server.Handler().ServeHTTP(response, request)

		if response.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d", response.Code)
		}
		var payload core.SemanticRegistry
		if err := json.Unmarshal(response.Body.Bytes(), &payload); err != nil {
			t.Fatalf("unmarshal failed: %v", err)
		}
		if _, ok := payload.Kinds["NodeContainer"]; !ok {
			t.Fatalf("expected NodeContainer kind in registry, got %+v", payload)
		}
	})

	t.Run("hydration materialize and apply", func(t *testing.T) {
		request := httptest.NewRequest(http.MethodPost, "/hydration/materialize", strings.NewReader(`{"actor":"actor:test","apply":true,"nodes":[{"urn":"urn:d","kind":"Node","payload":{"stage":"authored"}},{"urn":"urn:e","kind":"Node"}],"wires":[{"source_urn":"urn:d","source_port":"out","target_urn":"urn:e","target_port":"in"}]}`))
		request.Header.Set("Content-Type", "application/json")
		response := httptest.NewRecorder()
		server.Handler().ServeHTTP(response, request)

		if response.Code != http.StatusAccepted {
			t.Fatalf("expected 202, got %d: %s", response.Code, response.Body.String())
		}
		node, ok := runtime.Node("urn:d")
		if !ok || node.Stratum != core.StratumMaterialized {
			t.Fatalf("expected materialized node urn:d, got %+v", node)
		}
		outgoing := runtime.OutgoingWires("urn:d")
		if len(outgoing) != 1 || outgoing[0].TargetURN != "urn:e" {
			t.Fatalf("expected wire from urn:d to urn:e, got %+v", outgoing)
		}
	})
}
