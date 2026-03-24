package transport_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/hydration"
	"moos/platform/kernel/internal/operad"
	"moos/platform/kernel/internal/shell"
	"moos/platform/kernel/internal/transport"
)

var testActor = cat.URN("urn:moos:identity:test-actor")

func newTestServer(t *testing.T) *transport.Server {
	t.Helper()
	store := shell.NewMemStore()
	rt, err := shell.NewRuntime(store, nil)
	if err != nil {
		t.Fatalf("NewRuntime: %v", err)
	}
	return transport.NewServer(rt, "")
}

func doRequest(t *testing.T, handler http.Handler, method, path string, body any) *httptest.ResponseRecorder {
	t.Helper()
	var buf bytes.Buffer
	if body != nil {
		json.NewEncoder(&buf).Encode(body)
	}
	req := httptest.NewRequest(method, path, &buf)
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)
	return w
}

func TestHealthz(t *testing.T) {
	srv := newTestServer(t)
	w := doRequest(t, srv.Handler(), "GET", "/healthz", nil)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
	var resp map[string]any
	json.Unmarshal(w.Body.Bytes(), &resp)
	if resp["status"] != "ok" {
		t.Errorf("expected status=ok, got %v", resp["status"])
	}
}

func TestPostMorphism_ADD(t *testing.T) {
	srv := newTestServer(t)
	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: testActor,
		Add:   &cat.AddPayload{URN: "urn:http-test", TypeID: "node_container"},
	}
	w := doRequest(t, srv.Handler(), "POST", "/morphisms", env)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
}

func TestPostProgram(t *testing.T) {
	srv := newTestServer(t)
	prog := cat.Program{
		Actor: testActor,
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:p1", TypeID: "node_container"}},
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:p2", TypeID: "node_container"}},
		},
	}
	w := doRequest(t, srv.Handler(), "POST", "/programs", prog)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
}

func TestGetState(t *testing.T) {
	srv := newTestServer(t)
	// Add a node first
	doRequest(t, srv.Handler(), "POST", "/morphisms", cat.Envelope{
		Type: cat.ADD, Actor: testActor,
		Add: &cat.AddPayload{URN: "urn:state-test", TypeID: "node_container"},
	})

	w := doRequest(t, srv.Handler(), "GET", "/state", nil)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
	var state cat.GraphState
	json.Unmarshal(w.Body.Bytes(), &state)
	if len(state.Nodes) != 1 {
		t.Errorf("expected 1 node, got %d", len(state.Nodes))
	}
}

