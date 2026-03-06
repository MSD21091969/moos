package main

import (
	"bufio"
	"context"
	"database/sql"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/collider/moos/internal/container"
	"github.com/collider/moos/internal/tool"
)

type fakeStore struct {
	records map[string]container.Record
	wires   map[string]container.WireRecord
	logs    []container.MorphismLogRecord
}

func wireKey(wire container.WireRecord) string {
	return wire.FromContainerURN + "|" + wire.FromPort + "|" + wire.ToContainerURN + "|" + wire.ToPort
}

func (store *fakeStore) Health(ctx context.Context) error {
	return nil
}

func (store *fakeStore) GetByURN(ctx context.Context, urn string) (*container.Record, error) {
	record, ok := store.records[urn]
	if !ok {
		return nil, container.ErrNotFound
	}
	copyRecord := record
	return &copyRecord, nil
}

func (store *fakeStore) Create(ctx context.Context, record container.Record) error {
	store.records[record.URN] = record
	return nil
}

func (store *fakeStore) ListChildren(ctx context.Context, parentURN string) ([]container.Record, error) {
	result := make([]container.Record, 0)
	for _, record := range store.records {
		if record.ParentURN.Valid && record.ParentURN.String == parentURN {
			result = append(result, record)
		}
	}
	return result, nil
}

func (store *fakeStore) TreeTraversal(ctx context.Context, rootURN string) ([]container.Record, error) {
	root, ok := store.records[rootURN]
	if !ok {
		return nil, container.ErrNotFound
	}
	result := []container.Record{root}
	for _, record := range store.records {
		if record.ParentURN.Valid && record.ParentURN.String == rootURN {
			result = append(result, record)
		}
	}
	return result, nil
}

func (store *fakeStore) MutateKernel(ctx context.Context, urn string, expectedVersion int64, kernelJSON json.RawMessage) (int64, error) {
	record, ok := store.records[urn]
	if !ok {
		return 0, container.ErrNotFound
	}
	if record.Version != expectedVersion {
		return record.Version, container.ErrVersionConflict
	}
	record.KernelJSON = kernelJSON
	record.Version = record.Version + 1
	store.records[urn] = record
	return record.Version, nil
}

func (store *fakeStore) Link(ctx context.Context, wire container.WireRecord) error {
	if _, ok := store.records[wire.FromContainerURN]; !ok {
		return container.ErrNotFound
	}
	if _, ok := store.records[wire.ToContainerURN]; !ok {
		return container.ErrNotFound
	}
	if _, exists := store.wires[wireKey(wire)]; exists {
		return container.ErrAlreadyExists
	}
	store.wires[wireKey(wire)] = wire
	return nil
}

func (store *fakeStore) Unlink(ctx context.Context, wire container.WireRecord) error {
	key := wireKey(wire)
	if _, exists := store.wires[key]; !exists {
		return container.ErrNotFound
	}
	delete(store.wires, key)
	return nil
}

func (store *fakeStore) AppendMorphismLog(ctx context.Context, record container.MorphismLogRecord) error {
	store.logs = append(store.logs, record)
	return nil
}

func (store *fakeStore) ListMorphismLog(ctx context.Context, query container.MorphismLogQuery) ([]container.MorphismLogEntry, error) {
	result := make([]container.MorphismLogEntry, 0, len(store.logs))
	for index, logRecord := range store.logs {
		if query.ScopeURN != "" && logRecord.ScopeURN != query.ScopeURN {
			continue
		}
		if query.Type != "" && logRecord.Type != query.Type {
			continue
		}
		expectedID := "test-log-" + string(rune('a'+index))
		entry := container.MorphismLogEntry{
			ID:              expectedID,
			Type:            logRecord.Type,
			ActorURN:        logRecord.ActorURN,
			ScopeURN:        logRecord.ScopeURN,
			ExpectedVersion: logRecord.ExpectedVersion,
			PayloadJSON:     logRecord.PayloadJSON,
			MetadataJSON:    logRecord.MetadataJSON,
			IssuedAt:        logRecord.IssuedAt,
			CommittedAt:     logRecord.IssuedAt.Add(10 * time.Millisecond),
		}
		result = append(result, entry)
	}
	if query.Limit > 0 && len(result) > query.Limit {
		result = result[:query.Limit]
	}
	return result, nil
}

