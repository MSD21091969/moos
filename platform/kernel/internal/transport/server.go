// Package transport provides the HTTP API — the only external interface to the kernel.
// All mutations go through the four invariant NTs via the shell.Runtime.
// Read paths are direct GraphState projections (functor deferred).
package transport

import (
	"context"
	_ "embed"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/functor"
	"moos/platform/kernel/internal/hydration"
	"moos/platform/kernel/internal/lens"
	"moos/platform/kernel/internal/shell"
)

//go:embed static/explorer.html
var explorerHTML []byte

// Server is the HTTP transport layer.
type Server struct {
	inspect shell.InspectSubstrate
	run     shell.RunSubstrate
	kbRoot  string // path to knowledge-base root; empty when --kb not supplied
	mux     *http.ServeMux
	srv     *http.Server

	bridgeMu      sync.Mutex
	bridgeCursors map[cat.URN]time.Time
}

// NewServer creates a new HTTP server bound to the given runtime.
// kbRoot is the path to the knowledge-base root directory; pass "" when
// the --kb flag was not supplied (source-based materialize will return 501).
func NewServer(inspect shell.InspectSubstrate, run shell.RunSubstrate, kbRoot string) *Server {
	s := &Server{
		inspect:       inspect,
		run:           run,
		kbRoot:        kbRoot,
		mux:           http.NewServeMux(),
		bridgeCursors: make(map[cat.URN]time.Time),
	}
	s.registerRoutes()
	return s
}

func (s *Server) registerRoutes() {
	s.mux.HandleFunc("GET /healthz", s.handleHealthz)
	s.mux.HandleFunc("GET /state", s.handleState)
	s.mux.HandleFunc("GET /state/nodes", s.handleNodes)
	s.mux.HandleFunc("GET /state/nodes/", s.handleNodeByURN)
	s.mux.HandleFunc("GET /state/wires", s.handleWires)
	s.mux.HandleFunc("GET /state/wires/outgoing/", s.handleOutgoingWires)
	s.mux.HandleFunc("GET /state/wires/incoming/", s.handleIncomingWires)
	s.mux.HandleFunc("POST /morphisms", s.handlePostMorphism)
	s.mux.HandleFunc("POST /programs", s.handlePostProgram)
	s.mux.HandleFunc("GET /log", s.handleLog)
	s.mux.HandleFunc("GET /log/stream", s.handleLogStream)
	s.mux.HandleFunc("GET /semantics/registry", s.handleRegistry)
	s.mux.HandleFunc("POST /hydration/materialize", s.handleMaterialize)
	s.mux.HandleFunc("GET /state/scope/", s.handleScope)
	s.mux.HandleFunc("GET /state/lens", s.handleLens)
	s.mux.HandleFunc("POST /state/lens", s.handleLensPost)
	s.mux.HandleFunc("GET /state/saturation", s.handleSaturation)
	s.mux.HandleFunc("GET /functor/benchmark/", s.handleBenchmarkFunctor)
	s.mux.HandleFunc("GET /functor/port-inventory", s.handlePortInventoryFunctor)
	s.mux.HandleFunc("GET /functor/binding-category", s.handleBindingCategoryFunctor)
	s.mux.HandleFunc("GET /functor/port-functor", s.handlePortFunctor)
	s.mux.HandleFunc("GET /functor/pipeline-metrics", s.handlePipelineMetricsFunctor)
	s.mux.HandleFunc("GET /explorer", s.handleExplorer)
	s.mux.HandleFunc("GET /functor/ui", s.handleUIFunctor)
	s.mux.HandleFunc("GET /functor/calendar", s.handleCalendarFunctor)
	s.mux.HandleFunc("GET /bridge/", s.handleBridge)
	s.mux.HandleFunc("POST /bridge/sync", s.handleBridgeSync)
	s.mux.HandleFunc("POST /callback/calendar/sync", s.handleCalendarSync)

	// Right-adjoint (Ingest)
	s.mux.HandleFunc("POST /webhooks/gcal", HandleGCalWebhook(s.run))
}

// ListenAndServe starts the HTTP server on the given address.
func (s *Server) ListenAndServe(addr string) error {
	s.srv = &http.Server{
		Addr:              addr,
		Handler:           s.mux,
		ReadHeaderTimeout: 10 * time.Second,
		IdleTimeout:       120 * time.Second,
		MaxHeaderBytes:    1 << 20,
	}
	log.Printf("[transport] listening on %s", addr)
	return s.srv.ListenAndServe()
}

// Shutdown gracefully stops the server.
func (s *Server) Shutdown(ctx context.Context) error {
	if s.srv == nil {
		return nil
	}
	return s.srv.Shutdown(ctx)
}

// Handler returns the http.Handler for testing.
func (s *Server) Handler() http.Handler {
	return s.mux
}

// --- Handlers ---

func (s *Server) handleHealthz(w http.ResponseWriter, r *http.Request) {
	resp := map[string]any{
		"status":    "ok",
		"nodes":     len(s.inspect.Nodes()),
		"wires":     len(s.inspect.Wires()),
		"log_depth": s.inspect.LogLen(),
	}
	if epoch := s.inspect.Epoch(); !epoch.IsZero() {
		resp["epoch"] = epoch.UTC().Format(time.RFC3339Nano)
	}
	writeJSON(w, http.StatusOK, resp)
}

