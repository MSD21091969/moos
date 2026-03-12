package mcp

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/functor"
	"moos/platform/kernel/internal/shell"
)

// Server is the MCP bridge — SSE transport wrapping the kernel runtime.
type Server struct {
	runtime *shell.Runtime
	mux     *http.ServeMux
	srv     *http.Server

	mu       sync.Mutex
	sessions map[string]*session
}

// session represents a connected SSE client.
type session struct {
	id     string
	events chan []byte // outbound SSE events
	done   chan struct{}
}

// NewServer creates an MCP server backed by the given runtime.
func NewServer(runtime *shell.Runtime) *Server {
	s := &Server{
		runtime:  runtime,
		mux:      http.NewServeMux(),
		sessions: make(map[string]*session),
	}
	s.mux.HandleFunc("GET /sse", s.handleSSE)
	s.mux.HandleFunc("POST /message", s.handleMessage)
	s.mux.HandleFunc("GET /healthz", s.handleHealthz)
	return s
}

// ListenAndServe starts the MCP SSE server on the given address.
func (s *Server) ListenAndServe(addr string) error {
	s.srv = &http.Server{
		Addr:              addr,
		Handler:           s.mux,
		ReadHeaderTimeout: 10 * time.Second,
		MaxHeaderBytes:    1 << 20,
	}
	log.Printf("[mcp] listening on %s", addr)
	return s.srv.ListenAndServe()
}

// Shutdown gracefully stops the server.
func (s *Server) Shutdown(ctx context.Context) error {
	s.mu.Lock()
	for _, sess := range s.sessions {
		close(sess.done)
	}
	s.sessions = make(map[string]*session)
	s.mu.Unlock()

	if s.srv == nil {
		return nil
	}
	return s.srv.Shutdown(ctx)
}

// Handler returns the http.Handler for testing.
func (s *Server) Handler() http.Handler {
	return s.mux
}

// handleSSE establishes a Server-Sent Events stream for a client session.
func (s *Server) handleSSE(w http.ResponseWriter, r *http.Request) {
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming not supported", http.StatusInternalServerError)
		return
	}

	sessionID := fmt.Sprintf("sess_%d", time.Now().UnixNano())
	sess := &session{
		id:     sessionID,
		events: make(chan []byte, 64),
		done:   make(chan struct{}),
	}
	s.mu.Lock()
	s.sessions[sessionID] = sess
	s.mu.Unlock()

	defer func() {
		s.mu.Lock()
		delete(s.sessions, sessionID)
		s.mu.Unlock()
	}()

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	// Send the endpoint event — tells the client where to POST messages.
	endpointMsg := fmt.Sprintf("event: endpoint\ndata: /message?sessionId=%s\n\n", sessionID)
	fmt.Fprint(w, endpointMsg)
	flusher.Flush()

	log.Printf("[mcp] session %s connected", sessionID)

	for {
		select {
		case <-r.Context().Done():
			log.Printf("[mcp] session %s disconnected", sessionID)
			return
		case <-sess.done:
			return
		case data := <-sess.events:
			fmt.Fprintf(w, "event: message\ndata: %s\n\n", data)
			flusher.Flush()
		}
	}
}

// handleMessage processes a JSON-RPC 2.0 message from a client.
func (s *Server) handleMessage(w http.ResponseWriter, r *http.Request) {
	sessionID := r.URL.Query().Get("sessionId")
	if sessionID == "" {
		writeJSONRPCError(w, nil, CodeInvalidRequest, "missing sessionId")
		return
	}

	s.mu.Lock()
	sess, ok := s.sessions[sessionID]
	s.mu.Unlock()
	if !ok {
		writeJSONRPCError(w, nil, CodeInvalidRequest, "unknown session")
		return
	}

	var req Request
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSONRPCError(w, nil, CodeParseError, "invalid JSON")
		return
	}

	if req.JSONRPC != "2.0" {
		writeJSONRPCError(w, req.ID, CodeInvalidRequest, "jsonrpc must be 2.0")
		return
	}

	resp := s.dispatch(req)

	data, err := json.Marshal(resp)
	if err != nil {
		writeJSONRPCError(w, req.ID, CodeInternalError, "marshal error")
		return
	}

	// Send response via SSE and also return 202.
	select {
	case sess.events <- data:
	default:
		log.Printf("[mcp] session %s: event buffer full, dropping", sessionID)
	}

	w.WriteHeader(http.StatusAccepted)
}