func TestCreateContainerHandler(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}}
	mux := newMux(store)

	body := `{"URN":"urn:moos:test:1","Kind":"data"}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1/containers", strings.NewReader(body))
	rr := httptest.NewRecorder()

	mux.ServeHTTP(rr, req)
	if rr.Code != http.StatusCreated {
		t.Fatalf("expected %d, got %d", http.StatusCreated, rr.Code)
	}
	if _, ok := store.records["urn:moos:test:1"]; !ok {
		t.Fatalf("expected record to be created in store")
	}
	if len(store.logs) != 1 || store.logs[0].Type != "ADD" {
		t.Fatalf("expected one ADD morphism log entry")
	}
}

func TestMetricsHandler(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}}
	mux := newMux(store)

	req := httptest.NewRequest(http.MethodGet, "/metrics", nil)
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d", http.StatusOK, rr.Code)
	}
	if !strings.Contains(rr.Body.String(), "go_gc_duration_seconds") {
		t.Fatalf("expected prometheus metrics payload")
	}
}

func TestListChildrenHandler(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:parent:1": {URN: "urn:moos:parent:1", Kind: "composite"},
		"urn:moos:child:1": {
			URN:       "urn:moos:child:1",
			Kind:      "data",
			ParentURN: sql.NullString{String: "urn:moos:parent:1", Valid: true},
		},
	}, wires: map[string]container.WireRecord{}}
	mux := newMux(store)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/containers/urn:moos:parent:1/children", nil)
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d", http.StatusOK, rr.Code)
	}
	var children []container.Record
	if err := json.Unmarshal(rr.Body.Bytes(), &children); err != nil {
		t.Fatalf("failed to decode json: %v", err)
	}
	if len(children) != 1 {
		t.Fatalf("expected 1 child, got %d", len(children))
	}
}

func TestTreeTraversalHandler(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:tree:root": {URN: "urn:moos:tree:root", Kind: "composite"},
		"urn:moos:tree:child": {
			URN:       "urn:moos:tree:child",
			Kind:      "data",
			ParentURN: sql.NullString{String: "urn:moos:tree:root", Valid: true},
		},
	}, wires: map[string]container.WireRecord{}}
	mux := newMux(store)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/containers/urn:moos:tree:root/tree", nil)
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d", http.StatusOK, rr.Code)
	}
	if rr.Header().Get("X-Tree-Count") != "2" {
		t.Fatalf("expected X-Tree-Count=2, got %s", rr.Header().Get("X-Tree-Count"))
	}
	var tree []container.Record
	if err := json.Unmarshal(rr.Body.Bytes(), &tree); err != nil {
		t.Fatalf("failed to decode json: %v", err)
	}
	if len(tree) != 2 {
		t.Fatalf("expected 2 records in tree, got %d", len(tree))
	}
}

func TestPatchContainerMutateSuccess(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:item:1": {URN: "urn:moos:item:1", Kind: "data", Version: 1},
	}, wires: map[string]container.WireRecord{}}
	mux := newMux(store)

	body := `{"expected_version":1,"kernel_json":{"status":"updated"}}`
	req := httptest.NewRequest(http.MethodPatch, "/api/v1/containers/urn:moos:item:1", strings.NewReader(body))
	rr := httptest.NewRecorder()

	mux.ServeHTTP(rr, req)
	if rr.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d", http.StatusOK, rr.Code)
	}
	record := store.records["urn:moos:item:1"]
	if record.Version != 2 {
		t.Fatalf("expected version 2 after mutate, got %d", record.Version)
	}
	if len(store.logs) != 1 || store.logs[0].Type != "MUTATE" {
		t.Fatalf("expected one MUTATE morphism log entry")
	}
}

func TestPatchContainerMutateConflict(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:item:2": {URN: "urn:moos:item:2", Kind: "data", Version: 3},
	}, wires: map[string]container.WireRecord{}}
	mux := newMux(store)

	body := `{"expected_version":1,"kernel_json":{"status":"stale"}}`
	req := httptest.NewRequest(http.MethodPatch, "/api/v1/containers/urn:moos:item:2", strings.NewReader(body))
	rr := httptest.NewRecorder()

	mux.ServeHTTP(rr, req)
	if rr.Code != http.StatusConflict {
		t.Fatalf("expected %d, got %d", http.StatusConflict, rr.Code)
	}
	if rr.Header().Get("X-Current-Version") != "3" {
		t.Fatalf("expected X-Current-Version=3, got %s", rr.Header().Get("X-Current-Version"))
	}
	if len(store.logs) != 0 {
		t.Fatalf("expected no morphism logs on mutate conflict")
	}
}

func TestPostWireHandler(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:from:1": {URN: "urn:moos:from:1", Kind: "composite", Version: 1},
		"urn:moos:to:1":   {URN: "urn:moos:to:1", Kind: "data", Version: 1},
	}, wires: map[string]container.WireRecord{}}
	mux := newMux(store)

	body := `{"from_port":"out","to_urn":"urn:moos:to:1","to_port":"in"}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1/containers/urn:moos:from:1/wires", strings.NewReader(body))
	rr := httptest.NewRecorder()

	mux.ServeHTTP(rr, req)
	if rr.Code != http.StatusCreated {
		t.Fatalf("expected %d, got %d", http.StatusCreated, rr.Code)
	}
	if len(store.wires) != 1 {
		t.Fatalf("expected 1 wire, got %d", len(store.wires))
	}
	if len(store.logs) != 1 || store.logs[0].Type != "LINK" {
		t.Fatalf("expected one LINK morphism log entry")
	}
}