func (s *Server) handleState(w http.ResponseWriter, r *http.Request) {
	state := s.inspect.State()
	if r.URL.Query().Has("compact") {
		writeJSONCompact(w, http.StatusOK, state)
		return
	}
	writeJSON(w, http.StatusOK, state)
}

func (s *Server) handleNodes(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, s.inspect.Nodes())
}

func (s *Server) handleNodeByURN(w http.ResponseWriter, r *http.Request) {
	urn := cat.URN(strings.TrimPrefix(r.URL.Path, "/state/nodes/"))
	if urn == "" {
		writeError(w, http.StatusBadRequest, "missing URN")
		return
	}
	node, ok := s.inspect.Node(urn)
	if !ok {
		writeError(w, http.StatusNotFound, fmt.Sprintf("node %s not found", urn))
		return
	}
	writeJSON(w, http.StatusOK, node)
}

func (s *Server) handleWires(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, s.inspect.Wires())
}

func (s *Server) handleOutgoingWires(w http.ResponseWriter, r *http.Request) {
	urn := cat.URN(strings.TrimPrefix(r.URL.Path, "/state/wires/outgoing/"))
	if urn == "" {
		writeError(w, http.StatusBadRequest, "missing URN")
		return
	}
	writeJSON(w, http.StatusOK, s.inspect.OutgoingWires(urn))
}

func (s *Server) handleIncomingWires(w http.ResponseWriter, r *http.Request) {
	urn := cat.URN(strings.TrimPrefix(r.URL.Path, "/state/wires/incoming/"))
	if urn == "" {
		writeError(w, http.StatusBadRequest, "missing URN")
		return
	}
	writeJSON(w, http.StatusOK, s.inspect.IncomingWires(urn))
}

func (s *Server) handleScope(w http.ResponseWriter, r *http.Request) {
	urn := cat.URN(strings.TrimPrefix(r.URL.Path, "/state/scope/"))
	if urn == "" {
		writeError(w, http.StatusBadRequest, "missing actor URN")
		return
	}
	writeJSON(w, http.StatusOK, s.inspect.ScopedSubgraph(urn))
}

func (s *Server) handleLens(w http.ResponseWriter, r *http.Request) {
	state := s.inspect.State()
	if scope := strings.TrimSpace(r.URL.Query().Get("scope")); scope != "" {
		state = s.inspect.ScopedSubgraph(cat.URN(scope))
	}
	spec := lens.ParseQueryParams(r.URL.Query())
	writeJSON(w, http.StatusOK, lens.Apply(state, spec))
}

func (s *Server) handleLensPost(w http.ResponseWriter, r *http.Request) {
	state := s.inspect.State()
	if scope := strings.TrimSpace(r.URL.Query().Get("scope")); scope != "" {
		state = s.inspect.ScopedSubgraph(cat.URN(scope))
	}

	var spec lens.LensSpec
	if err := json.NewDecoder(r.Body).Decode(&spec); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Sprintf("invalid JSON: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, lens.Apply(state, spec))
}

func (s *Server) handleSaturation(w http.ResponseWriter, r *http.Request) {
	reg := s.inspect.Registry()
	if reg == nil {
		writeJSON(w, http.StatusOK, map[string]any{"status": "no registry loaded"})
		return
	}
	state := s.inspect.State()

	// Optional single-node lookup: ?urn=<urn>
	if urnParam := strings.TrimSpace(r.URL.Query().Get("urn")); urnParam != "" {
		sat, ok := lens.ComputeNodeSaturation(state, reg, cat.URN(urnParam))
		if !ok {
			writeError(w, http.StatusNotFound,
				fmt.Sprintf("node %s not found or has no port spec", urnParam))
			return
		}
		writeJSON(w, http.StatusOK, sat)
		return
	}

	writeJSON(w, http.StatusOK, lens.ComputeSaturation(state, reg))
}

func (s *Server) handlePostMorphism(w http.ResponseWriter, r *http.Request) {
	var env cat.Envelope
	if err := json.NewDecoder(r.Body).Decode(&env); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Sprintf("invalid JSON: %v", err))
		return
	}
	result, err := s.run.Apply(env)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, result)
}

func (s *Server) handlePostProgram(w http.ResponseWriter, r *http.Request) {
	var prog cat.Program
	if err := json.NewDecoder(r.Body).Decode(&prog); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Sprintf("invalid JSON: %v", err))
		return
	}
	result, err := s.run.ApplyProgram(prog)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, result)
}

type bridgeSyncRequest struct {
	SourceKernelURN cat.URN        `json:"source_kernel_urn,omitempty"`
	TargetKernelURN cat.URN        `json:"target_kernel_urn,omitempty"`
	Envelopes       []cat.Envelope `json:"envelopes,omitempty"`
	Program         *cat.Program   `json:"program,omitempty"`
}

func (s *Server) bridgeCursor(urn cat.URN) time.Time {
	s.bridgeMu.Lock()
	defer s.bridgeMu.Unlock()
	return s.bridgeCursors[urn]
}

func (s *Server) setBridgeCursor(urn cat.URN, ts time.Time) {
	s.bridgeMu.Lock()
	defer s.bridgeMu.Unlock()
	if ts.IsZero() {
		return
	}
	if prev, ok := s.bridgeCursors[urn]; ok && !ts.After(prev) {
		return
	}
	s.bridgeCursors[urn] = ts
}

