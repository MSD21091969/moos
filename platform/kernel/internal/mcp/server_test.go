package mcp_test

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/mcp"
	"moos/platform/kernel/internal/shell"
)

var testActor = cat.URN("urn:moos:identity:test-actor")

func newTestMCP(t *testing.T) *mcp.Server {
	t.Helper()
	rt, err := shell.NewRuntime(shell.NewMemStore(), nil)
	if err != nil {
		t.Fatalf("NewRuntime: %v", err)
	}
	return mcp.NewServer(rt)
}

func newSeededMCP(t *testing.T) *mcp.Server {
	t.Helper()
	rt, err := shell.NewRuntime(shell.NewMemStore(), nil)
	if err != nil {
		t.Fatalf("NewRuntime: %v", err)
	}
	prog := cat.Program{
		Actor: testActor,
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Actor: testActor, Add: &cat.AddPayload{URN: "urn:parent", TypeID: "node_container"}},
			{Type: cat.ADD, Actor: testActor, Add: &cat.AddPayload{URN: "urn:child", TypeID: "node_container"}},
			{Type: cat.LINK, Actor: testActor, Link: &cat.LinkPayload{SourceURN: "urn:parent", SourcePort: "OWNS", TargetURN: "urn:child", TargetPort: "OWNS"}},
		},
	}
	if _, err := rt.ApplyProgram(prog); err != nil {
		t.Fatalf("seed program: %v", err)
	}
	return mcp.NewServer(rt)
}

// jsonRPC builds a JSON-RPC 2.0 request body.
func jsonRPC(id any, method string, params any) []byte {
	req := map[string]any{
		"jsonrpc": "2.0",
		"id":      id,
		"method":  method,
	}
	if params != nil {
		p, _ := json.Marshal(params)
		req["params"] = json.RawMessage(p)
	}
	data, _ := json.Marshal(req)
	return data
}

// sseSession opens an SSE connection to the test server, reads the endpoint
// event to extract the session ID, and returns a channel of subsequent SSE
// event data lines. Call cleanup to close the connection.
func sseSession(t *testing.T, tsURL string) (sessionID string, events <-chan string, cleanup func()) {
	t.Helper()

	resp, err := http.Get(tsURL + "/sse")
	if err != nil {
		t.Fatalf("GET /sse: %v", err)
	}

	ch := make(chan string, 64)
	go func() {
		defer resp.Body.Close()
		scanner := bufio.NewScanner(resp.Body)
		for scanner.Scan() {
			line := scanner.Text()
			if strings.HasPrefix(line, "data: ") {
				ch <- strings.TrimPrefix(line, "data: ")
			}
		}
		close(ch)
	}()

	// First data line is the endpoint event.
	select {
	case data := <-ch:
		if idx := strings.Index(data, "sessionId="); idx >= 0 {
			sessionID = data[idx+len("sessionId="):]
		}
	case <-time.After(3 * time.Second):
		t.Fatal("timeout waiting for SSE endpoint event")
	}

	if sessionID == "" {
		t.Fatal("no sessionId in endpoint event")
	}

	return sessionID, ch, func() { resp.Body.Close() }
}

// postMessage sends a JSON-RPC message to the /message endpoint.
func postMessage(t *testing.T, tsURL, sessionID string, body []byte) *http.Response {
	t.Helper()
	url := fmt.Sprintf("%s/message?sessionId=%s", tsURL, sessionID)
	resp, err := http.Post(url, "application/json", bytes.NewReader(body))
	if err != nil {
		t.Fatalf("POST /message: %v", err)
	}
	return resp
}

// readSSEEvent reads the next SSE data payload from the events channel.
func readSSEEvent(t *testing.T, events <-chan string) string {
	t.Helper()
	select {
	case data := <-events:
		return data
	case <-time.After(3 * time.Second):
		t.Fatal("timeout waiting for SSE event")
		return ""
	}
}

// --- Tests ---

