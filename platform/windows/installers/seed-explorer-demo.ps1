param(
    [string]$BaseUrl = 'http://127.0.0.1:8000',
    [string]$PayloadPath
)

$ErrorActionPreference = 'Stop'

function Fail([string]$Message) {
    Write-Error $Message
    exit 1
}

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
}

function Get-PayloadPath([string]$RepoRoot, [string]$RequestedPath) {
    if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
        if ([System.IO.Path]::IsPathRooted($RequestedPath)) {
            return $RequestedPath
        }
        return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $RequestedPath))
    }

    return (Join-Path $RepoRoot 'platform\kernel\examples\explorer-demo.materialize.json')
}

$repoRoot = Get-RepoRoot
$resolvedPayloadPath = Get-PayloadPath $repoRoot $PayloadPath

if (-not (Test-Path $resolvedPayloadPath)) {
    Fail "Seed payload not found: $resolvedPayloadPath"
}

try {
    $health = Invoke-RestMethod -Method Get -Uri ($BaseUrl.TrimEnd('/') + '/healthz')
}
catch {
    Fail "Kernel is not reachable at $BaseUrl. Start the bootstrap first."
}

if ($health.status -ne 'ok') {
    Fail "Kernel health check failed at $BaseUrl."
}

$payloadText = Get-Content -Raw -Path $resolvedPayloadPath
$payload = $payloadText | ConvertFrom-Json

if (-not $payload.nodes -or $payload.nodes.Count -eq 0) {
    Fail 'Seed payload must declare at least one node.'
}

$state = Invoke-RestMethod -Method Get -Uri ($BaseUrl.TrimEnd('/') + '/state')
$seedURN = [string]$payload.nodes[0].urn

if ($state.graph.nodes.PSObject.Properties.Name -contains $seedURN) {
    Write-Host "Explorer demo already present: $seedURN"
    exit 0
}

$result = Invoke-RestMethod -Method Post -Uri ($BaseUrl.TrimEnd('/') + '/hydration/materialize') -ContentType 'application/json' -Body $payloadText

Write-Host 'Explorer demo seeded.'
Write-Host ("  nodes: " + $result.state.nodes)
Write-Host ("  wires: " + $result.state.wires)
Write-Host ("  summary: " + $result.summary)