func (s *Server) handleBridgeDiff(w http.ResponseWriter, r *http.Request) {
	kernelURN := cat.URN(strings.TrimPrefix(r.URL.Path, "/bridge/"))
	if kernelURN == "" {
		writeError(w, http.StatusBadRequest, "missing kernel URN")
		return
	}

	node, ok := s.inspect.Node(kernelURN)
	if !ok {
		writeError(w, http.StatusNotFound, fmt.Sprintf("kernel node %s not found", kernelURN))
		return
	}
	if !isBridgeKernelNode(node) {
		writeError(w, http.StatusBadRequest, fmt.Sprintf("node %s is type %s, expected kernel_instance or infra_service", kernelURN, node.TypeID))
		return
	}

	since := s.bridgeCursor(kernelURN)
	if sinceParam := strings.TrimSpace(r.URL.Query().Get("since")); sinceParam != "" {
		t, err := time.Parse(time.RFC3339, sinceParam)
		if err != nil {
			writeError(w, http.StatusBadRequest, fmt.Sprintf("invalid since (RFC3339 required): %v", err))
			return
		}
		since = t.UTC()
	}

	entries := s.inspect.Log()
	diff := make([]cat.PersistedEnvelope, 0, len(entries))
	until := since
	for _, entry := range entries {
		if !entry.IssuedAt.After(since) {
			continue
		}
		diff = append(diff, entry)
		if entry.IssuedAt.After(until) {
			until = entry.IssuedAt
		}
	}

	if len(diff) > 0 {
		s.setBridgeCursor(kernelURN, until)
	}

	resp := map[string]any{
		"kernel_urn": kernelURN,
		"since":      since.UTC().Format(time.RFC3339Nano),
		"until":      until.UTC().Format(time.RFC3339Nano),
		"count":      len(diff),
		"envelopes":  diff,
	}
	writeJSON(w, http.StatusOK, resp)
}

func (s *Server) handleBridge(w http.ResponseWriter, r *http.Request) {
	if strings.HasSuffix(r.URL.Path, "/fiber") {
		s.handleBridgeFiber(w, r)
		return
	}
	s.handleBridgeDiff(w, r)
}

type fiberNode struct {
	URN     cat.URN        `json:"urn"`
	TypeID  cat.TypeID     `json:"type_id"`
	Payload map[string]any `json:"payload,omitempty"`
}

type fiberWire struct {
	SourceURN  cat.URN  `json:"source_urn"`
	SourcePort cat.Port `json:"source_port"`
	TargetURN  cat.URN  `json:"target_urn"`
	TargetPort cat.Port `json:"target_port"`
}

type fiberInterfacePort struct {
	URN       cat.URN  `json:"urn"`
	Port      cat.Port `json:"port"`
	Direction string   `json:"direction"`
}