func TestDeleteWireHandler(t *testing.T) {
	initialWire := container.WireRecord{FromContainerURN: "urn:moos:from:1", FromPort: "out", ToContainerURN: "urn:moos:to:1", ToPort: "in"}
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:from:1": {URN: "urn:moos:from:1", Kind: "composite", Version: 1},
		"urn:moos:to:1":   {URN: "urn:moos:to:1", Kind: "data", Version: 1},
	}, wires: map[string]container.WireRecord{wireKey(initialWire): initialWire}}
	mux := newMux(store)

	body := `{"from_port":"out","to_urn":"urn:moos:to:1","to_port":"in"}`
	req := httptest.NewRequest(http.MethodDelete, "/api/v1/containers/urn:moos:from:1/wires", strings.NewReader(body))
	rr := httptest.NewRecorder()

	mux.ServeHTTP(rr, req)
	if rr.Code != http.StatusNoContent {
		t.Fatalf("expected %d, got %d", http.StatusNoContent, rr.Code)
	}
	if len(store.wires) != 0 {
		t.Fatalf("expected 0 wires, got %d", len(store.wires))
	}
	if len(store.logs) != 1 || store.logs[0].Type != "UNLINK" {
		t.Fatalf("expected one UNLINK morphism log entry")
	}
}

func TestGetMorphismLogHandler(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}, logs: []container.MorphismLogRecord{
		{Type: "ADD", ActorURN: "urn:moos:actor:system", ScopeURN: "urn:moos:item:1", IssuedAt: time.Now().UTC()},
		{Type: "MUTATE", ActorURN: "urn:moos:actor:system", ScopeURN: "urn:moos:item:1", IssuedAt: time.Now().UTC()},
	}}
	mux := newMux(store)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/morphisms/log?scope_urn=urn:moos:item:1&type=MUTATE&limit=10", nil)
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d", http.StatusOK, rr.Code)
	}
	if rr.Header().Get("X-Log-Count") != "1" {
		t.Fatalf("expected X-Log-Count=1, got %s", rr.Header().Get("X-Log-Count"))
	}
	var entries []container.MorphismLogEntry
	if err := json.Unmarshal(rr.Body.Bytes(), &entries); err != nil {
		t.Fatalf("failed to decode json: %v", err)
	}
	if len(entries) != 1 || entries[0].Type != "MUTATE" {
		t.Fatalf("expected one MUTATE entry")
	}
}

