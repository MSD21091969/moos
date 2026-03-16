#Requires -Version 5.0
<#
.SYNOPSIS
    mo:os Kernel — 8-step interactive demo (PowerShell)

.DESCRIPTION
    Walks through the mo:os kernel HTTP API and MCP bridge.
    Run this in a second terminal while the kernel is running.

.EXAMPLE
    # Start the kernel first (in another terminal):
    Push-Location platform\kernel
    go run .\cmd\moos --kb "..\..\..\.agent\kb" --hydrate

    # Then run this demo:
    .\platform\kernel\examples\demo.ps1
#>

param(
    [string]$KernelBase = "http://localhost:8000",
    [string]$McpBase    = "http://localhost:8080",
    [switch]$NonInteractive
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── helpers ──────────────────────────────────────────────────────────────────

function Banner([string]$Step, [string]$Title) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "  STEP $Step — $Title" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

function Pause-Step([string]$Prompt = "Press Enter to continue...") {
    if (-not $NonInteractive) {
        Write-Host ""
        Write-Host $Prompt -ForegroundColor DarkGray
        $null = Read-Host
    }
}

function Invoke-KernelGet([string]$Path) {
    Invoke-RestMethod -Uri "$KernelBase$Path"
}

function Invoke-KernelPost([string]$Path, [object]$Body) {
    Invoke-RestMethod -Method Post `
        -Uri "$KernelBase$Path" `
        -Body ($Body | ConvertTo-Json -Depth 10) `
        -ContentType "application/json"
}

function Show-Json([object]$Obj, [int]$Depth = 3) {
    $Obj | ConvertTo-Json -Depth $Depth | Write-Host -ForegroundColor White
}

# ── preflight ─────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "mo:os Kernel Demo" -ForegroundColor Green
Write-Host "Kernel : $KernelBase" -ForegroundColor DarkGray
Write-Host "MCP    : $McpBase" -ForegroundColor DarkGray

try {
    $null = Invoke-KernelGet "/healthz"
} catch {
    Write-Host ""
    Write-Host "ERROR: Cannot reach kernel at $KernelBase" -ForegroundColor Red
    Write-Host "Start the kernel first:" -ForegroundColor Yellow
    Write-Host "  Push-Location platform\kernel" -ForegroundColor Yellow
    Write-Host "  go run .\cmd\moos --kb `"..\..\.agent\kb`" --hydrate" -ForegroundColor Yellow
    exit 1
}

Pause-Step "Kernel is reachable. Press Enter to start the demo..."

# ── STEP 1 — Health check ────────────────────────────────────────────────────

Banner "1" "Health check"
Write-Host "  GET $KernelBase/healthz" -ForegroundColor DarkYellow

$health = Invoke-KernelGet "/healthz"
Show-Json $health

Write-Host ""
Write-Host "  nodes : $($health.nodes)" -ForegroundColor Green
Write-Host "  wires : $($health.wires)" -ForegroundColor Green

Pause-Step

# ── STEP 2 — Full graph state ────────────────────────────────────────────────

Banner "2" "Full graph state"
Write-Host "  GET $KernelBase/state" -ForegroundColor DarkYellow

$state = Invoke-KernelGet "/state"
Write-Host "  nodes : $($state.nodes.Count)" -ForegroundColor Green
Write-Host "  wires : $($state.wires.Count)" -ForegroundColor Green
Write-Host ""
Write-Host "  (Full response omitted — large payload. Use /state/nodes or /state/wires for details.)" -ForegroundColor DarkGray

Pause-Step

# ── STEP 3 — Node listing ────────────────────────────────────────────────────

Banner "3" "Node listing"
Write-Host "  GET $KernelBase/state/nodes" -ForegroundColor DarkYellow

$nodes = Invoke-KernelGet "/state/nodes"

Write-Host ""
Write-Host "  First 10 nodes:" -ForegroundColor DarkGray
$nodes | Select-Object -First 10 | ForEach-Object {
    $stratum = if ($_.stratum) { "  S$($_.stratum)" } else { "" }
    Write-Host ("  {0,-42}  [{1}]{2}" -f $_.urn, $_.kind, $stratum) -ForegroundColor White
}
if ($nodes.Count -gt 10) {
    Write-Host "  ... and $($nodes.Count - 10) more" -ForegroundColor DarkGray
}

Pause-Step

# ── STEP 4 — Single node lookup ──────────────────────────────────────────────

Banner "4" "Single node lookup"

$kernelUrn = "urn:moos:kernel:wave-0"
Write-Host "  GET $KernelBase/state/nodes/$kernelUrn" -ForegroundColor DarkYellow

try {
    $node = Invoke-KernelGet "/state/nodes/$kernelUrn"
    Show-Json $node
} catch {
    # Try first node if the canonical URN doesn't exist
    $firstUrn = $nodes[0].urn
    Write-Host "  (Kernel URN not found; using first node: $firstUrn)" -ForegroundColor DarkGray
    $node = Invoke-KernelGet "/state/nodes/$firstUrn"
    Show-Json $node
}

Pause-Step

# ── STEP 5 — Explorer UI ─────────────────────────────────────────────────────

Banner "5" "Explorer UI"

Write-Host ""
Write-Host "  The Explorer is a read-only S4 functor projection of the graph." -ForegroundColor White
Write-Host "  It renders all 21 node kinds as colored SVG circles, with wire" -ForegroundColor White
Write-Host "  edges, sidebar cards, and kind/stratum filter toggles." -ForegroundColor White
Write-Host ""
Write-Host "  URL: $KernelBase/explorer" -ForegroundColor Green
Write-Host ""

# Verify the UI functor endpoint is reachable
try {
    $ui = Invoke-KernelGet "/functor/ui"
    Write-Host "  /functor/ui : $($ui.nodes.Count) nodes, $($ui.edges.Count) edges" -ForegroundColor DarkGray
} catch {
    Write-Host "  /functor/ui : not reachable (Explorer may still render via explorer endpoint)" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "  Opening browser..." -ForegroundColor DarkGray
Start-Process "$KernelBase/explorer"

Pause-Step "Explorer opened. Press Enter to continue..."

# ── STEP 6 — Apply a morphism ────────────────────────────────────────────────

Banner "6" "Apply a morphism"

$demoUrn = "urn:demo:agent:hello-world-$(Get-Random -Maximum 9999)"
Write-Host "  POST $KernelBase/morphisms  (ADD envelope)" -ForegroundColor DarkYellow
Write-Host "  URN : $demoUrn" -ForegroundColor DarkGray

$envelope = @{
    type     = "ADD"
    urn      = $demoUrn
    kind     = "Agent"
    stratum  = "S2"
    payload  = @{ label = "Hello World Agent"; version = "0.1.0"; demo = $true }
    metadata = @{ created_by = "demo.ps1"; step = 6 }
}

$result = Invoke-KernelPost "/morphisms" $envelope
Show-Json $result

Write-Host ""
Write-Host "  Verifying via /state/nodes lookup..." -ForegroundColor DarkGray
$created = Invoke-KernelGet "/state/nodes/$demoUrn"
Write-Host "  ✓ Node created: kind=$($created.kind)  stratum=$($created.stratum)" -ForegroundColor Green

Pause-Step

# ── STEP 7 — Scoped subgraph ─────────────────────────────────────────────────

Banner "7" "Scoped subgraph"

$actor = "urn:moos:kernel:self"
Write-Host "  GET $KernelBase/state/scope/$actor" -ForegroundColor DarkYellow

try {
    $scope = Invoke-KernelGet "/state/scope/$actor"
    Write-Host "  nodes in scope : $($scope.nodes.Count)" -ForegroundColor Green
    Write-Host "  wires in scope : $($scope.wires.Count)" -ForegroundColor Green
    Write-Host ""
    Write-Host "  First 5 scoped nodes:" -ForegroundColor DarkGray
    $scope.nodes | Select-Object -First 5 | ForEach-Object {
        Write-Host ("  {0,-40}  [{1}]" -f $_.urn, $_.kind) -ForegroundColor White
    }
} catch {
    Write-Host "  Scope endpoint returned: $_" -ForegroundColor DarkYellow
}

Pause-Step

# ── STEP 8 — MCP bridge ──────────────────────────────────────────────────────

Banner "8" "MCP bridge (JSON-RPC 2.0 over HTTP)"

$sessionId = "demo-$(Get-Random -Maximum 99999)"
Write-Host "  SSE endpoint : $McpBase/sse" -ForegroundColor DarkGray
Write-Host "  Session      : $sessionId" -ForegroundColor DarkGray
Write-Host ""

# Check MCP health
try {
    $mcpHealth = Invoke-RestMethod -Uri "$McpBase/healthz"
    Write-Host "  MCP healthz: $($mcpHealth | ConvertTo-Json -Compress)" -ForegroundColor DarkGray
} catch {
    Write-Host "  WARNING: MCP bridge not reachable at $McpBase/healthz" -ForegroundColor DarkYellow
    Write-Host "  The kernel starts MCP on :8080. Check boot logs." -ForegroundColor DarkYellow
    Pause-Step "Press Enter to skip MCP steps..."
    goto :end
}

# tools/list
Write-Host ""
Write-Host "  POST $McpBase/message  (tools/list)" -ForegroundColor DarkYellow
$listBody = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

try {
    $listResp = Invoke-RestMethod -Method Post `
        -Uri "$McpBase/message?sessionId=$sessionId" `
        -Body $listBody `
        -ContentType "application/json"
    Show-Json $listResp
} catch {
    Write-Host "  (tools/list failed — MCP may require SSE session handshake first)" -ForegroundColor DarkYellow
}

# tools/call graph_state
Write-Host ""
Write-Host "  POST $McpBase/message  (tools/call → graph_state)" -ForegroundColor DarkYellow

$callBody = @{
    jsonrpc = "2.0"; id = 2; method = "tools/call"
    params  = @{ name = "graph_state"; arguments = @{} }
} | ConvertTo-Json -Depth 5

try {
    $callResp = Invoke-RestMethod -Method Post `
        -Uri "$McpBase/message?sessionId=$sessionId" `
        -Body $callBody `
        -ContentType "application/json"
    Show-Json $callResp 4
    Write-Host "  ✓ MCP tool call succeeded" -ForegroundColor Green
} catch {
    Write-Host "  (tools/call failed — see note above about SSE session)" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "  The MCP server is designed for AI client integration." -ForegroundColor DarkGray
Write-Host "  5 tools: graph_state, node_lookup, apply_morphism, scoped_subgraph, benchmark_project" -ForegroundColor DarkGray
Write-Host "  See README.md for the full MCP bridge reference." -ForegroundColor DarkGray

:end

# ── Summary ───────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  Demo complete!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Write-Host "  Kernel HTTP API : $KernelBase"
Write-Host "  MCP bridge      : $McpBase"
Write-Host "  Explorer UI     : $KernelBase/explorer"
Write-Host ""
Write-Host "  Next steps:"
Write-Host "  - Browse the Explorer:  $KernelBase/explorer"
Write-Host "  - Read the API docs:    platform\kernel\README.md"
Write-Host "  - Deep dive:            platform\kernel\DEVELOPERS.md"
Write-Host "  - Inspect the log:      GET $KernelBase/log"
Write-Host "  - Run tests:            Push-Location platform\kernel; go test ./..."
Write-Host ""