func (s *Server) handleBridgeFiber(w http.ResponseWriter, r *http.Request) {
	if !strings.HasSuffix(r.URL.Path, "/fiber") {
		return
	}

	kernelURN := cat.URN(strings.TrimSuffix(strings.TrimPrefix(r.URL.Path, "/bridge/"), "/fiber"))
	if kernelURN == "" {
		writeError(w, http.StatusBadRequest, "missing kernel URN")
		return
	}

	kernelNode, ok := s.inspect.Node(kernelURN)
	if !ok {
		writeError(w, http.StatusNotFound, fmt.Sprintf("kernel node %s not found", kernelURN))
		return
	}
	if !isBridgeKernelNode(kernelNode) {
		writeError(w, http.StatusBadRequest, fmt.Sprintf("node %s is type %s, expected kernel_instance or infra_service", kernelURN, kernelNode.TypeID))
		return
	}

	root := cat.URN(strings.TrimSpace(r.URL.Query().Get("root")))
	if root == "" {
		writeError(w, http.StatusBadRequest, "missing root query parameter")
		return
	}
	if _, ok := s.inspect.Node(root); !ok {
		writeError(w, http.StatusNotFound, fmt.Sprintf("root node %s not found", root))
		return
	}

	depth := 1
	if depthStr := strings.TrimSpace(r.URL.Query().Get("depth")); depthStr != "" {
		n, err := strconv.Atoi(depthStr)
		if err != nil || n < 0 {
			writeError(w, http.StatusBadRequest, "invalid depth (must be integer >= 0)")
			return
		}
		depth = n
	}

	state := s.inspect.State()
	visited := map[cat.URN]bool{root: true}
	type queueEntry struct {
		urn   cat.URN
		level int
	}
	queue := []queueEntry{{urn: root, level: 0}}

	for len(queue) > 0 {
		cur := queue[0]
		queue = queue[1:]
		if cur.level >= depth {
			continue
		}
		for _, wire := range state.Wires {
			var next cat.URN
			if wire.SourceURN == cur.urn {
				next = wire.TargetURN
			} else if wire.TargetURN == cur.urn {
				next = wire.SourceURN
			} else {
				continue
			}
			if !visited[next] {
				visited[next] = true
				queue = append(queue, queueEntry{urn: next, level: cur.level + 1})
			}
		}
	}

	nodes := make([]fiberNode, 0, len(visited))
	for urn := range visited {
		n := state.Nodes[urn]
		nodes = append(nodes, fiberNode{URN: n.URN, TypeID: n.TypeID, Payload: n.Payload})
	}
	sort.Slice(nodes, func(i, j int) bool { return nodes[i].URN < nodes[j].URN })

	wires := make([]fiberWire, 0)
	interfaceSeen := map[string]bool{}
	interfaces := make([]fiberInterfacePort, 0)

	for _, wire := range state.Wires {
		sIn := visited[wire.SourceURN]
		tIn := visited[wire.TargetURN]

		if sIn && tIn {
			wires = append(wires, fiberWire{
				SourceURN:  wire.SourceURN,
				SourcePort: wire.SourcePort,
				TargetURN:  wire.TargetURN,
				TargetPort: wire.TargetPort,
			})
			continue
		}

		if sIn && !tIn {
			key := string(wire.SourceURN) + "|" + string(wire.SourcePort) + "|out"
			if !interfaceSeen[key] {
				interfaces = append(interfaces, fiberInterfacePort{URN: wire.SourceURN, Port: wire.SourcePort, Direction: "out"})
				interfaceSeen[key] = true
			}
		}
		if !sIn && tIn {
			key := string(wire.TargetURN) + "|" + string(wire.TargetPort) + "|in"
			if !interfaceSeen[key] {
				interfaces = append(interfaces, fiberInterfacePort{URN: wire.TargetURN, Port: wire.TargetPort, Direction: "in"})
				interfaceSeen[key] = true
			}
		}
	}

	sort.Slice(wires, func(i, j int) bool {
		if wires[i].SourceURN != wires[j].SourceURN {
			return wires[i].SourceURN < wires[j].SourceURN
		}
		if wires[i].SourcePort != wires[j].SourcePort {
			return wires[i].SourcePort < wires[j].SourcePort
		}
		if wires[i].TargetURN != wires[j].TargetURN {
			return wires[i].TargetURN < wires[j].TargetURN
		}
		return wires[i].TargetPort < wires[j].TargetPort
	})

	sort.Slice(interfaces, func(i, j int) bool {
		if interfaces[i].URN != interfaces[j].URN {
			return interfaces[i].URN < interfaces[j].URN
		}
		if interfaces[i].Port != interfaces[j].Port {
			return interfaces[i].Port < interfaces[j].Port
		}
		return interfaces[i].Direction < interfaces[j].Direction
	})

	writeJSON(w, http.StatusOK, map[string]any{
		"kernel_urn":      kernelURN,
		"root":            root,
		"depth":           depth,
		"nodes":           nodes,
		"wires":           wires,
		"interface_ports": interfaces,
		"completeness":    1.0,
	})
}

func isBridgeKernelNode(n cat.Node) bool {
	return n.TypeID == "kernel_instance" || n.TypeID == "infra_service"
}

func (s *Server) handleCalendarSync(w http.ResponseWriter, r *http.Request) {
	var entry CalendarEntry
	if err := json.NewDecoder(r.Body).Decode(&entry); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Sprintf("invalid JSON: %v", err))
		return
	}

	envelopes := IngestCalendarEvent(entry)
	if len(envelopes) == 0 {
		writeError(w, http.StatusBadRequest, "no envelopes generated")
		return
	}

	applied := 0
	errs := make([]string, 0)
	for _, env := range envelopes {
		if _, err := s.run.Apply(env); err != nil {
			errs = append(errs, err.Error())
			continue
		}
		applied++
	}

	status := http.StatusAccepted
	if applied == 0 {
		status = http.StatusUnprocessableEntity
	}

	writeJSON(w, status, map[string]any{
		"status":         "ok",
		"applied":        applied,
		"generated":      len(envelopes),
		"errors":         errs,
		"calendar_event": entry.ID,
	})
}

func (s *Server) handleBridgeSync(w http.ResponseWriter, r *http.Request) {
	var req bridgeSyncRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Sprintf("invalid JSON: %v", err))
		return
	}

	var prog cat.Program
	switch {
	case req.Program != nil:
		prog = *req.Program
	case len(req.Envelopes) > 0:
		prog = cat.Program{Envelopes: req.Envelopes}
	default:
		writeError(w, http.StatusBadRequest, "request must include either program or non-empty envelopes")
		return
	}

	result, err := s.run.ApplyProgram(prog)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}

	if req.TargetKernelURN != "" && len(result.Persisted) > 0 {
		last := result.Persisted[len(result.Persisted)-1].IssuedAt
		s.setBridgeCursor(req.TargetKernelURN, last)
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"status":            "ok",
		"applied":           len(result.Results),
		"source_kernel_urn": req.SourceKernelURN,
		"target_kernel_urn": req.TargetKernelURN,
		"summary":           result.Summary,
	})
}