// dispatch routes a JSON-RPC request to the appropriate handler.
func (s *Server) dispatch(req Request) Response {
	switch req.Method {
	case MethodInitialize:
		return s.handleInitialize(req)
	case MethodToolsList:
		return s.handleToolsList(req)
	case MethodToolsCall:
		return s.handleToolsCall(req)
	default:
		return Response{
			JSONRPC: "2.0",
			ID:      req.ID,
			Error:   &RPCError{Code: CodeMethodNotFound, Message: fmt.Sprintf("method not found: %s", req.Method)},
		}
	}
}

// handleInitialize returns server capabilities.
func (s *Server) handleInitialize(req Request) Response {
	return Response{
		JSONRPC: "2.0",
		ID:      req.ID,
		Result: InitializeResult{
			ProtocolVersion: ProtocolVersion,
			Capabilities: ServerCapabilities{
				Tools: &ToolsCapability{},
			},
			ServerInfo: Implementation{
				Name:    "moos-kernel",
				Version: "0.1.0",
			},
		},
	}
}

// handleToolsList returns the list of available tools.
func (s *Server) handleToolsList(req Request) Response {
	return Response{
		JSONRPC: "2.0",
		ID:      req.ID,
		Result:  ToolsListResult{Tools: toolDefinitions()},
	}
}

// handleToolsCall dispatches to the named tool.
func (s *Server) handleToolsCall(req Request) Response {
	var params ToolCallParams
	if err := json.Unmarshal(req.Params, &params); err != nil {
		return Response{
			JSONRPC: "2.0",
			ID:      req.ID,
			Error:   &RPCError{Code: CodeInvalidParams, Message: "invalid tool call params"},
		}
	}

	result := s.callTool(params)
	return Response{
		JSONRPC: "2.0",
		ID:      req.ID,
		Result:  result,
	}
}

// callTool dispatches to the correct tool implementation.
func (s *Server) callTool(params ToolCallParams) ToolCallResult {
	switch params.Name {
	case "graph_state":
		return toolGraphState(s.runtime)
	case "node_lookup":
		return toolNodeLookup(s.runtime, params.Arguments)
	case "apply_morphism":
		return toolApplyMorphism(s.runtime, params.Arguments)
	case "scoped_subgraph":
		return toolScopedSubgraph(s.runtime, params.Arguments)
	case "benchmark_project":
		return toolBenchmarkProject(s.runtime)
	default:
		return ToolCallResult{
			IsError: true,
			Content: []ContentBlock{{Type: "text", Text: fmt.Sprintf("unknown tool: %s", params.Name)}},
		}
	}
}

// handleHealthz is a simple health check for the MCP server.
func (s *Server) handleHealthz(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok", "protocol": "mcp"})
}

// --- helpers ---

func writeJSONRPCError(w http.ResponseWriter, id any, code int, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(Response{
		JSONRPC: "2.0",
		ID:      id,
		Error:   &RPCError{Code: code, Message: msg},
	})
}

// --- Tool definitions ---