func TestPostMorphismAddHandler(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}}
	mux := newMux(store)

	body := `{"type":"ADD","add":{"container":{"URN":"urn:moos:morphism:add:1","Kind":"data"}}}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1/morphisms", strings.NewReader(body))
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)

	if rr.Code != http.StatusAccepted {
		t.Fatalf("expected %d, got %d", http.StatusAccepted, rr.Code)
	}
	if _, ok := store.records["urn:moos:morphism:add:1"]; !ok {
		t.Fatalf("expected record to be created")
	}
	if len(store.logs) != 1 || store.logs[0].Type != "ADD" {
		t.Fatalf("expected one ADD log entry")
	}
}

func TestPostMorphismMutateConflict(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:morphism:item": {URN: "urn:moos:morphism:item", Kind: "data", Version: 4},
	}, wires: map[string]container.WireRecord{}}
	mux := newMux(store)

	body := `{"type":"MUTATE","mutate":{"urn":"urn:moos:morphism:item","expected_version":1,"kernel_json":{"state":"stale"}}}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1/morphisms", strings.NewReader(body))
	rr := httptest.NewRecorder()
	mux.ServeHTTP(rr, req)

	if rr.Code != http.StatusConflict {
		t.Fatalf("expected %d, got %d", http.StatusConflict, rr.Code)
	}
	if rr.Header().Get("X-Current-Version") != "4" {
		t.Fatalf("expected X-Current-Version=4, got %s", rr.Header().Get("X-Current-Version"))
	}
	if len(store.logs) != 0 {
		t.Fatalf("expected no log entry on conflict")
	}
}

func TestBearerAuthEnforcedWhenConfigured(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}}
	mux := newMuxWithAuth(store, "secret-token")

	unauthorizedReq := httptest.NewRequest(http.MethodGet, "/api/v1/morphisms/log", nil)
	unauthorizedRR := httptest.NewRecorder()
	mux.ServeHTTP(unauthorizedRR, unauthorizedReq)
	if unauthorizedRR.Code != http.StatusUnauthorized {
		t.Fatalf("expected %d, got %d", http.StatusUnauthorized, unauthorizedRR.Code)
	}

	authorizedReq := httptest.NewRequest(http.MethodGet, "/api/v1/morphisms/log", nil)
	authorizedReq.Header.Set("Authorization", "Bearer secret-token")
	authorizedRR := httptest.NewRecorder()
	mux.ServeHTTP(authorizedRR, authorizedReq)
	if authorizedRR.Code != http.StatusOK {
		t.Fatalf("expected %d, got %d", http.StatusOK, authorizedRR.Code)
	}
}

func TestMCPSSEAnnouncesSessionEndpoint(t *testing.T) {
	mux := http.NewServeMux()
	bridge := tool.NewMCPBridge(tool.NewRegistry(), tool.DefaultPolicy())
	attachMCPRoutes(mux, bridge, newMCPSessionBroker(), "")
	server := httptest.NewServer(mux)
	defer server.Close()

	response, err := http.Get(server.URL + "/mcp/sse")
	if err != nil {
		t.Fatalf("failed to open mcp sse: %v", err)
	}
	defer response.Body.Close()

	if response.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", response.StatusCode)
	}

	reader := bufio.NewReader(response.Body)
	event, data, readErr := readSSEEvent(reader, 2*time.Second)
	if readErr != nil {
		t.Fatalf("failed reading endpoint event: %v", readErr)
	}
	if event != "endpoint" {
		t.Fatalf("expected endpoint event, got %s", event)
	}
	if !strings.Contains(data, "sessionId") || !strings.Contains(data, "/mcp/messages?sessionId=") {
		t.Fatalf("expected endpoint payload with correlated session id, got %s", data)
	}
}