func (s *Server) handleLog(w http.ResponseWriter, r *http.Request) {
	entries := s.inspect.Log()
	q := r.URL.Query()

	// ?after=<RFC3339>
	if afterStr := q.Get("after"); afterStr != "" {
		t, err := time.Parse(time.RFC3339, afterStr)
		if err != nil {
			http.Error(w, "invalid after param: "+err.Error(), http.StatusBadRequest)
			return
		}
		filtered := entries[:0]
		for _, e := range entries {
			if e.IssuedAt.After(t) {
				filtered = append(filtered, e)
			}
		}
		entries = filtered
	}

	// ?actor=<urn>
	if actor := q.Get("actor"); actor != "" {
		filtered := entries[:0]
		for _, e := range entries {
			if string(e.Envelope.Actor) == actor {
				filtered = append(filtered, e)
			}
		}
		entries = filtered
	}

	// ?type=<ADD|LINK|MUTATE|UNLINK>
	if typeStr := q.Get("type"); typeStr != "" {
		upper := strings.ToUpper(typeStr)
		filtered := entries[:0]
		for _, e := range entries {
			if strings.ToUpper(string(e.Envelope.Type)) == upper {
				filtered = append(filtered, e)
			}
		}
		entries = filtered
	}

	// ?limit=<n>
	if limitStr := q.Get("limit"); limitStr != "" {
		n, err := strconv.Atoi(limitStr)
		if err != nil || n < 0 {
			http.Error(w, "invalid limit param", http.StatusBadRequest)
			return
		}
		if n < len(entries) {
			entries = entries[len(entries)-n:]
		}
	}

	writeJSON(w, http.StatusOK, entries)
}

// handleLogStream streams new morphisms over SSE as they are applied.
// Clients receive events of type "morphism" with JSON-encoded PersistedEnvelope data.
func (s *Server) handleLogStream(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	fl, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming unsupported", http.StatusInternalServerError)
		return
	}

	id, ch := s.inspect.Subscribe()
	defer s.inspect.Unsubscribe(id)

	// Send a comment as heartbeat to confirm stream opened.
	fmt.Fprintf(w, ": connected\n\n")
	fl.Flush()

	for {
		select {
		case entry, ok := <-ch:
			if !ok {
				return
			}
			data, err := json.Marshal(entry)
			if err != nil {
				continue
			}
			fmt.Fprintf(w, "event: morphism\ndata: %s\n\n", data)
			if trigger, ok := s.firestarterTriggerFrom(entry); ok {
				triggerData, err := json.Marshal(trigger)
				if err == nil {
					fmt.Fprintf(w, "event: firestarter-trigger\ndata: %s\n\n", triggerData)
				}
			}
			fl.Flush()
		case <-r.Context().Done():
			return
		}
	}
}

func (s *Server) firestarterTriggerFrom(entry cat.PersistedEnvelope) (map[string]any, bool) {
	if entry.Envelope.Type != cat.LINK || entry.Envelope.Link == nil {
		return nil, false
	}

	link := entry.Envelope.Link
	targetNode, ok := s.inspect.Node(link.TargetURN)
	if !ok {
		return nil, false
	}

	targetType := strings.ToLower(string(targetNode.TypeID))
	isFirestarterType := strings.Contains(targetType, "firestarter")
	hasTriggerFilter := false

	if targetNode.TypeID == "agent_session" && targetNode.Payload != nil {
		if raw, exists := targetNode.Payload["trigger_filter"]; exists {
			switch v := raw.(type) {
			case string:
				hasTriggerFilter = strings.TrimSpace(v) != ""
			default:
				hasTriggerFilter = raw != nil
			}
		}
	}

	if !isFirestarterType && !hasTriggerFilter {
		return nil, false
	}

	return map[string]any{
		"source_urn":     link.SourceURN,
		"target_urn":     link.TargetURN,
		"source_port":    link.SourcePort,
		"target_port":    link.TargetPort,
		"target_type_id": targetNode.TypeID,
		"issued_at":      entry.IssuedAt.UTC().Format(time.RFC3339Nano),
	}, true
}

func (s *Server) handleRegistry(w http.ResponseWriter, r *http.Request) {
	reg := s.inspect.Registry()
	if reg == nil {
		writeJSON(w, http.StatusOK, map[string]any{"status": "no registry loaded"})
		return
	}
	writeJSON(w, http.StatusOK, reg)
}

func (s *Server) handleMaterialize(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		writeError(w, http.StatusBadRequest, fmt.Sprintf("read body: %v", err))
		return
	}

	// Source-based dispatch: {"source": "providers.json"} delegates to the
	// KB loader so callers can hydrate a single instance file by name.
	var probe struct {
		Source string `json:"source"`
	}
	if probErr := json.Unmarshal(body, &probe); probErr == nil && probe.Source != "" {
		s.handleMaterializeSource(w, r, probe.Source)
		return
	}

	// Standard path: caller supplies a full MaterializeRequest body.
	var req hydration.MaterializeRequest
	if err := json.Unmarshal(body, &req); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Sprintf("invalid JSON: %v", err))
		return
	}

	dryRun := r.URL.Query().Get("dry_run") == "true"
	reg := s.inspect.Registry()

	result, err := hydration.Materialize(req, reg, dryRun)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}
	if len(result.Errors) > 0 {
		writeJSON(w, http.StatusUnprocessableEntity, result)
		return
	}
	if dryRun {
		writeJSON(w, http.StatusOK, result)
		return
	}

	progResult, err := s.run.ApplyProgram(result.Program)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"materialized": result,
		"result":       progResult.Summary,
		"nodes_added":  len(result.Program.Envelopes),
	})
}