func toolDefinitions() []ToolDefinition {
	return []ToolDefinition{
		{
			Name:        "graph_state",
			Description: "Returns the full graph state (all nodes and wires).",
			InputSchema: json.RawMessage(`{"type":"object","properties":{}}`),
		},
		{
			Name:        "node_lookup",
			Description: "Returns a single node by URN.",
			InputSchema: json.RawMessage(`{"type":"object","properties":{"urn":{"type":"string","description":"The URN of the node to look up."}},"required":["urn"]}`),
		},
		{
			Name:        "apply_morphism",
			Description: "Applies a morphism envelope (ADD, LINK, MUTATE, or UNLINK) to the graph.",
			InputSchema: json.RawMessage(`{"type":"object","properties":{"envelope":{"type":"object","description":"A morphism envelope with type, actor, and payload."}},"required":["envelope"]}`),
		},
		{
			Name:        "scoped_subgraph",
			Description: "Returns the ownership-scoped subgraph reachable via OWNS from an actor URN.",
			InputSchema: json.RawMessage(`{"type":"object","properties":{"actor":{"type":"string","description":"The actor URN whose ownership scope to return."}},"required":["actor"]}`),
		},
		{
			Name:        "benchmark_project",
			Description: "Runs the benchmark functor (FUN05) and returns provider rankings per suite.",
			InputSchema: json.RawMessage(`{"type":"object","properties":{}}`),
		},
	}
}

// --- Tool implementations ---

func toolGraphState(rt *shell.Runtime) ToolCallResult {
	state := rt.State()
	data, err := json.Marshal(state)
	if err != nil {
		return errResult(fmt.Sprintf("marshal error: %v", err))
	}
	return ToolCallResult{Content: []ContentBlock{{Type: "text", Text: string(data)}}}
}

func toolNodeLookup(rt *shell.Runtime, args json.RawMessage) ToolCallResult {
	var p struct {
		URN string `json:"urn"`
	}
	if err := json.Unmarshal(args, &p); err != nil || p.URN == "" {
		return errResult("urn is required")
	}
	node, ok := rt.Node(cat.URN(p.URN))
	if !ok {
		return errResult(fmt.Sprintf("node not found: %s", p.URN))
	}
	data, err := json.Marshal(node)
	if err != nil {
		return errResult(fmt.Sprintf("marshal error: %v", err))
	}
	return ToolCallResult{Content: []ContentBlock{{Type: "text", Text: string(data)}}}
}

func toolApplyMorphism(rt *shell.Runtime, args json.RawMessage) ToolCallResult {
	var p struct {
		Envelope cat.Envelope `json:"envelope"`
	}
	if err := json.Unmarshal(args, &p); err != nil {
		return errResult(fmt.Sprintf("invalid envelope: %v", err))
	}
	result, err := rt.Apply(p.Envelope)
	if err != nil {
		return errResult(fmt.Sprintf("apply error: %v", err))
	}
	data, err := json.Marshal(result)
	if err != nil {
		return errResult(fmt.Sprintf("marshal error: %v", err))
	}
	return ToolCallResult{Content: []ContentBlock{{Type: "text", Text: string(data)}}}
}

func toolScopedSubgraph(rt *shell.Runtime, args json.RawMessage) ToolCallResult {
	var p struct {
		Actor string `json:"actor"`
	}
	if err := json.Unmarshal(args, &p); err != nil || p.Actor == "" {
		return errResult("actor is required")
	}
	state := rt.ScopedSubgraph(cat.URN(p.Actor))
	data, err := json.Marshal(state)
	if err != nil {
		return errResult(fmt.Sprintf("marshal error: %v", err))
	}
	return ToolCallResult{Content: []ContentBlock{{Type: "text", Text: string(data)}}}
}

func toolBenchmarkProject(rt *shell.Runtime) ToolCallResult {
	bench := functor.Benchmark{}
	result, err := bench.Project(rt.State())
	if err != nil {
		return errResult(fmt.Sprintf("benchmark error: %v", err))
	}
	data, err := json.Marshal(result)
	if err != nil {
		return errResult(fmt.Sprintf("marshal error: %v", err))
	}
	return ToolCallResult{Content: []ContentBlock{{Type: "text", Text: string(data)}}}
}

func errResult(msg string) ToolCallResult {
	return ToolCallResult{
		IsError: true,
		Content: []ContentBlock{{Type: "text", Text: msg}},
	}
}
