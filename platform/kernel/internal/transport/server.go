// Package transport provides the HTTP API — the only external interface to the kernel.
// All mutations go through the four invariant NTs via the shell.Runtime.
// Read paths are direct GraphState projections (functor deferred).
package transport

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/hydration"
	"moos/platform/kernel/internal/shell"
)

// Server is the HTTP transport layer.
type Server struct {
	runtime *shell.Runtime
	kbRoot  string // path to knowledge-base root; empty when --kb not supplied
	mux     *http.ServeMux
	srv     *http.Server
}

// NewServer creates a new HTTP server bound to the given runtime.
// kbRoot is the path to the knowledge-base root directory; pass "" when
// the --kb flag was not supplied (source-based materialize will return 501).
func NewServer(runtime *shell.Runtime, kbRoot string) *Server {
	s := &Server{
		runtime: runtime,
		kbRoot:  kbRoot,
		mux:     http.NewServeMux(),
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
	s.mux.HandleFunc("GET /semantics/registry", s.handleRegistry)
	s.mux.HandleFunc("POST /hydration/materialize", s.handleMaterialize)
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
	writeJSON(w, http.StatusOK, map[string]any{
		"status":    "ok",
		"nodes":     len(s.runtime.Nodes()),
		"wires":     len(s.runtime.Wires()),
		"log_depth": s.runtime.LogLen(),
	})
}

func (s *Server) handleState(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, s.runtime.State())
}

func (s *Server) handleNodes(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, s.runtime.Nodes())
}

func (s *Server) handleNodeByURN(w http.ResponseWriter, r *http.Request) {
	urn := cat.URN(strings.TrimPrefix(r.URL.Path, "/state/nodes/"))
	if urn == "" {
		writeError(w, http.StatusBadRequest, "missing URN")
		return
	}
	node, ok := s.runtime.Node(urn)
	if !ok {
		writeError(w, http.StatusNotFound, fmt.Sprintf("node %s not found", urn))
		return
	}
	writeJSON(w, http.StatusOK, node)
}

func (s *Server) handleWires(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, s.runtime.Wires())
}

func (s *Server) handleOutgoingWires(w http.ResponseWriter, r *http.Request) {
	urn := cat.URN(strings.TrimPrefix(r.URL.Path, "/state/wires/outgoing/"))
	if urn == "" {
		writeError(w, http.StatusBadRequest, "missing URN")
		return
	}
	writeJSON(w, http.StatusOK, s.runtime.OutgoingWires(urn))
}

func (s *Server) handleIncomingWires(w http.ResponseWriter, r *http.Request) {
	urn := cat.URN(strings.TrimPrefix(r.URL.Path, "/state/wires/incoming/"))
	if urn == "" {
		writeError(w, http.StatusBadRequest, "missing URN")
		return
	}
	writeJSON(w, http.StatusOK, s.runtime.IncomingWires(urn))
}

func (s *Server) handlePostMorphism(w http.ResponseWriter, r *http.Request) {
	var env cat.Envelope
	if err := json.NewDecoder(r.Body).Decode(&env); err != nil {
		writeError(w, http.StatusBadRequest, fmt.Sprintf("invalid JSON: %v", err))
		return
	}
	result, err := s.runtime.Apply(env)
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
	result, err := s.runtime.ApplyProgram(prog)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, result)
}

func (s *Server) handleLog(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, s.runtime.Log())
}

func (s *Server) handleRegistry(w http.ResponseWriter, r *http.Request) {
	reg := s.runtime.Registry()
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
	reg := s.runtime.Registry()

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

	progResult, err := s.runtime.ApplyProgram(result.Program)
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

	reg := s.runtime.Registry()
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

	progResult, err := s.runtime.ApplyProgram(result.Program)
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

// --- Helpers ---

func writeJSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	enc.Encode(data)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]string{"error": msg})
}