// handleMaterializeSource loads a single KB instance file by name and
// materializes it via ApplyProgram. kbRoot must be configured (--kb flag).
func (s *Server) handleMaterializeSource(w http.ResponseWriter, r *http.Request, source string) {
	if s.kbRoot == "" {
		writeError(w, http.StatusNotImplemented,
			"no KB root configured; restart with --kb flag to enable source-based hydration")
		return
	}

	dryRun := r.URL.Query().Get("dry_run") == "true"

	req, err := hydration.LoadInstanceFile(s.kbRoot, source, "")
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, fmt.Sprintf("load %s: %v", source, err))
		return
	}

	reg := s.inspect.Registry()
	result, err := hydration.Materialize(req, reg, dryRun)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}
	if len(result.Errors) > 0 {
		writeJSON(w, http.StatusUnprocessableEntity, result)
		return
	}
	if dryRun {
		writeJSON(w, http.StatusOK, result)
		return
	}

	progResult, err := s.run.ApplyProgram(result.Program)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}
	log.Printf("[transport] materialize source=%s applied", source)
	writeJSON(w, http.StatusOK, map[string]any{
		"source":       source,
		"materialized": result,
		"result":       progResult.Summary,
	})
}

func (s *Server) handleBenchmarkFunctor(w http.ResponseWriter, r *http.Request) {
	suiteURN := strings.TrimPrefix(r.URL.Path, "/functor/benchmark/")
	if suiteURN == "" {
		// Return all suites.
		b := functor.Benchmark{}
		result, err := b.Project(s.inspect.State())
		if err != nil {
			writeError(w, http.StatusInternalServerError, err.Error())
			return
		}
		writeJSON(w, http.StatusOK, result)
		return
	}
	b := functor.Benchmark{}
	result, err := b.ProjectSuite(s.inspect.State(), suiteURN)
	if err != nil {
		writeError(w, http.StatusNotFound, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, result)
}

type portInventoryPair struct {
	SourceType cat.TypeID `json:"source_type"`
	SourcePort cat.Port   `json:"source_port"`
	TargetType cat.TypeID `json:"target_type"`
	TargetPort cat.Port   `json:"target_port"`
}

type portInventoryResponse struct {
	SourceType cat.TypeID          `json:"source_type,omitempty"`
	PairCount  int                 `json:"pair_count"`
	Pairs      []portInventoryPair `json:"pairs"`
}

type bindingFamily struct {
	FamilyID        string       `json:"family_id"`
	SourcePort      cat.Port     `json:"source_port"`
	TargetPort      cat.Port     `json:"target_port"`
	TargetTypeCount int          `json:"target_type_count"`
	TargetTypes     []cat.TypeID `json:"target_types"`
	PairCount       int          `json:"pair_count"`
}

type bindingCategoryResponse struct {
	SourceType  cat.TypeID      `json:"source_type"`
	SourcePort  cat.Port        `json:"source_port,omitempty"`
	FamilyCount int             `json:"family_count"`
	Families    []bindingFamily `json:"families"`
}

type portFunctorMapping struct {
	FromFamily     string     `json:"from_family"`
	ToFamily       string     `json:"to_family"`
	ComposedFamily string     `json:"composed_family"`
	SourceType     cat.TypeID `json:"source_type"`
	SourcePort     cat.Port   `json:"source_port"`
	ViaType        cat.TypeID `json:"via_type"`
	ViaPort        cat.Port   `json:"via_port"`
	TargetType     cat.TypeID `json:"target_type"`
	TargetPort     cat.Port   `json:"target_port"`
}

type portFunctorResponse struct {
	SourceType   cat.TypeID           `json:"source_type"`
	SourcePort   cat.Port             `json:"source_port,omitempty"`
	MappingCount int                  `json:"mapping_count"`
	Mappings     []portFunctorMapping `json:"mappings"`
}

type pipelineKernelMetrics struct {
	KernelURN    cat.URN    `json:"kernel_urn"`
	TypeID       cat.TypeID `json:"type_id"`
	Incoming     int        `json:"incoming"`
	Outgoing     int        `json:"outgoing"`
	Internal     int        `json:"internal"`
	Boundary     int        `json:"boundary"`
	Completeness float64    `json:"completeness"`
	Curvature    float64    `json:"curvature"`
}

func (s *Server) handlePipelineMetricsFunctor(w http.ResponseWriter, r *http.Request) {
	state := s.inspect.State()
	filterKernel := cat.URN(strings.TrimSpace(r.URL.Query().Get("kernel_urn")))

	kernels := make([]cat.Node, 0)
	for _, n := range state.Nodes {
		if !isBridgeKernelNode(n) {
			continue
		}
		if filterKernel != "" && n.URN != filterKernel {
			continue
		}
		kernels = append(kernels, n)
	}

	if filterKernel != "" && len(kernels) == 0 {
		writeError(w, http.StatusNotFound, fmt.Sprintf("kernel node %s not found or not a kernel type", filterKernel))
		return
	}

	sort.Slice(kernels, func(i, j int) bool { return kernels[i].URN < kernels[j].URN })

	metrics := make([]pipelineKernelMetrics, 0, len(kernels))
	var totalCurvature float64
	var totalCompleteness float64
	for _, k := range kernels {
		m := pipelineKernelMetrics{KernelURN: k.URN, TypeID: k.TypeID}
		for _, wire := range state.Wires {
			touchesSource := wire.SourceURN == k.URN
			touchesTarget := wire.TargetURN == k.URN
			if !touchesSource && !touchesTarget {
				continue
			}

			if touchesSource {
				m.Outgoing++
			}
			if touchesTarget {
				m.Incoming++
			}

			other := wire.TargetURN
			if touchesTarget {
				other = wire.SourceURN
			}
			otherNode, ok := state.Nodes[other]
			if ok && isBridgeKernelNode(otherNode) {
				m.Internal++
			} else {
				m.Boundary++
			}
		}

		totalEdges := m.Incoming + m.Outgoing
		if totalEdges > 0 {
			m.Completeness = float64(m.Boundary) / float64(totalEdges)
			if m.Completeness > 1 {
				m.Completeness = 1
			}
			m.Curvature = float64(m.Internal-m.Boundary) / float64(totalEdges)
		} else {
			m.Completeness = 0
			m.Curvature = 0
		}

		totalCurvature += m.Curvature
		totalCompleteness += m.Completeness
		metrics = append(metrics, m)
	}

	avgCurvature := 0.0
	avgCompleteness := 0.0
	if len(metrics) > 0 {
		avgCurvature = totalCurvature / float64(len(metrics))
		avgCompleteness = totalCompleteness / float64(len(metrics))
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"kernel_count":     len(metrics),
		"avg_curvature":    avgCurvature,
		"avg_completeness": avgCompleteness,
		"by_kernel":        metrics,
	})
}