func TestMCPMessagesPublishToCorrelatedSSESession(t *testing.T) {
	mux := http.NewServeMux()
	bridge := tool.NewMCPBridge(tool.NewRegistry(), tool.DefaultPolicy())
	attachMCPRoutes(mux, bridge, newMCPSessionBroker(), "")
	server := httptest.NewServer(mux)
	defer server.Close()

	sessionID := "mcp-test-session"
	request, _ := http.NewRequest(http.MethodGet, server.URL+"/mcp/sse?sessionId="+sessionID, nil)
	response, err := http.DefaultClient.Do(request)
	if err != nil {
		t.Fatalf("failed to connect sse: %v", err)
	}
	defer response.Body.Close()

	reader := bufio.NewReader(response.Body)
	_, _, _ = readSSEEvent(reader, 2*time.Second)

	body := strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}`)
	postResponse, postErr := http.Post(server.URL+"/mcp/messages?sessionId="+sessionID, "application/json", body)
	if postErr != nil {
		t.Fatalf("failed posting mcp message: %v", postErr)
	}
	defer postResponse.Body.Close()

	if postResponse.StatusCode != http.StatusOK {
		t.Fatalf("expected 200 from mcp/messages, got %d", postResponse.StatusCode)
	}

	seenResponseEvent := false
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		event, data, err := readSSEEvent(reader, time.Until(deadline))
		if err != nil {
			t.Fatalf("failed to read correlated sse event: %v", err)
		}
		if event == "response" && strings.Contains(data, `"method":"tools/list"`) {
			seenResponseEvent = true
			break
		}
	}

	if !seenResponseEvent {
		t.Fatalf("expected correlated response event for tools/list")
	}
}

func TestMCPToolsCallCanBeCancelled(t *testing.T) {
	registry := tool.NewRegistry()
	_ = registry.Register(tool.Definition{Name: "slow_tool", Description: "sleeps or cancels"}, func(ctx context.Context, arguments map[string]any) (map[string]any, error) {
		_ = arguments
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(3 * time.Second):
			return map[string]any{"ok": true}, nil
		}
	})

	mux := http.NewServeMux()
	bridge := tool.NewMCPBridge(registry, tool.DefaultPolicy())
	attachMCPRoutes(mux, bridge, newMCPSessionBroker(), "")
	server := httptest.NewServer(mux)
	defer server.Close()

	sessionID := "mcp-cancel-test"
	sseRequest, _ := http.NewRequest(http.MethodGet, server.URL+"/mcp/sse?sessionId="+sessionID, nil)
	sseResponse, err := http.DefaultClient.Do(sseRequest)
	if err != nil {
		t.Fatalf("failed to connect sse: %v", err)
	}
	defer sseResponse.Body.Close()
	reader := bufio.NewReader(sseResponse.Body)
	_, _, _ = readSSEEvent(reader, 2*time.Second)

	var wg sync.WaitGroup
	wg.Add(1)

	callResultCh := make(chan string, 1)
	go func() {
		defer wg.Done()
		body := strings.NewReader(`{"jsonrpc":"2.0","id":42,"method":"tools/call","params":{"name":"slow_tool","arguments":{}}}`)
		response, postErr := http.Post(server.URL+"/mcp/messages?sessionId="+sessionID, "application/json", body)
		if postErr != nil {
			callResultCh <- postErr.Error()
			return
		}
		defer response.Body.Close()
		payload, _ := io.ReadAll(response.Body)
		callResultCh <- string(payload)
	}()

	time.Sleep(200 * time.Millisecond)
	cancelBody := strings.NewReader(`{"jsonrpc":"2.0","id":99,"method":"$/cancelRequest","params":{"id":42}}`)
	cancelResponse, cancelErr := http.Post(server.URL+"/mcp/messages?sessionId="+sessionID, "application/json", cancelBody)
	if cancelErr != nil {
		t.Fatalf("failed posting cancel request: %v", cancelErr)
	}
	defer cancelResponse.Body.Close()
	if cancelResponse.StatusCode != http.StatusOK {
		t.Fatalf("expected cancel status 200, got %d", cancelResponse.StatusCode)
	}

	var cancelPayload map[string]any
	if err := json.NewDecoder(cancelResponse.Body).Decode(&cancelPayload); err != nil {
		t.Fatalf("failed decoding cancel response: %v", err)
	}
	result, _ := cancelPayload["result"].(map[string]any)
	if result == nil || result["cancelled"] != true {
		t.Fatalf("expected cancelled=true in cancel response")
	}

	wg.Wait()
	callResult := <-callResultCh
	if !strings.Contains(callResult, "context canceled") {
		t.Fatalf("expected tools/call to be canceled, got: %s", callResult)
	}
}

func TestMCPPingAndInitialized(t *testing.T) {
	mux := http.NewServeMux()
	bridge := tool.NewMCPBridge(tool.NewRegistry(), tool.DefaultPolicy())
	attachMCPRoutes(mux, bridge, newMCPSessionBroker(), "")
	server := httptest.NewServer(mux)
	defer server.Close()

	sessionID := "mcp-proto-test"
	pingBody := strings.NewReader(`{"jsonrpc":"2.0","id":7,"method":"ping","params":{}}`)
	pingResponse, pingErr := http.Post(server.URL+"/mcp/messages?sessionId="+sessionID, "application/json", pingBody)
	if pingErr != nil {
		t.Fatalf("failed posting ping: %v", pingErr)
	}
	defer pingResponse.Body.Close()
	if pingResponse.StatusCode != http.StatusOK {
		t.Fatalf("expected ping status 200, got %d", pingResponse.StatusCode)
	}
	var pingPayload map[string]any
	if err := json.NewDecoder(pingResponse.Body).Decode(&pingPayload); err != nil {
		t.Fatalf("failed decoding ping response: %v", err)
	}
	result, _ := pingPayload["result"].(map[string]any)
	if result == nil || result["pong"] != true {
		t.Fatalf("expected pong=true")
	}

	initBody := strings.NewReader(`{"jsonrpc":"2.0","id":8,"method":"notifications/initialized","params":{}}`)
	initResponse, initErr := http.Post(server.URL+"/mcp/messages?sessionId="+sessionID, "application/json", initBody)
	if initErr != nil {
		t.Fatalf("failed posting initialized: %v", initErr)
	}
	defer initResponse.Body.Close()
	if initResponse.StatusCode != http.StatusOK {
		t.Fatalf("expected initialized status 200, got %d", initResponse.StatusCode)
	}
}

func readSSEEvent(reader *bufio.Reader, timeout time.Duration) (string, string, error) {
	if timeout <= 0 {
		timeout = 2 * time.Second
	}
	type result struct {
		event string
		data  string
		err   error
	}
	resultCh := make(chan result, 1)

	go func() {
		event := ""
		data := ""
		for {
			line, err := reader.ReadString('\n')
			if err != nil {
				resultCh <- result{"", "", err}
				return
			}
			trimmed := strings.TrimSpace(line)
			if trimmed == "" {
				if event != "" || data != "" {
					resultCh <- result{event: event, data: data, err: nil}
					return
				}
				continue
			}
			if strings.HasPrefix(trimmed, "event:") {
				event = strings.TrimSpace(strings.TrimPrefix(trimmed, "event:"))
			}
			if strings.HasPrefix(trimmed, "data:") {
				if data != "" {
					data += "\n"
				}
				data += strings.TrimSpace(strings.TrimPrefix(trimmed, "data:"))
			}
		}
	}()

	select {
	case result := <-resultCh:
		return result.event, result.data, result.err
	case <-time.After(timeout):
		return "", "", context.DeadlineExceeded
	}
}
