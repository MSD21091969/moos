#!/usr/bin/env bash
# mo:os Kernel — 8-step interactive demo (bash)
#
# Walks through the mo:os kernel HTTP API and MCP bridge.
# Run this in a second terminal while the kernel is running.
#
# Usage:
#   ./platform/kernel/examples/demo.sh [--non-interactive] [--base URL] [--mcp URL]
#
# Start the kernel first:
#   cd platform/kernel
#   go run ./cmd/moos --kb "../../.agent/knowledge_base" --hydrate

set -euo pipefail

# ── defaults ──────────────────────────────────────────────────────────────────

BASE="${MOOS_BASE:-http://localhost:8000}"
MCP="${MOOS_MCP:-http://localhost:8080}"
NON_INTERACTIVE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --non-interactive) NON_INTERACTIVE=true; shift ;;
        --base) BASE="$2"; shift 2 ;;
        --mcp)  MCP="$2";  shift 2 ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

# ── helpers ───────────────────────────────────────────────────────────────────

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
GRAY='\033[0;90m'
WHITE='\033[0;97m'
RED='\033[0;31m'
NC='\033[0m'

banner() {
    local step="$1" title="$2"
    echo ""
    printf "${CYAN}%s${NC}\n" "$(printf '%.0s=' {1..60})"
    printf "${CYAN}  STEP %s — %s${NC}\n" "$step" "$title"
    printf "${CYAN}%s${NC}\n" "$(printf '%.0s=' {1..60})"
}

pause_step() {
    local prompt="${1:-Press Enter to continue...}"
    if [[ "$NON_INTERACTIVE" == "false" ]]; then
        echo ""
        printf "${GRAY}%s${NC}" "$prompt"
        read -r _
    fi
}

jprint() {
    # Pretty-print JSON — prefer python3, fall back to cat
    if command -v python3 &>/dev/null; then
        python3 -m json.tool 2>/dev/null || cat
    else
        cat
    fi
}

kget() {
    curl -sf "$BASE$1"
}

kpost() {
    local path="$1" body="$2"
    curl -sf -X POST "$BASE$path" \
        -H "Content-Type: application/json" \
        -d "$body"
}

# ── preflight ─────────────────────────────────────────────────────────────────

echo ""
printf "${GREEN}mo:os Kernel Demo${NC}\n"
printf "${GRAY}Kernel : %s${NC}\n" "$BASE"
printf "${GRAY}MCP    : %s${NC}\n" "$MCP"

if ! kget "/healthz" &>/dev/null; then
    echo ""
    printf "${RED}ERROR: Cannot reach kernel at %s${NC}\n" "$BASE"
    printf "${YELLOW}Start the kernel first:${NC}\n"
    printf "${YELLOW}  cd platform/kernel${NC}\n"
    printf "${YELLOW}  go run ./cmd/moos --kb '../../.agent/knowledge_base' --hydrate${NC}\n"
    exit 1
fi

pause_step "Kernel is reachable. Press Enter to start the demo..."

# ── STEP 1 — Health check ────────────────────────────────────────────────────

banner "1" "Health check"
printf "${YELLOW}  GET %s/healthz${NC}\n" "$BASE"

health="$(kget "/healthz")"
echo "$health" | jprint

nodes_count="$(echo "$health" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("nodes","?"))' 2>/dev/null || echo "?")"
wires_count="$(echo "$health" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("wires","?"))' 2>/dev/null || echo "?")"

echo ""
printf "${GREEN}  nodes : %s${NC}\n" "$nodes_count"
printf "${GREEN}  wires : %s${NC}\n" "$wires_count"

pause_step

# ── STEP 2 — Full graph state ─────────────────────────────────────────────────

banner "2" "Full graph state"
printf "${YELLOW}  GET %s/state${NC}\n" "$BASE"

state="$(kget "/state")"
n="$(echo "$state" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d.get("nodes",[])))' 2>/dev/null || echo "?")"
w="$(echo "$state" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d.get("wires",[])))' 2>/dev/null || echo "?")"

printf "${GREEN}  nodes : %s${NC}\n" "$n"
printf "${GREEN}  wires : %s${NC}\n" "$w"
printf "${GRAY}  (Full response omitted — large payload. Use /state/nodes or /state/wires.)${NC}\n"

pause_step

# ── STEP 3 — Node listing ────────────────────────────────────────────────────

banner "3" "Node listing"
printf "${YELLOW}  GET %s/state/nodes${NC}\n" "$BASE"