func (s *Server) handlePortInventoryFunctor(w http.ResponseWriter, r *http.Request) {
	reg := s.inspect.Registry()
	if reg == nil {
		writeJSON(w, http.StatusOK, map[string]any{"status": "no registry loaded"})
		return
	}

	collect := func(srcType cat.TypeID) []portInventoryPair {
		spec, ok := reg.Types[srcType]
		if !ok {
			return nil
		}
		var pairs []portInventoryPair
		for srcPort, ps := range spec.Ports {
			if ps.Direction != "out" {
				continue
			}
			for _, tgt := range ps.Targets {
				pairs = append(pairs, portInventoryPair{
					SourceType: srcType,
					SourcePort: srcPort,
					TargetType: tgt.TypeID,
					TargetPort: tgt.Port,
				})
			}
		}
		sort.Slice(pairs, func(i, j int) bool {
			ai := string(pairs[i].SourceType) + "/" + string(pairs[i].SourcePort) + "/" + string(pairs[i].TargetType) + "/" + string(pairs[i].TargetPort)
			aj := string(pairs[j].SourceType) + "/" + string(pairs[j].SourcePort) + "/" + string(pairs[j].TargetType) + "/" + string(pairs[j].TargetPort)
			return ai < aj
		})
		return pairs
	}

	if src := strings.TrimSpace(r.URL.Query().Get("src_type")); src != "" {
		srcType := cat.TypeID(src)
		if _, ok := reg.Types[srcType]; !ok {
			writeError(w, http.StatusNotFound, fmt.Sprintf("unknown source type: %s", src))
			return
		}
		pairs := collect(srcType)
		writeJSON(w, http.StatusOK, portInventoryResponse{
			SourceType: srcType,
			PairCount:  len(pairs),
			Pairs:      pairs,
		})
		return
	}

	var all []portInventoryPair
	for srcType := range reg.Types {
		all = append(all, collect(srcType)...)
	}
	sort.Slice(all, func(i, j int) bool {
		ai := string(all[i].SourceType) + "/" + string(all[i].SourcePort) + "/" + string(all[i].TargetType) + "/" + string(all[i].TargetPort)
		aj := string(all[j].SourceType) + "/" + string(all[j].SourcePort) + "/" + string(all[j].TargetType) + "/" + string(all[j].TargetPort)
		return ai < aj
	})

	writeJSON(w, http.StatusOK, portInventoryResponse{
		PairCount: len(all),
		Pairs:     all,
	})
}

func (s *Server) handleBindingCategoryFunctor(w http.ResponseWriter, r *http.Request) {
	reg := s.inspect.Registry()
	if reg == nil {
		writeJSON(w, http.StatusOK, map[string]any{"status": "no registry loaded"})
		return
	}

	src := strings.TrimSpace(r.URL.Query().Get("src_type"))
	if src == "" {
		writeError(w, http.StatusBadRequest, "src_type is required")
		return
	}
	srcType := cat.TypeID(src)
	spec, ok := reg.Types[srcType]
	if !ok {
		writeError(w, http.StatusNotFound, fmt.Sprintf("unknown source type: %s", src))
		return
	}

	filterPort := cat.Port(strings.TrimSpace(r.URL.Query().Get("source_port")))
	groups := map[string]*bindingFamily{}
	for srcPort, ps := range spec.Ports {
		if ps.Direction != "out" {
			continue
		}
		if filterPort != "" && srcPort != filterPort {
			continue
		}
		for _, tgt := range ps.Targets {
			key := string(srcPort) + "->" + string(tgt.Port)
			fam, exists := groups[key]
			if !exists {
				fam = &bindingFamily{
					FamilyID:   key,
					SourcePort: srcPort,
					TargetPort: tgt.Port,
				}
				groups[key] = fam
			}
			fam.PairCount++
			seen := false
			for _, tt := range fam.TargetTypes {
				if tt == tgt.TypeID {
					seen = true
					break
				}
			}
			if !seen {
				fam.TargetTypes = append(fam.TargetTypes, tgt.TypeID)
			}
		}
	}

	families := make([]bindingFamily, 0, len(groups))
	for _, fam := range groups {
		sort.Slice(fam.TargetTypes, func(i, j int) bool {
			return string(fam.TargetTypes[i]) < string(fam.TargetTypes[j])
		})
		fam.TargetTypeCount = len(fam.TargetTypes)
		families = append(families, *fam)
	}
	sort.Slice(families, func(i, j int) bool { return families[i].FamilyID < families[j].FamilyID })

	writeJSON(w, http.StatusOK, bindingCategoryResponse{
		SourceType:  srcType,
		SourcePort:  filterPort,
		FamilyCount: len(families),
		Families:    families,
	})
}

