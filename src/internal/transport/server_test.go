package transport

import (
	"bytes"
	"encoding/json"
	"net/http/httptest"
	"testing"

	"moos/src/internal/cat"
	"moos/src/internal/functor"
	"moos/src/internal/shell"
)

func setupTestServer(t *testing.T) *Server {
	t.Helper()
	store := shell.NewMemStore()
	rt, err := shell.NewRuntime(store, nil)
	if err != nil {
		t.Fatal(err)
	}
	return NewServer(rt, functor.MockUILens{})
}

func TestHealthz(t *testing.T) {
	srv := setupTestServer(t)
	req := httptest.NewRequest("GET", "/healthz", nil)
	w := httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)

	if w.Code != 200 {
		t.Fatalf("expected 200, got %d", w.Code)
	}
	var body map[string]any
	json.NewDecoder(w.Body).Decode(&body)
	if body["status"] != "ok" {
		t.Fatalf("expected status ok, got %v", body["status"])
	}
}

func TestPostMorphismAndQueryNode(t *testing.T) {
	srv := setupTestServer(t)

	// POST a morphism
	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: "urn:test:actor",
		Add:   &cat.AddPayload{URN: "urn:test:node", Kind: "TestKind", Stratum: cat.S2},
	}
	body, _ := json.Marshal(env)
	req := httptest.NewRequest("POST", "/morphisms", bytes.NewReader(body))
	w := httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("POST /morphisms: expected 200, got %d: %s", w.Code, w.Body.String())
	}

	// GET the node
	req = httptest.NewRequest("GET", "/state/nodes/urn:test:node", nil)
	w = httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("GET node: expected 200, got %d", w.Code)
	}
	var node cat.Node
	json.NewDecoder(w.Body).Decode(&node)
	if node.URN != "urn:test:node" {
		t.Fatalf("expected urn:test:node, got %s", node.URN)
	}
}

func TestPostProgramAtomic(t *testing.T) {
	srv := setupTestServer(t)

	prog := cat.Program{
		Actor: "urn:actor",
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:a", Kind: "K", Stratum: cat.S2}},
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:b", Kind: "K", Stratum: cat.S2}},
		},
	}
	body, _ := json.Marshal(prog)
	req := httptest.NewRequest("POST", "/programs", bytes.NewReader(body))
	w := httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("POST /programs: expected 200, got %d: %s", w.Code, w.Body.String())
	}

	// Verify state
	req = httptest.NewRequest("GET", "/state/nodes", nil)
	w = httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	var nodes map[string]cat.Node
	json.NewDecoder(w.Body).Decode(&nodes)
	if len(nodes) != 2 {
		t.Fatalf("expected 2 nodes, got %d", len(nodes))
	}
}

func TestFunctorUI(t *testing.T) {
	srv := setupTestServer(t)

	// Add a node first
	env := cat.Envelope{
		Type: cat.ADD, Actor: "urn:actor",
		Add: &cat.AddPayload{URN: "urn:n", Kind: "K", Stratum: cat.S2},
	}
	body, _ := json.Marshal(env)
	req := httptest.NewRequest("POST", "/morphisms", bytes.NewReader(body))
	w := httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)

	// GET /functor/ui
	req = httptest.NewRequest("GET", "/functor/ui", nil)
	w = httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d", w.Code)
	}
	var proj functor.UIProjection
	json.NewDecoder(w.Body).Decode(&proj)
	if len(proj.Nodes) != 1 {
		t.Fatalf("expected 1 UI node, got %d", len(proj.Nodes))
	}
}

func TestExplorer(t *testing.T) {
	srv := setupTestServer(t)
	req := httptest.NewRequest("GET", "/explorer", nil)
	w := httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d", w.Code)
	}
	ct := w.Header().Get("Content-Type")
	if ct != "text/html; charset=utf-8" {
		t.Fatalf("expected text/html, got %s", ct)
	}
}

func TestInvalidMorphism(t *testing.T) {
	srv := setupTestServer(t)
	req := httptest.NewRequest("POST", "/morphisms", bytes.NewReader([]byte(`{}`)))
	w := httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	if w.Code != 422 {
		t.Fatalf("expected 422 for invalid morphism, got %d", w.Code)
	}
}

func TestNodeNotFound(t *testing.T) {
	srv := setupTestServer(t)
	req := httptest.NewRequest("GET", "/state/nodes/urn:nonexistent", nil)
	w := httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	if w.Code != 404 {
		t.Fatalf("expected 404, got %d", w.Code)
	}
}

func TestLog(t *testing.T) {
	srv := setupTestServer(t)
	req := httptest.NewRequest("GET", "/log", nil)
	w := httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d", w.Code)
	}
}

func TestRegistry(t *testing.T) {
	srv := setupTestServer(t)
	req := httptest.NewRequest("GET", "/semantics/registry", nil)
	w := httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d", w.Code)
	}
}