func TestHealthz(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/healthz")
	if err != nil {
		t.Fatalf("GET /healthz: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("expected 200, got %d", resp.StatusCode)
	}
	var body map[string]string
	json.NewDecoder(resp.Body).Decode(&body)
	if body["protocol"] != "mcp" {
		t.Errorf("expected protocol=mcp, got %v", body["protocol"])
	}
}

func TestSSE_Connects(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, _, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	if sessionID == "" {
		t.Error("expected non-empty sessionId")
	}
}

func TestMessage_MissingSession(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	resp, err := http.Post(ts.URL+"/message", "application/json", bytes.NewReader(jsonRPC(1, "initialize", nil)))
	if err != nil {
		t.Fatalf("POST: %v", err)
	}
	defer resp.Body.Close()

	var rpcResp mcp.Response
	json.NewDecoder(resp.Body).Decode(&rpcResp)
	if rpcResp.Error == nil {
		t.Error("expected error for missing sessionId")
	}
}

func TestMessage_UnknownSession(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	resp := postMessage(t, ts.URL, "nonexistent", jsonRPC(1, "initialize", nil))
	defer resp.Body.Close()

	var rpcResp mcp.Response
	json.NewDecoder(resp.Body).Decode(&rpcResp)
	if rpcResp.Error == nil {
		t.Error("expected error for unknown session")
	}
}

func TestSSE_Initialize(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, events, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	resp := postMessage(t, ts.URL, sessionID, jsonRPC(1, "initialize", nil))
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("expected 202, got %d", resp.StatusCode)
	}

	data := readSSEEvent(t, events)
	var rpcResp mcp.Response
	json.Unmarshal([]byte(data), &rpcResp)
	if rpcResp.Error != nil {
		t.Fatalf("unexpected error: %v", rpcResp.Error)
	}
	if !strings.Contains(data, "moos-kernel") {
		t.Errorf("expected moos-kernel in response, got: %s", data)
	}
	if !strings.Contains(data, mcp.ProtocolVersion) {
		t.Errorf("expected protocol version in response, got: %s", data)
	}
}

func TestSSE_ToolsList(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, events, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	resp := postMessage(t, ts.URL, sessionID, jsonRPC(1, "tools/list", nil))
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("expected 202, got %d", resp.StatusCode)
	}

	data := readSSEEvent(t, events)
	for _, tool := range []string{"graph_state", "node_lookup", "apply_morphism", "scoped_subgraph", "benchmark_project"} {
		if !strings.Contains(data, tool) {
			t.Errorf("expected tool %q in response, got: %s", tool, data)
		}
	}
}

func TestSSE_ToolCall_GraphState(t *testing.T) {
	srv := newSeededMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, events, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	params := map[string]any{"name": "graph_state", "arguments": map[string]any{}}
	resp := postMessage(t, ts.URL, sessionID, jsonRPC(1, "tools/call", params))
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("expected 202, got %d", resp.StatusCode)
	}

	data := readSSEEvent(t, events)
	if !strings.Contains(data, "urn:parent") {
		t.Errorf("expected urn:parent in graph state, got: %s", data)
	}
}

func TestSSE_ToolCall_NodeLookup(t *testing.T) {
	srv := newSeededMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, events, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	params := map[string]any{"name": "node_lookup", "arguments": map[string]any{"urn": "urn:parent"}}
	resp := postMessage(t, ts.URL, sessionID, jsonRPC(1, "tools/call", params))
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("expected 202, got %d", resp.StatusCode)
	}

	data := readSSEEvent(t, events)
	if !strings.Contains(data, "urn:parent") {
		t.Errorf("expected urn:parent in node lookup, got: %s", data)
	}
}

func TestSSE_ToolCall_NodeLookup_NotFound(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, events, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	params := map[string]any{"name": "node_lookup", "arguments": map[string]any{"urn": "urn:missing"}}
	resp := postMessage(t, ts.URL, sessionID, jsonRPC(1, "tools/call", params))
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("expected 202, got %d", resp.StatusCode)
	}

	data := readSSEEvent(t, events)
	if !strings.Contains(data, "isError") {
		t.Errorf("expected isError in response for missing node, got: %s", data)
	}
}

func TestSSE_ToolCall_ApplyMorphism(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, events, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	envelope := cat.Envelope{
		Type:  cat.ADD,
		Actor: testActor,
		Add:   &cat.AddPayload{URN: "urn:mcp-added", TypeID: "node_container"},
	}
	params := map[string]any{"name": "apply_morphism", "arguments": map[string]any{"envelope": envelope}}
	resp := postMessage(t, ts.URL, sessionID, jsonRPC(1, "tools/call", params))
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("expected 202, got %d", resp.StatusCode)
	}

	data := readSSEEvent(t, events)
	if strings.Contains(data, "isError") {
		t.Errorf("unexpected error in apply_morphism, got: %s", data)
	}
}

func TestSSE_ToolCall_ScopedSubgraph(t *testing.T) {
	srv := newSeededMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, events, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	params := map[string]any{"name": "scoped_subgraph", "arguments": map[string]any{"actor": "urn:parent"}}
	resp := postMessage(t, ts.URL, sessionID, jsonRPC(1, "tools/call", params))
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("expected 202, got %d", resp.StatusCode)
	}

	data := readSSEEvent(t, events)
	if !strings.Contains(data, "urn:parent") {
		t.Errorf("expected urn:parent in scoped subgraph, got: %s", data)
	}
}