func (s *Server) handlePortFunctor(w http.ResponseWriter, r *http.Request) {
	reg := s.inspect.Registry()
	if reg == nil {
		writeJSON(w, http.StatusOK, map[string]any{"status": "no registry loaded"})
		return
	}

	srcType := cat.TypeID(strings.TrimSpace(r.URL.Query().Get("src_type")))
	if srcType == "" {
		writeError(w, http.StatusBadRequest, "src_type is required")
		return
	}
	if _, ok := reg.Types[srcType]; !ok {
		writeError(w, http.StatusNotFound, fmt.Sprintf("unknown src_type: %s", srcType))
		return
	}

	filterPort := cat.Port(strings.TrimSpace(r.URL.Query().Get("source_port")))

	collect := func(t cat.TypeID) []portInventoryPair {
		spec, ok := reg.Types[t]
		if !ok {
			return nil
		}
		var pairs []portInventoryPair
		for srcPort, ps := range spec.Ports {
			if ps.Direction != "out" {
				continue
			}
			for _, tgt := range ps.Targets {
				pairs = append(pairs, portInventoryPair{
					SourceType: t,
					SourcePort: srcPort,
					TargetType: tgt.TypeID,
					TargetPort: tgt.Port,
				})
			}
		}
		return pairs
	}

	first := collect(srcType)
	if filterPort != "" {
		filtered := make([]portInventoryPair, 0, len(first))
		for _, p := range first {
			if p.SourcePort == filterPort {
				filtered = append(filtered, p)
			}
		}
		first = filtered
	}

	secondByType := map[cat.TypeID][]portInventoryPair{}
	var mappings []portFunctorMapping
	for _, p1 := range first {
		second, ok := secondByType[p1.TargetType]
		if !ok {
			second = collect(p1.TargetType)
			secondByType[p1.TargetType] = second
		}
		for _, p2 := range second {
			if p1.TargetPort != p2.SourcePort {
				continue
			}
			mappings = append(mappings, portFunctorMapping{
				FromFamily:     string(p1.SourcePort) + "->" + string(p1.TargetPort),
				ToFamily:       string(p2.SourcePort) + "->" + string(p2.TargetPort),
				ComposedFamily: string(p1.SourcePort) + "->" + string(p2.TargetPort),
				SourceType:     p1.SourceType,
				SourcePort:     p1.SourcePort,
				ViaType:        p1.TargetType,
				ViaPort:        p1.TargetPort,
				TargetType:     p2.TargetType,
				TargetPort:     p2.TargetPort,
			})
		}
	}

	sort.Slice(mappings, func(i, j int) bool {
		a, b := mappings[i], mappings[j]
		if a.SourceType != b.SourceType {
			return a.SourceType < b.SourceType
		}
		if a.SourcePort != b.SourcePort {
			return a.SourcePort < b.SourcePort
		}
		if a.ViaType != b.ViaType {
			return a.ViaType < b.ViaType
		}
		if a.ViaPort != b.ViaPort {
			return a.ViaPort < b.ViaPort
		}
		if a.TargetType != b.TargetType {
			return a.TargetType < b.TargetType
		}
		return a.TargetPort < b.TargetPort
	})

	writeJSON(w, http.StatusOK, portFunctorResponse{
		SourceType:   srcType,
		SourcePort:   filterPort,
		MappingCount: len(mappings),
		Mappings:     mappings,
	})
}

func (s *Server) handleExplorer(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Write(explorerHTML)
}

func (s *Server) handleUIFunctor(w http.ResponseWriter, r *http.Request) {
	lens := functor.UILens{}
	result, err := lens.Project(s.inspect.State())
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, result)
}

func (s *Server) handleCalendarFunctor(w http.ResponseWriter, r *http.Request) {
	cal := functor.Calendar{}
	result, err := cal.Project(s.inspect.State())
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}

	proj, ok := result.(functor.CalendarProjection)
	if !ok {
		writeError(w, http.StatusInternalServerError, "invalid calendar projection type")
		return
	}

	if strings.EqualFold(r.URL.Query().Get("format"), "ical") {
		w.Header().Set("Content-Type", "text/calendar; charset=utf-8")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(functor.RenderICalendar(proj, "moos-calendar")))
		return
	}

	writeJSON(w, http.StatusOK, proj)
}

// --- Helpers ---

func writeJSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	enc.Encode(data)
}

func writeJSONCompact(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]string{"error": msg})
}