func TestGetNodes(t *testing.T) {
	srv := newTestServer(t)
	doRequest(t, srv.Handler(), "POST", "/morphisms", cat.Envelope{
		Type: cat.ADD, Actor: testActor,
		Add: &cat.AddPayload{URN: "urn:nodes-test", TypeID: "node_container"},
	})

	w := doRequest(t, srv.Handler(), "GET", "/state/nodes", nil)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func TestGetNodeByURN(t *testing.T) {
	srv := newTestServer(t)
	doRequest(t, srv.Handler(), "POST", "/morphisms", cat.Envelope{
		Type: cat.ADD, Actor: testActor,
		Add: &cat.AddPayload{URN: "urn:lookup", TypeID: "node_container"},
	})

	w := doRequest(t, srv.Handler(), "GET", "/state/nodes/urn:lookup", nil)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
}

func TestGetNodeByURN_NotFound(t *testing.T) {
	srv := newTestServer(t)
	w := doRequest(t, srv.Handler(), "GET", "/state/nodes/urn:missing", nil)
	if w.Code != http.StatusNotFound {
		t.Errorf("expected 404, got %d", w.Code)
	}
}

func TestGetLog(t *testing.T) {
	srv := newTestServer(t)
	doRequest(t, srv.Handler(), "POST", "/morphisms", cat.Envelope{
		Type: cat.ADD, Actor: testActor,
		Add: &cat.AddPayload{URN: "urn:log-test", TypeID: "node_container"},
	})

	w := doRequest(t, srv.Handler(), "GET", "/log", nil)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
	var log []cat.PersistedEnvelope
	json.Unmarshal(w.Body.Bytes(), &log)
	if len(log) != 1 {
		t.Errorf("expected 1 log entry, got %d", len(log))
	}
}

func TestGetRegistry_Nil(t *testing.T) {
	srv := newTestServer(t)
	w := doRequest(t, srv.Handler(), "GET", "/semantics/registry", nil)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func newTestServerWithRegistry(t *testing.T) *transport.Server {
	t.Helper()
	store := shell.NewMemStore()
	ontology := `{
		"objects": [
			{
				"name": "AgentSession",
				"type_id": "agent_session",
				"allowed_strata": ["S2"],
				"source_connections": ["OWNS", "LINK_NODES", "INBOUND"],
				"target_connections": ["OWNS", "LINK_NODES", "INBOUND"]
			},
			{
				"name": "PRGTask",
				"type_id": "prg_task",
				"allowed_strata": ["S1", "S2"],
				"source_connections": ["LINK_NODES", "INBOUND"],
				"target_connections": ["OWNS", "LINK_NODES", "INBOUND"]
			}
		],
		"morphisms": [
			{
				"name": "KeepNote",
				"type_id": "keep_note",
				"allowed_strata": ["S0", "S1"],
				"source_connections": ["LINK_NODES", "INBOUND"],
				"target_connections": ["OWNS", "LINK_NODES", "INBOUND"]
			},
			{
				"name": "LINK_NODES",
				"decomposition": "LINK(source, 'out', target, 'in')",
				"target": "structure.*"
			},
			{
				"name": "INBOUND",
				"decomposition": "LINK(source, 'in', target, 'in')",
				"target": "structure.*"
			},
			{
				"name": "OWNS",
				"decomposition": "LINK(owner, 'owns', target, 'child')",
				"target": "any"
			}
		]
	}`
	reg, err := operad.LoadRegistry([]byte(ontology))
	if err != nil {
		t.Fatalf("LoadRegistry: %v", err)
	}
	rt, err := shell.NewRuntime(store, reg)
	if err != nil {
		t.Fatalf("NewRuntime: %v", err)
	}
	return transport.NewServer(rt, "")
}

func TestPortInventoryFunctor_BySourceType(t *testing.T) {
	srv := newTestServerWithRegistry(t)
	w := doRequest(t, srv.Handler(), "GET", "/functor/port-inventory?src_type=agent_session", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var resp struct {
		SourceType string `json:"source_type"`
		PairCount  int    `json:"pair_count"`
		Pairs      []struct {
			SourceType string `json:"source_type"`
			SourcePort string `json:"source_port"`
			TargetType string `json:"target_type"`
			TargetPort string `json:"target_port"`
		} `json:"pairs"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if resp.SourceType != "agent_session" {
		t.Fatalf("source_type = %q, want %q", resp.SourceType, "agent_session")
	}
	if resp.PairCount == 0 || len(resp.Pairs) == 0 {
		t.Fatal("expected at least one port inventory pair")
	}
	matched := false
	for _, p := range resp.Pairs {
		if p.SourceType == "agent_session" && p.SourcePort == "out" && p.TargetType == "prg_task" && p.TargetPort == "in" {
			matched = true
			break
		}
	}
	if !matched {
		t.Fatalf("expected agent_session/out -> prg_task/in pair, got %+v", resp.Pairs)
	}
}

func TestPortInventoryFunctor_UnknownSourceType(t *testing.T) {
	srv := newTestServerWithRegistry(t)
	w := doRequest(t, srv.Handler(), "GET", "/functor/port-inventory?src_type=does_not_exist", nil)
	if w.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d: %s", w.Code, w.Body.String())
	}
}

func TestBindingCategoryFunctor_CollapsesOwnsFanOut(t *testing.T) {
	srv := newTestServerWithRegistry(t)
	w := doRequest(t, srv.Handler(), "GET", "/functor/binding-category?src_type=agent_session&source_port=owns", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var resp struct {
		SourceType  string `json:"source_type"`
		SourcePort  string `json:"source_port"`
		FamilyCount int    `json:"family_count"`
		Families    []struct {
			FamilyID        string   `json:"family_id"`
			SourcePort      string   `json:"source_port"`
			TargetPort      string   `json:"target_port"`
			TargetTypeCount int      `json:"target_type_count"`
			TargetTypes     []string `json:"target_types"`
			PairCount       int      `json:"pair_count"`
		} `json:"families"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if resp.SourceType != "agent_session" || resp.SourcePort != "owns" {
		t.Fatalf("unexpected source in response: %+v", resp)
	}
	if resp.FamilyCount != 1 || len(resp.Families) != 1 {
		t.Fatalf("expected exactly one family for owns fan-out, got %+v", resp.Families)
	}
	f := resp.Families[0]
	if f.FamilyID != "owns->child" || f.SourcePort != "owns" || f.TargetPort != "child" {
		t.Fatalf("unexpected family identity: %+v", f)
	}
	if f.TargetTypeCount < 2 {
		t.Fatalf("expected owns fan-out to multiple target types, got %+v", f)
	}
}

func TestBindingCategoryFunctor_UnknownSourceType(t *testing.T) {
	srv := newTestServerWithRegistry(t)
	w := doRequest(t, srv.Handler(), "GET", "/functor/binding-category?src_type=does_not_exist", nil)
	if w.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d: %s", w.Code, w.Body.String())
	}
}

func TestPortFunctor_CompositionPreserved(t *testing.T) {
	srv := newTestServerWithRegistry(t)
	w := doRequest(t, srv.Handler(), "GET", "/functor/port-functor?src_type=agent_session&source_port=out", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var resp struct {
		SourceType   string `json:"source_type"`
		SourcePort   string `json:"source_port"`
		MappingCount int    `json:"mapping_count"`
		Mappings     []struct {
			FromFamily     string `json:"from_family"`
			ToFamily       string `json:"to_family"`
			ComposedFamily string `json:"composed_family"`
			SourceType     string `json:"source_type"`
			SourcePort     string `json:"source_port"`
			ViaType        string `json:"via_type"`
			ViaPort        string `json:"via_port"`
			TargetType     string `json:"target_type"`
			TargetPort     string `json:"target_port"`
		} `json:"mappings"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if resp.SourceType != "agent_session" || resp.SourcePort != "out" {
		t.Fatalf("unexpected source in response: %+v", resp)
	}
	if resp.MappingCount == 0 || len(resp.Mappings) == 0 {
		t.Fatalf("expected at least one composed mapping, got %+v", resp)
	}
	found := false
	for _, m := range resp.Mappings {
		if m.SourceType == "agent_session" && m.SourcePort == "out" && m.ViaPort == "in" && m.ComposedFamily == "out->in" {
			found = true
			break
		}
	}
	if !found {
		t.Fatalf("expected composition-preserving out->in mapping, got %+v", resp.Mappings)
	}
}

func TestPortFunctor_UnknownSourceType(t *testing.T) {
	srv := newTestServerWithRegistry(t)
	w := doRequest(t, srv.Handler(), "GET", "/functor/port-functor?src_type=does_not_exist", nil)
	if w.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d: %s", w.Code, w.Body.String())
	}
}

func TestCalendarFunctorJSON(t *testing.T) {
	srv := newTestServer(t)

	// Add a prg_task node that should project into calendar entries.
	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: testActor,
		Add: &cat.AddPayload{
			URN:    "urn:test:prg:calendar",
			TypeID: "prg_task",
			Payload: map[string]any{
				"title":  "Calendar Test Task",
				"status": "in_progress",
			},
		},
	}
	doRequest(t, srv.Handler(), "POST", "/morphisms", env)

	w := doRequest(t, srv.Handler(), "GET", "/functor/calendar", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var resp struct {
		GeneratedAt string           `json:"generated_at"`
		Entries     []map[string]any `json:"entries"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if resp.GeneratedAt == "" {
		t.Fatal("generated_at must be present")
	}
	if len(resp.Entries) == 0 {
		t.Fatal("expected at least one calendar entry")
	}
}

func TestCalendarFunctorICal(t *testing.T) {
	srv := newTestServer(t)

	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: testActor,
		Add: &cat.AddPayload{
			URN:    "urn:test:calendar:event",
			TypeID: "calendar_event",
			Payload: map[string]any{
				"summary":    "ICal Test",
				"start_time": "2026-03-24T09:00:00Z",
				"end_time":   "2026-03-24T10:00:00Z",
			},
		},
	}
	doRequest(t, srv.Handler(), "POST", "/morphisms", env)

	w := doRequest(t, srv.Handler(), "GET", "/functor/calendar?format=ical", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	if ct := w.Header().Get("Content-Type"); !strings.HasPrefix(ct, "text/calendar") {
		t.Fatalf("expected text/calendar content type, got %q", ct)
	}
	body := w.Body.String()
	if !strings.Contains(body, "BEGIN:VCALENDAR") || !strings.Contains(body, "BEGIN:VEVENT") {
		t.Fatalf("invalid ical body:\n%s", body)
	}
}

func TestMaterialize(t *testing.T) {
	srv := newTestServer(t)
	req := hydration.MaterializeRequest{
		Actor: string(testActor),
		Nodes: []hydration.NodeRequest{
			{URN: "urn:mat-a", TypeID: "node_container"},
			{URN: "urn:mat-b", TypeID: "node_container"},
		},
		Wires: []hydration.WireRequest{
			{SourceURN: "urn:mat-a", SourcePort: "out", TargetURN: "urn:mat-b", TargetPort: "in"},
		},
	}
	w := doRequest(t, srv.Handler(), "POST", "/hydration/materialize", req)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
}

func TestMaterialize_DryRun(t *testing.T) {
	srv := newTestServer(t)
	req := hydration.MaterializeRequest{
		Actor: string(testActor),
		Nodes: []hydration.NodeRequest{
			{URN: "urn:dry", TypeID: "node_container"},
		},
	}
	w := doRequest(t, srv.Handler(), "POST", "/hydration/materialize?dry_run=true", req)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
}

func TestPostMorphism_InvalidJSON(t *testing.T) {
	srv := newTestServer(t)
	req := httptest.NewRequest("POST", "/morphisms", bytes.NewReader([]byte("not json")))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	if w.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestGetWires(t *testing.T) {
	srv := newTestServer(t)
	w := doRequest(t, srv.Handler(), "GET", "/state/wires", nil)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func TestGetScope(t *testing.T) {
	srv := newTestServer(t)
	// Build: actor -> OWNS -> child
	prog := cat.Program{
		Actor: testActor,
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:actor", TypeID: "node_container"}},
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:owned", TypeID: "node_container"}},
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:other", TypeID: "node_container"}},
			{Type: cat.LINK, Link: &cat.LinkPayload{SourceURN: "urn:actor", SourcePort: "OWNS", TargetURN: "urn:owned", TargetPort: "OWNS"}},
		},
	}
	doRequest(t, srv.Handler(), "POST", "/programs", prog)

	w := doRequest(t, srv.Handler(), "GET", "/state/scope/urn:actor", nil)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var state cat.GraphState
	json.Unmarshal(w.Body.Bytes(), &state)
	if len(state.Nodes) != 2 {
		t.Errorf("expected 2 nodes in scope, got %d", len(state.Nodes))
	}
	if _, ok := state.Nodes["urn:other"]; ok {
		t.Error("urn:other should not be in scoped subgraph")
	}
}

func TestGetScope_Empty(t *testing.T) {
	srv := newTestServer(t)
	w := doRequest(t, srv.Handler(), "GET", "/state/scope/urn:nonexistent", nil)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
	var state cat.GraphState
	json.Unmarshal(w.Body.Bytes(), &state)
	if len(state.Nodes) != 0 {
		t.Errorf("expected 0 nodes for missing actor, got %d", len(state.Nodes))
	}
}

func TestGetLens_KindFilter(t *testing.T) {
	srv := newTestServer(t)
	prog := cat.Program{Actor: testActor, Envelopes: []cat.Envelope{
		{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:provider:a", TypeID: "provider"}},
		{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:user:a", TypeID: "user"}},
	}}
	doRequest(t, srv.Handler(), "POST", "/programs", prog)

	w := doRequest(t, srv.Handler(), "GET", "/state/lens?kind=provider", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var state cat.GraphState
	json.Unmarshal(w.Body.Bytes(), &state)
	if len(state.Nodes) != 1 {
		t.Fatalf("expected 1 node, got %d", len(state.Nodes))
	}
	if _, ok := state.Nodes["urn:provider:a"]; !ok {
		t.Fatal("expected provider node in result")
	}
}

func TestGetLens_ComposeWithScope(t *testing.T) {
	srv := newTestServer(t)
	prog := cat.Program{Actor: testActor, Envelopes: []cat.Envelope{
		{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:actor", TypeID: "node_container"}},
		{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:provider:in", TypeID: "provider"}},
		{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:provider:out", TypeID: "provider"}},
		{Type: cat.LINK, Link: &cat.LinkPayload{SourceURN: "urn:actor", SourcePort: "OWNS", TargetURN: "urn:provider:in", TargetPort: "CHILD"}},
	}}
	doRequest(t, srv.Handler(), "POST", "/programs", prog)

	w := doRequest(t, srv.Handler(), "GET", "/state/lens?scope=urn:actor&kind=provider", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var state cat.GraphState
	json.Unmarshal(w.Body.Bytes(), &state)
	if len(state.Nodes) != 1 {
		t.Fatalf("expected 1 scoped provider node, got %d", len(state.Nodes))
	}
	if _, ok := state.Nodes["urn:provider:in"]; !ok {
		t.Fatal("expected scoped provider in result")
	}
	if _, ok := state.Nodes["urn:provider:out"]; ok {
		t.Fatal("unexpected out-of-scope provider in result")
	}
}

func TestPostLens_Union(t *testing.T) {
	srv := newTestServer(t)
	prog := cat.Program{Actor: testActor, Envelopes: []cat.Envelope{
		{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:provider:a", TypeID: "provider"}},
		{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:user:a", TypeID: "user"}},
		{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:tool:a", TypeID: "system_tool"}},
	}}
	doRequest(t, srv.Handler(), "POST", "/programs", prog)

	body := map[string]any{
		"mode": "union",
		"rules": []map[string]any{
			{"kind": []string{"provider"}},
			{"kind": []string{"user"}},
		},
	}
	w := doRequest(t, srv.Handler(), "POST", "/state/lens", body)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var state cat.GraphState
	json.Unmarshal(w.Body.Bytes(), &state)
	if len(state.Nodes) != 2 {
		t.Fatalf("expected 2 nodes, got %d", len(state.Nodes))
	}
}

func TestPostLens_InvalidJSON(t *testing.T) {
	srv := newTestServer(t)
	req := httptest.NewRequest("POST", "/state/lens", bytes.NewReader([]byte("not json")))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	srv.Handler().ServeHTTP(w, req)
	if w.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestUIFunctor_IncludesS0IndustryNodes(t *testing.T) {
	srv := newTestServer(t)

	prog := cat.Program{Actor: testActor, Envelopes: []cat.Envelope{
		{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:moos:industry:providers:ind-provider-anthropic", TypeID: "industry_entity", Stratum: cat.S0}},
	}}
	doRequest(t, srv.Handler(), "POST", "/programs", prog)

	w := doRequest(t, srv.Handler(), "GET", "/functor/ui", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var payload map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &payload); err != nil {
		t.Fatalf("decode ui payload: %v", err)
	}

	nodesRaw, ok := payload["nodes"].([]any)
	if !ok {
		t.Fatalf("nodes field missing or invalid: %T", payload["nodes"])
	}

	found := false
	for _, raw := range nodesRaw {
		node, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		if node["kind"] == "industry_entity" && node["stratum"] == "S0" {
			found = true
			break
		}
	}
	if !found {
		t.Fatal("expected S0 industry_entity node in /functor/ui output")
	}
}
