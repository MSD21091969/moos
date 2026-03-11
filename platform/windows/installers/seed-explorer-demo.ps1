# Seed Explorer Demo
# Posts the explorer demo materialization payload to a running kernel.
# No-ops if the demo root URN already exists.

param(
    [string]$KernelAddr = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$DemoPayload = Join-Path $WorkspaceRoot "platform\kernel\examples\explorer-demo.materialize.json"

if (-not (Test-Path $DemoPayload)) {
    Write-Warning "Demo payload not found: $DemoPayload (skipping)"
    return
}

# Check if kernel is running
try {
    $null = Invoke-RestMethod -Uri "$KernelAddr/explorer" -Method GET -TimeoutSec 3
} catch {
    Write-Error "Kernel not reachable at $KernelAddr — is it running?"
    return
}

# Post demo payload
Write-Host "Seeding explorer demo..."
$body = Get-Content $DemoPayload -Raw
try {
    $result = Invoke-RestMethod -Uri "$KernelAddr/hydration/materialize" -Method POST -Body $body -ContentType "application/json"
    Write-Host "  Seeded successfully: $result"
} catch {
    if ($_.Exception.Response.StatusCode -eq 409) {
        Write-Host "  Demo already seeded (409 Conflict) — skipping"
    } else {
        Write-Error "Seed failed: $_"
    }
}