nodes_json="$(kget "/state/nodes")"

echo ""
printf "${GRAY}  First 10 nodes:${NC}\n"
echo "$nodes_json" | python3 - << 'EOF'
import sys, json
nodes = json.load(sys.stdin)
for n in nodes[:10]:
    urn     = n.get("urn", "")
    kind    = n.get("kind", "")
    stratum = n.get("stratum", "")
    s_tag   = f"  S{stratum}" if stratum else ""
    print(f"  {urn:<42}  [{kind}]{s_tag}")
rest = len(nodes) - 10
if rest > 0:
    print(f"  ... and {rest} more")
EOF

pause_step

# ── STEP 4 — Single node lookup ───────────────────────────────────────────────

banner "4" "Single node lookup"

KERNEL_URN="urn:moos:kernel:wave-0"
printf "${YELLOW}  GET %s/state/nodes/%s${NC}\n" "$BASE" "$KERNEL_URN"

if node_json="$(kget "/state/nodes/$KERNEL_URN" 2>/dev/null)"; then
    echo "$node_json" | jprint
else
    first_urn="$(echo "$nodes_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)[0]["urn"])' 2>/dev/null || echo "")"
    if [[ -n "$first_urn" ]]; then
        printf "${GRAY}  (Kernel URN not found; using first node: %s)${NC}\n" "$first_urn"
        kget "/state/nodes/$first_urn" | jprint
    else
        printf "${YELLOW}  No nodes found.${NC}\n"
    fi
fi

pause_step

# ── STEP 5 — Explorer UI ──────────────────────────────────────────────────────

banner "5" "Explorer UI"

echo ""
printf "${WHITE}  The Explorer is a read-only S4 functor projection of the graph.${NC}\n"
printf "${WHITE}  It renders all 21 node kinds as colored SVG circles, with wire${NC}\n"
printf "${WHITE}  edges, sidebar cards, and kind/stratum filter toggles.${NC}\n"
echo ""
printf "${GREEN}  URL: %s/explorer${NC}\n" "$BASE"
echo ""

if ui_json="$(kget "/functor/ui" 2>/dev/null)"; then
    un="$(echo "$ui_json" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d.get("nodes",[])))' 2>/dev/null || echo "?")"
    ue="$(echo "$ui_json" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d.get("edges",[])))' 2>/dev/null || echo "?")"
    printf "${GRAY}  /functor/ui : %s nodes, %s edges${NC}\n" "$un" "$ue"
else
    printf "${YELLOW}  /functor/ui not reachable (Explorer may still render via /explorer)${NC}\n"
fi

echo ""
printf "${GRAY}  Open in browser:${NC}\n"
printf "  %s/explorer\n" "$BASE"

# Try to open browser (best-effort)
if command -v xdg-open &>/dev/null; then
    xdg-open "$BASE/explorer" &>/dev/null &
elif command -v open &>/dev/null; then
    open "$BASE/explorer" &>/dev/null &
fi

pause_step "Explorer URL printed. Press Enter to continue..."

# ── STEP 6 — Apply a morphism ─────────────────────────────────────────────────

banner "6" "Apply a morphism"

RAND="$((RANDOM % 9999))"
DEMO_URN="urn:demo:agent:hello-world-${RAND}"
printf "${YELLOW}  POST %s/morphisms  (ADD envelope)${NC}\n" "$BASE"
printf "${GRAY}  URN : %s${NC}\n" "$DEMO_URN"

envelope_body="$(cat << EOF
{
  "type":    "ADD",
  "urn":     "$DEMO_URN",
  "kind":    "Agent",
  "stratum": "S2",
  "payload": { "label": "Hello World Agent", "version": "0.1.0", "demo": true },
  "metadata": { "created_by": "demo.sh", "step": 6 }
}
EOF
)"

result="$(kpost "/morphisms" "$envelope_body")"
echo "$result" | jprint

echo ""
printf "${GRAY}  Verifying via /state/nodes lookup...${NC}\n"
if verify="$(kget "/state/nodes/$DEMO_URN" 2>/dev/null)"; then
    kind_v="$(echo "$verify" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("kind","?"))' 2>/dev/null || echo "?")"
    stratum_v="$(echo "$verify" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("stratum","?"))' 2>/dev/null || echo "?")"
    printf "${GREEN}  ✓ Node created: kind=%s  stratum=%s${NC}\n" "$kind_v" "$stratum_v"
else
    printf "${YELLOW}  Node lookup returned no result.${NC}\n"
