package transport

import (
	"embed"
	"encoding/json"
	"html/template"
	"net/http"
)

//go:embed explorer.html
var explorerFS embed.FS

var explorerTmpl = template.Must(template.ParseFS(explorerFS, "explorer.html"))

// handleExplorer serves the UI_Lens explorer — a self-contained HTML page
// that fetches /functor/ui and renders the graph. Read-only. No morphism capability.
func (s *Server) handleExplorer(w http.ResponseWriter, r *http.Request) {
	state := s.runtime.State()
	var uiData []byte
	if s.uiLens != nil {
		proj := s.uiLens.ProjectUI(state)
		uiData, _ = json.Marshal(proj)
	} else {
		uiData = []byte(`{"nodes":[],"edges":[]}`)
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	explorerTmpl.Execute(w, template.JS(uiData))
}
