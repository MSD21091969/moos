package httpapi

import (
	_ "embed"
	"net/http"
	"os"
	"path/filepath"
)

//go:embed explorer.html
var explorerHTML []byte

func explorerDemoCandidates() []string {
	return []string{
		filepath.FromSlash("examples/explorer-demo.materialize.json"),
		filepath.FromSlash("../examples/explorer-demo.materialize.json"),
		filepath.FromSlash("../../examples/explorer-demo.materialize.json"),
		filepath.FromSlash("platform/kernel/examples/explorer-demo.materialize.json"),
	}
}

func loadExplorerDemoPayload() ([]byte, error) {
	for _, candidate := range explorerDemoCandidates() {
		payload, err := os.ReadFile(candidate)
		if err == nil {
			return payload, nil
		}
	}
	return nil, os.ErrNotExist
}

func (server *Server) handleExplorer(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	writer.Header().Set("Content-Type", "text/html; charset=utf-8")
	writer.WriteHeader(http.StatusOK)
	_, _ = writer.Write(explorerHTML)
}

func (server *Server) handleExplorerDemoExample(writer http.ResponseWriter, request *http.Request) {
	if request.Method != http.MethodGet {
		writeError(writer, http.StatusMethodNotAllowed, "method not allowed")
		return
	}
	payload, err := loadExplorerDemoPayload()
	if err != nil {
		writeError(writer, http.StatusNotFound, "explorer demo example not found")
		return
	}
	writer.Header().Set("Content-Type", "application/json; charset=utf-8")
	writer.WriteHeader(http.StatusOK)
	_, _ = writer.Write(payload)
}
