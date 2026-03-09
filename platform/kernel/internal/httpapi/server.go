package httpapi

import (
	"encoding/json"
	"errors"
	"net/http"
	"strings"

	"moos/platform/kernel/internal/core"
	"moos/platform/kernel/internal/hydration"
	"moos/platform/kernel/internal/shell"
)

type Server struct {
	runtime *shell.Runtime
	mux     *http.ServeMux
}

func New(runtime *shell.Runtime) *Server {
	server := &Server{
		runtime: runtime,
		mux:     http.NewServeMux(),
	}
	server.routes()
	return server
}

func (server *Server) Handler() http.Handler {
	return server.mux
}

func (server *Server) routes() {
	server.mux.HandleFunc("/", server.handleExplorer)
	server.mux.HandleFunc("/explorer", server.handleExplorer)
	server.mux.HandleFunc("/healthz", server.handleHealth)
	server.mux.HandleFunc("/hydration/examples/explorer-demo", server.handleExplorerDemoExample)
	server.mux.HandleFunc("/morphisms", server.handleMorphisms)
	server.mux.HandleFunc("/programs", server.handlePrograms)
	server.mux.HandleFunc("/hydration/materialize", server.handleMaterialize)
	server.mux.HandleFunc("/semantics/registry", server.handleRegistry)
	server.mux.HandleFunc("/state", server.handleState)
	server.mux.HandleFunc("/state/nodes", server.handleNodes)
	server.mux.HandleFunc("/state/nodes/", server.handleNode)
	server.mux.HandleFunc("/state/wires", server.handleWires)
	server.mux.HandleFunc("/state/traversal/outgoing/", server.handleOutgoing)
	server.mux.HandleFunc("/state/traversal/incoming/", server.handleIncoming)
	server.mux.HandleFunc("/log", server.handleLog)
}

func (server *Server) handleHealth(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	writeJSON(writer, http.StatusOK, map[string]any{
		"status":  "ok",
		"summary": server.runtime.Summary(),
	})
}

func (server *Server) handleMorphisms(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodPost {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	defer request.Body.Close()
	var envelope core.Envelope
	if err := json.NewDecoder(request.Body).Decode(&envelope); err != nil {
		writeError(writer, http.StatusBadRequest, "invalid json body")
		return
	}
	result, err := server.runtime.Apply(envelope)
	if err != nil {
		status := http.StatusBadRequest
		if errors.Is(err, core.ErrVersionConflict) {
			status = http.StatusConflict
		}
		writeJSON(writer, status, map[string]any{
			"error": err.Error(),
		})
		return
	}
	writeJSON(writer, http.StatusAccepted, map[string]any{
		"summary":   result.Summary,
		"node":      result.Node,
		"wire":      result.Wire,
		"persisted": result.Persisted,
		"state":     server.runtime.Summary(),
	})
}

func (server *Server) handlePrograms(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodPost {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	defer request.Body.Close()
	var program core.Program
	if err := json.NewDecoder(request.Body).Decode(&program); err != nil {
		writeError(writer, http.StatusBadRequest, "invalid json body")
		return
	}
	result, err := server.runtime.ApplyProgram(program)
	if err != nil {
		status := http.StatusBadRequest
		if errors.Is(err, core.ErrVersionConflict) {
			status = http.StatusConflict
		}
		writeJSON(writer, status, map[string]any{
			"error": err.Error(),
		})
		return
	}
	writeJSON(writer, http.StatusAccepted, map[string]any{
		"summary":   result.Summary,
		"results":   result.Results,
		"persisted": result.Persisted,
		"state":     server.runtime.Summary(),
	})
}

func (server *Server) handleMaterialize(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodPost {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	defer request.Body.Close()
	var authored hydration.MaterializeRequest
	if err := json.NewDecoder(request.Body).Decode(&authored); err != nil {
		writeError(writer, http.StatusBadRequest, "invalid json body")
		return
	}
	materialized, err := hydration.Materialize(authored, server.runtime.Registry())
	if err != nil {
		writeJSON(writer, http.StatusBadRequest, map[string]any{"error": err.Error()})
		return
	}
	if !authored.Apply {
		writeJSON(writer, http.StatusOK, materialized)
		return
	}
	result, err := server.runtime.ApplyProgram(materialized.Program)
	if err != nil {
		status := http.StatusBadRequest
		if errors.Is(err, core.ErrVersionConflict) {
			status = http.StatusConflict
		}
		writeJSON(writer, status, map[string]any{"error": err.Error()})
		return
	}
	writeJSON(writer, http.StatusAccepted, map[string]any{
		"summary": materialized.Summary,
		"stages":  materialized.Stages,
		"program": materialized.Program,
		"applied": result,
		"state":   server.runtime.Summary(),
	})
}

func (server *Server) handleRegistry(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	registry := server.runtime.Registry()
	if registry == nil {
		writeError(writer, http.StatusNotFound, "semantic registry not loaded")
		return
	}
	writeJSON(writer, http.StatusOK, registry)
}

func (server *Server) handleState(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	writeJSON(writer, http.StatusOK, map[string]any{
		"summary": server.runtime.Summary(),
		"graph":   server.runtime.Snapshot(),
	})
}

func (server *Server) handleNodes(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	kind := request.URL.Query().Get("kind")
	stratum := request.URL.Query().Get("stratum")
	writeJSON(writer, http.StatusOK, map[string]any{
		"nodes": server.runtime.Nodes(kind, stratum),
	})
}

func (server *Server) handleNode(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	urn := strings.TrimPrefix(request.URL.Path, "/state/nodes/")
	if urn == "" {
		writeError(writer, http.StatusBadRequest, "node urn is required")
		return
	}
	node, ok := server.runtime.Node(urn)
	if !ok {
		writeError(writer, http.StatusNotFound, "node not found")
		return
	}
	writeJSON(writer, http.StatusOK, node)
}

func (server *Server) handleWires(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	writeJSON(writer, http.StatusOK, server.runtime.Wires())
}

func (server *Server) handleOutgoing(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	urn := strings.TrimPrefix(request.URL.Path, "/state/traversal/outgoing/")
	if urn == "" {
		writeError(writer, http.StatusBadRequest, "node urn is required")
		return
	}
	writeJSON(writer, http.StatusOK, map[string]any{
		"urn":   urn,
		"wires": server.runtime.OutgoingWires(urn),
	})
}

func (server *Server) handleIncoming(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	urn := strings.TrimPrefix(request.URL.Path, "/state/traversal/incoming/")
	if urn == "" {
		writeError(writer, http.StatusBadRequest, "node urn is required")
		return
	}
	writeJSON(writer, http.StatusOK, map[string]any{
		"urn":   urn,
		"wires": server.runtime.IncomingWires(urn),
	})
}

func (server *Server) handleLog(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	writeJSON(writer, http.StatusOK, server.runtime.LogEntries())
}

func writeError(writer http.ResponseWriter, status int, message string) {
	writeJSON(writer, status, map[string]string{"error": message})
}

func writeJSON(writer http.ResponseWriter, status int, payload any) {
	writer.Header().Set("Content-Type", "application/json")
	writer.WriteHeader(status)
	_ = json.NewEncoder(writer).Encode(payload)
}
