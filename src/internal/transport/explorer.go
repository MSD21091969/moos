package transport

import (
	"encoding/json"
	"fmt"
	"net/http"
)

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
	fmt.Fprintf(w, explorerHTML, string(uiData))
}

const explorerHTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>mo:os — Explorer (UI_Lens)</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, sans-serif; background: #0d1117; color: #c9d1d9; }
  header { padding: 12px 20px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 16px; font-weight: 600; }
  header .badge { font-size: 11px; background: #238636; padding: 2px 8px; border-radius: 12px; }
  .container { display: flex; height: calc(100vh - 48px); }
  .sidebar { width: 320px; overflow-y: auto; border-right: 1px solid #30363d; padding: 12px; }
  .sidebar h2 { font-size: 13px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
  .node-card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 10px; margin-bottom: 8px; cursor: pointer; }
  .node-card:hover { border-color: #58a6ff; }
  .node-card .urn { font-size: 12px; font-family: monospace; color: #58a6ff; word-break: break-all; }
  .node-card .kind { font-size: 11px; color: #8b949e; }
  .canvas-area { flex: 1; position: relative; overflow: hidden; }
  svg { width: 100%%; height: 100%%; }
  .node circle { fill: #238636; stroke: #3fb950; stroke-width: 2; }
  .node text { fill: #c9d1d9; font-size: 10px; font-family: monospace; }
  .edge line { stroke: #30363d; stroke-width: 1.5; }
  .edge text { fill: #8b949e; font-size: 9px; }
  .stats { font-size: 11px; color: #8b949e; margin-bottom: 12px; }
</style>
</head>
<body>
<header>
  <h1>mo:os Explorer</h1>
  <span class="badge">UI_Lens</span>
  <span class="badge" style="background:#1f6feb">read-only</span>
</header>
<div class="container">
  <div class="sidebar" id="sidebar">
    <div class="stats" id="stats"></div>
    <h2>Nodes</h2>
    <div id="node-list"></div>
  </div>
  <div class="canvas-area">
    <svg id="graph"></svg>
  </div>
</div>
<script>
const data = %s;
const stats = document.getElementById('stats');
const nodeList = document.getElementById('node-list');
const svg = document.getElementById('graph');

stats.textContent = data.nodes.length + ' nodes, ' + data.edges.length + ' edges';

data.nodes.forEach(n => {
  const card = document.createElement('div');
  card.className = 'node-card';
  card.innerHTML = '<div class="urn">' + escapeHtml(n.id) + '</div><div class="kind">' + escapeHtml(n.kind) + '</div>';
  nodeList.appendChild(card);
});

// Render edges as SVG lines
data.edges.forEach(e => {
  const src = data.nodes.find(n => n.id === e.source);
  const tgt = data.nodes.find(n => n.id === e.target);
  if (!src || !tgt) return;
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.setAttribute('class', 'edge');
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  line.setAttribute('x1', src.x + 200); line.setAttribute('y1', src.y + 60);
  line.setAttribute('x2', tgt.x + 200); line.setAttribute('y2', tgt.y + 60);
  g.appendChild(line);
  svg.appendChild(g);
});

// Render nodes as SVG circles
data.nodes.forEach(n => {
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.setAttribute('class', 'node');
  g.setAttribute('transform', 'translate(' + (n.x + 200) + ',' + (n.y + 60) + ')');
  const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  circle.setAttribute('r', 8);
  g.appendChild(circle);
  const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  text.setAttribute('dx', 12); text.setAttribute('dy', 4);
  text.textContent = n.id.split(':').pop();
  g.appendChild(text);
  svg.appendChild(g);
});

function escapeHtml(s) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(s));
  return div.innerHTML;
}
</script>
</body>
</html>`
