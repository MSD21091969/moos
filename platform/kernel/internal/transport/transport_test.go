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
	return transport.NewServer(rt, rt, "")
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

func TestBridgeDiff_CursorAdvances(t *testing.T) {
	srv := newTestServer(t)

	// Seed required kernel node.
	doRequest(t, srv.Handler(), "POST", "/morphisms", cat.Envelope{
		Type: cat.ADD, Actor: testActor,
		Add: &cat.AddPayload{URN: "urn:moos:kernel:test", TypeID: "kernel_instance"},
	})
	// Add one additional envelope that should appear in diff.
	doRequest(t, srv.Handler(), "POST", "/morphisms", cat.Envelope{
		Type: cat.ADD, Actor: testActor,
		Add: &cat.AddPayload{URN: "urn:bridge-diff:test-node", TypeID: "node_container"},
	})

	first := doRequest(t, srv.Handler(), "GET", "/bridge/urn:moos:kernel:test", nil)
	if first.Code != http.StatusOK {
		t.Fatalf("expected first bridge diff 200, got %d: %s", first.Code, first.Body.String())
	}
	var firstResp map[string]any
	if err := json.Unmarshal(first.Body.Bytes(), &firstResp); err != nil {
		t.Fatalf("decode first bridge diff: %v", err)
	}
	countVal, ok := firstResp["count"].(float64)
	if !ok {
		t.Fatalf("bridge diff count missing or invalid: %#v", firstResp["count"])
	}
	if int(countVal) == 0 {
		t.Fatalf("expected non-empty bridge diff on first request")
	}

	second := doRequest(t, srv.Handler(), "GET", "/bridge/urn:moos:kernel:test", nil)
	if second.Code != http.StatusOK {
		t.Fatalf("expected second bridge diff 200, got %d: %s", second.Code, second.Body.String())
	}
	var secondResp map[string]any
	if err := json.Unmarshal(second.Body.Bytes(), &secondResp); err != nil {
		t.Fatalf("decode second bridge diff: %v", err)
	}
	secondCount, ok := secondResp["count"].(float64)
	if !ok {
		t.Fatalf("second bridge diff count missing or invalid: %#v", secondResp["count"])
	}
	if int(secondCount) != 0 {
		t.Fatalf("expected empty bridge diff after cursor advance, got %d", int(secondCount))
	}
}

func TestBridgeSync_AppliesEnvelopes(t *testing.T) {
	srv := newTestServer(t)

	body := map[string]any{
		"source_kernel_urn": "urn:moos:kernel:remote",
		"target_kernel_urn": "urn:moos:kernel:local",
		"envelopes": []map[string]any{
			{
				"type":  "ADD",
				"actor": string(testActor),
				"add": map[string]any{
					"urn":     "urn:bridge-sync:test-node",
					"type_id": "node_container",
				},
			},
		},
	}

	w := doRequest(t, srv.Handler(), "POST", "/bridge/sync", body)
	if w.Code != http.StatusOK {
		t.Fatalf("expected bridge sync 200, got %d: %s", w.Code, w.Body.String())
	}

	lookup := doRequest(t, srv.Handler(), "GET", "/state/nodes/urn:bridge-sync:test-node", nil)
	if lookup.Code != http.StatusOK {
		t.Fatalf("expected synced node to exist, got %d: %s", lookup.Code, lookup.Body.String())
	}
}