fi

pause_step

# ── STEP 7 — Scoped subgraph ──────────────────────────────────────────────────

banner "7" "Scoped subgraph"

ACTOR="urn:moos:kernel:self"
printf "${YELLOW}  GET %s/state/scope/%s${NC}\n" "$BASE" "$ACTOR"

if scope_json="$(kget "/state/scope/$ACTOR" 2>/dev/null)"; then
    sn="$(echo "$scope_json" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d.get("nodes",[])))' 2>/dev/null || echo "?")"
    sw="$(echo "$scope_json" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d.get("wires",[])))' 2>/dev/null || echo "?")"
    printf "${GREEN}  nodes in scope : %s${NC}\n" "$sn"
    printf "${GREEN}  wires in scope : %s${NC}\n" "$sw"
    echo ""
    printf "${GRAY}  First 5 scoped nodes:${NC}\n"
    echo "$scope_json" | python3 - << 'EOF'
import sys, json
d = json.load(sys.stdin)
for n in d.get("nodes", [])[:5]:
    urn  = n.get("urn", "")
    kind = n.get("kind", "")
    print(f"  {urn:<40}  [{kind}]")
EOF
else
    printf "${YELLOW}  Scope endpoint not reachable.${NC}\n"
fi

pause_step

# ── STEP 8 — MCP bridge ───────────────────────────────────────────────────────

banner "8" "MCP bridge (JSON-RPC 2.0 over HTTP)"

SESSION="demo-${RANDOM}"
printf "${GRAY}  SSE endpoint : %s/sse${NC}\n" "$MCP"
printf "${GRAY}  Session      : %s${NC}\n" "$SESSION"
echo ""

if ! curl -sf "$MCP/healthz" &>/dev/null; then
    printf "${YELLOW}  WARNING: MCP bridge not reachable at %s/healthz${NC}\n" "$MCP"
    printf "${YELLOW}  The kernel starts MCP on :8080. Check boot logs.${NC}\n"
    pause_step "Press Enter to skip MCP steps..."
else
    mcp_health="$(curl -sf "$MCP/healthz")"
    printf "${GRAY}  MCP healthz: %s${NC}\n" "$mcp_health"

    # tools/list
    echo ""
    printf "${YELLOW}  POST %s/message  (tools/list)${NC}\n" "$MCP"
    list_body='{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

    if list_resp="$(curl -sf -X POST "$MCP/message?sessionId=$SESSION" \
            -H "Content-Type: application/json" -d "$list_body" 2>/dev/null)"; then
        echo "$list_resp" | jprint
    else
        printf "${YELLOW}  (tools/list failed — MCP may require SSE session handshake first)${NC}\n"
    fi

    # tools/call graph_state
    echo ""
    printf "${YELLOW}  POST %s/message  (tools/call → graph_state)${NC}\n" "$MCP"
    call_body='{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"graph_state","arguments":{}}}'

    if call_resp="$(curl -sf -X POST "$MCP/message?sessionId=$SESSION" \
            -H "Content-Type: application/json" -d "$call_body" 2>/dev/null)"; then
        echo "$call_resp" | jprint
        printf "${GREEN}  ✓ MCP tool call succeeded${NC}\n"
    else
        printf "${YELLOW}  (tools/call failed — see note above about SSE session)${NC}\n"
    fi

    echo ""
    printf "${GRAY}  5 tools: graph_state, node_lookup, apply_morphism, scoped_subgraph, benchmark_project${NC}\n"
    printf "${GRAY}  See README.md for the full MCP bridge reference.${NC}\n"
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
printf "${GREEN}%s${NC}\n" "$(printf '%.0s=' {1..60})"
printf "${GREEN}  Demo complete!${NC}\n"
printf "${GREEN}%s${NC}\n" "$(printf '%.0s=' {1..60})"
echo ""
printf "  Kernel HTTP API : %s\n" "$BASE"
printf "  MCP bridge      : %s\n" "$MCP"
printf "  Explorer UI     : %s/explorer\n" "$BASE"
echo ""
echo "  Next steps:"
printf "  - Browse the Explorer  : %s/explorer\n" "$BASE"
echo "  - Read the API docs    : platform/kernel/README.md"
echo "  - Deep dive            : platform/kernel/DEVELOPERS.md"
printf "  - Inspect the log      : curl -s %s/log | python3 -m json.tool\n" "$BASE"
echo "  - Run tests            : cd platform/kernel && go test ./..."
echo ""