func TestSSE_ToolCall_BenchmarkProject(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, events, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	params := map[string]any{"name": "benchmark_project", "arguments": map[string]any{}}
	resp := postMessage(t, ts.URL, sessionID, jsonRPC(1, "tools/call", params))
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("expected 202, got %d", resp.StatusCode)
	}

	data := readSSEEvent(t, events)
	if strings.Contains(data, "isError") {
		t.Errorf("unexpected error in benchmark_project, got: %s", data)
	}
}

func TestSSE_ToolCall_UnknownTool(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, events, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	params := map[string]any{"name": "nonexistent_tool", "arguments": map[string]any{}}
	resp := postMessage(t, ts.URL, sessionID, jsonRPC(1, "tools/call", params))
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("expected 202, got %d", resp.StatusCode)
	}

	data := readSSEEvent(t, events)
	if !strings.Contains(data, "isError") {
		t.Errorf("expected isError for unknown tool, got: %s", data)
	}
}

func TestSSE_MethodNotFound(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, events, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	resp := postMessage(t, ts.URL, sessionID, jsonRPC(1, "unknown/method", nil))
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("expected 202, got %d", resp.StatusCode)
	}

	data := readSSEEvent(t, events)
	if !strings.Contains(data, "method not found") {
		t.Errorf("expected method not found error, got: %s", data)
	}
}

func TestMessage_InvalidJSON(t *testing.T) {
	srv := newTestMCP(t)
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	sessionID, _, cleanup := sseSession(t, ts.URL)
	defer cleanup()

	url := fmt.Sprintf("%s/message?sessionId=%s", ts.URL, sessionID)
	resp, err := http.Post(url, "application/json", bytes.NewReader([]byte("not json")))
	if err != nil {
		t.Fatalf("POST: %v", err)
	}
	defer resp.Body.Close()

	// Parse errors are returned directly in HTTP body, not via SSE.
	var rpcResp mcp.Response
	json.NewDecoder(resp.Body).Decode(&rpcResp)
	if rpcResp.Error == nil || rpcResp.Error.Code != mcp.CodeParseError {
		t.Error("expected parse error for invalid JSON")
	}
}

func TestStdio_InitializeRoundTrip(t *testing.T) {
	srv := newTestMCP(t)

	in := bytes.NewBufferString(`{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}` + "\n")
	out := &bytes.Buffer{}

	if err := srv.HandleStdio(context.Background(), in, out); err != nil {
		t.Fatalf("HandleStdio: %v", err)
	}

	var resp mcp.Response
	if err := json.Unmarshal(bytes.TrimSpace(out.Bytes()), &resp); err != nil {
		t.Fatalf("unmarshal response: %v", err)
	}
	if resp.Error != nil {
		t.Fatalf("unexpected error: %+v", resp.Error)
	}

	data, _ := json.Marshal(resp.Result)
	if !strings.Contains(string(data), "moos-kernel") {
		t.Fatalf("expected initialize response with server info, got: %s", string(data))
	}
}

func TestStdio_InvalidJSONThenToolsList(t *testing.T) {
	srv := newTestMCP(t)

	in := bytes.NewBufferString("not json\n" + `{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}` + "\n")
	out := &bytes.Buffer{}

	if err := srv.HandleStdio(context.Background(), in, out); err != nil {
		t.Fatalf("HandleStdio: %v", err)
	}

	lines := strings.Split(strings.TrimSpace(out.String()), "\n")
	if len(lines) != 2 {
		t.Fatalf("expected 2 response lines, got %d: %q", len(lines), out.String())
	}

	var parseErrResp mcp.Response
	if err := json.Unmarshal([]byte(lines[0]), &parseErrResp); err != nil {
		t.Fatalf("unmarshal parse-error response: %v", err)
	}
	if parseErrResp.Error == nil || parseErrResp.Error.Code != mcp.CodeParseError {
		t.Fatalf("expected parse error response, got: %+v", parseErrResp)
	}

	var toolsResp mcp.Response
	if err := json.Unmarshal([]byte(lines[1]), &toolsResp); err != nil {
		t.Fatalf("unmarshal tools/list response: %v", err)
	}
	if toolsResp.Error != nil {
		t.Fatalf("unexpected tools/list error: %+v", toolsResp.Error)
	}

	data, _ := json.Marshal(toolsResp.Result)
	if !strings.Contains(string(data), "graph_state") {
		t.Fatalf("expected tools/list payload, got: %s", string(data))
	}
}