func TestBridgeFiber_DepthAndBoundary(t *testing.T) {
	srv := newTestServer(t)

	for _, env := range []cat.Envelope{
		{Type: cat.ADD, Actor: testActor, Add: &cat.AddPayload{URN: "urn:moos:kernel:test-fiber", TypeID: "kernel_instance"}},
		{Type: cat.ADD, Actor: testActor, Add: &cat.AddPayload{URN: "urn:moos:fiber:root", TypeID: "node_container"}},
		{Type: cat.ADD, Actor: testActor, Add: &cat.AddPayload{URN: "urn:moos:fiber:neighbor", TypeID: "node_container"}},
		{Type: cat.ADD, Actor: testActor, Add: &cat.AddPayload{URN: "urn:moos:fiber:outside", TypeID: "node_container"}},
		{Type: cat.LINK, Actor: testActor, Link: &cat.LinkPayload{SourceURN: "urn:moos:fiber:root", SourcePort: "out", TargetURN: "urn:moos:fiber:neighbor", TargetPort: "in"}},
		{Type: cat.LINK, Actor: testActor, Link: &cat.LinkPayload{SourceURN: "urn:moos:fiber:neighbor", SourcePort: "out", TargetURN: "urn:moos:fiber:outside", TargetPort: "in"}},
	} {
		w := doRequest(t, srv.Handler(), "POST", "/morphisms", env)
		if w.Code != http.StatusOK {
			t.Fatalf("seed morphism failed: %d %s", w.Code, w.Body.String())
		}
	}

	w := doRequest(t, srv.Handler(), "GET", "/bridge/urn:moos:kernel:test-fiber/fiber?root=urn:moos:fiber:root&depth=1", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var resp struct {
		Completeness float64 `json:"completeness"`
		Nodes        []struct {
			URN cat.URN `json:"urn"`
		} `json:"nodes"`
		Wires []struct {
			SourceURN cat.URN `json:"source_urn"`
			TargetURN cat.URN `json:"target_urn"`
		} `json:"wires"`
		InterfacePorts []struct {
			URN       cat.URN  `json:"urn"`
			Port      cat.Port `json:"port"`
			Direction string   `json:"direction"`
		} `json:"interface_ports"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("decode fiber response: %v", err)
	}
	if resp.Completeness != 1.0 {
		t.Fatalf("completeness = %v, want 1.0", resp.Completeness)
	}

	nodeSet := map[cat.URN]bool{}
	for _, n := range resp.Nodes {
		nodeSet[n.URN] = true
	}
	if !nodeSet["urn:moos:fiber:root"] || !nodeSet["urn:moos:fiber:neighbor"] {
		t.Fatalf("fiber missing expected nodes: %+v", resp.Nodes)
	}
	if nodeSet["urn:moos:fiber:outside"] {
		t.Fatalf("fiber should not include outside node at depth=1")
	}

	if len(resp.Wires) != 1 {
		t.Fatalf("expected 1 in-fiber wire, got %d", len(resp.Wires))
	}

	foundBoundary := false
	for _, p := range resp.InterfacePorts {
		if p.URN == "urn:moos:fiber:neighbor" && p.Port == "out" && p.Direction == "out" {
			foundBoundary = true
			break
		}
	}
	if !foundBoundary {
		t.Fatalf("expected neighbor/out boundary interface port, got %+v", resp.InterfacePorts)
	}
}

func TestCalendarSync_PRGLinkAndKeepNote(t *testing.T) {
	srv := newTestServer(t)

	seedPRG := doRequest(t, srv.Handler(), "POST", "/morphisms", cat.Envelope{
		Type:  cat.ADD,
		Actor: testActor,
		Add:   &cat.AddPayload{URN: "urn:moos:prg:036", TypeID: "prg_task"},
	})
	if seedPRG.Code != http.StatusOK {
		t.Fatalf("seed PRG node failed: %d %s", seedPRG.Code, seedPRG.Body.String())
	}

	prgBody := map[string]any{
		"id":          "evt-prg-1",
		"summary":     "Planning sync",
		"start_time":  "2026-03-26T11:00:00Z",
		"end_time":    "2026-03-26T11:30:00Z",
		"description": "Team check-in for PRG036 bridge work",
		"source_type": "gcal",
	}
	prgResp := doRequest(t, srv.Handler(), "POST", "/callback/calendar/sync", prgBody)
	if prgResp.Code != http.StatusAccepted {
		t.Fatalf("expected 202 for PRG event, got %d: %s", prgResp.Code, prgResp.Body.String())
	}

	eventLookup := doRequest(t, srv.Handler(), "GET", "/state/nodes/urn:moos:calendar_event:evt-prg-1", nil)
	if eventLookup.Code != http.StatusOK {
		t.Fatalf("expected calendar_event node, got %d: %s", eventLookup.Code, eventLookup.Body.String())
	}

	wiresResp := doRequest(t, srv.Handler(), "GET", "/state/wires", nil)
	if wiresResp.Code != http.StatusOK {
		t.Fatalf("state/wires failed: %d", wiresResp.Code)
	}
	var wires map[string]cat.Wire
	if err := json.Unmarshal(wiresResp.Body.Bytes(), &wires); err != nil {
		t.Fatalf("decode wires: %v", err)
	}
	key := cat.WireKey("urn:moos:calendar_event:evt-prg-1", "out", "urn:moos:prg:036", "in")
	if _, ok := wires[key]; !ok {
		t.Fatalf("expected PRG link wire %s", key)
	}

	noteBody := map[string]any{
		"id":          "evt-note-1",
		"summary":     "General note",
		"start_time":  "2026-03-26T12:00:00Z",
		"end_time":    "2026-03-26T12:30:00Z",
		"description": "No PRG tag in this note",
		"source_type": "gcal",
	}
	noteResp := doRequest(t, srv.Handler(), "POST", "/callback/calendar/sync", noteBody)
	if noteResp.Code != http.StatusAccepted {
		t.Fatalf("expected 202 for note event, got %d: %s", noteResp.Code, noteResp.Body.String())
	}

	noteLookup := doRequest(t, srv.Handler(), "GET", "/state/nodes/urn:moos:keep_note:evt-note-1", nil)
	if noteLookup.Code != http.StatusOK {
		t.Fatalf("expected keep_note node, got %d: %s", noteLookup.Code, noteLookup.Body.String())
	}
	var noteNode cat.Node
	if err := json.Unmarshal(noteLookup.Body.Bytes(), &noteNode); err != nil {
		t.Fatalf("decode keep_note node: %v", err)
	}
	if noteNode.Stratum != cat.S0 {
		t.Fatalf("keep_note stratum = %s, want %s", noteNode.Stratum, cat.S0)
	}
}

func TestPipelineMetricsFunctor(t *testing.T) {
	srv := newTestServer(t)

	for _, env := range []cat.Envelope{
		{Type: cat.ADD, Actor: testActor, Add: &cat.AddPayload{URN: "urn:moos:kernel:test-metrics", TypeID: "kernel_instance"}},
		{Type: cat.ADD, Actor: testActor, Add: &cat.AddPayload{URN: "urn:moos:node:metrics-a", TypeID: "node_container"}},
		{Type: cat.LINK, Actor: testActor, Link: &cat.LinkPayload{SourceURN: "urn:moos:kernel:test-metrics", SourcePort: "out", TargetURN: "urn:moos:node:metrics-a", TargetPort: "in"}},
		{Type: cat.LINK, Actor: testActor, Link: &cat.LinkPayload{SourceURN: "urn:moos:node:metrics-a", SourcePort: "out", TargetURN: "urn:moos:kernel:test-metrics", TargetPort: "in"}},
	} {
		w := doRequest(t, srv.Handler(), "POST", "/morphisms", env)
		if w.Code != http.StatusOK {
			t.Fatalf("seed morphism failed: %d %s", w.Code, w.Body.String())
		}
	}

	w := doRequest(t, srv.Handler(), "GET", "/functor/pipeline-metrics?kernel_urn=urn:moos:kernel:test-metrics", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var resp struct {
		KernelCount     int     `json:"kernel_count"`
		AvgCurvature    float64 `json:"avg_curvature"`
		AvgCompleteness float64 `json:"avg_completeness"`
		ByKernel        []struct {
			KernelURN    cat.URN `json:"kernel_urn"`
			Incoming     int     `json:"incoming"`
			Outgoing     int     `json:"outgoing"`
			Completeness float64 `json:"completeness"`
			Curvature    float64 `json:"curvature"`
		} `json:"by_kernel"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("decode pipeline metrics: %v", err)
	}
	if resp.KernelCount != 1 || len(resp.ByKernel) != 1 {
		t.Fatalf("expected one kernel metric, got %+v", resp)
	}
	km := resp.ByKernel[0]
	if km.KernelURN != "urn:moos:kernel:test-metrics" {
		t.Fatalf("unexpected kernel urn: %s", km.KernelURN)
	}
	if km.Incoming != 1 || km.Outgoing != 1 {
		t.Fatalf("unexpected in/out counts: %+v", km)
	}
	if km.Completeness <= 0 || km.Completeness > 1 {
		t.Fatalf("unexpected completeness: %v", km.Completeness)
	}
}

func TestPipelineMetricsFunctor_UnknownKernel(t *testing.T) {
	srv := newTestServer(t)
	w := doRequest(t, srv.Handler(), "GET", "/functor/pipeline-metrics?kernel_urn=urn:moos:kernel:missing", nil)
	if w.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d: %s", w.Code, w.Body.String())
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
	return transport.NewServer(rt, rt, "")
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
