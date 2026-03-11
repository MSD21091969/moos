param(
    [string]$ConfigPath = "$env:TEMP\moos\config.json",
    [string]$BaseUrl = "http://localhost:8000",
    [string]$PayloadPath = "kernel/examples/usergraph.materialize.json"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ConfigPath)) {
    throw "Config file not found: $ConfigPath"
}

$config = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json

if ($config.store_type -ne "file") {
    Write-Host "store_type is '$($config.store_type)'; nothing to reset on disk." -ForegroundColor Yellow
} elseif (-not $config.log_path) {
    throw "Config is missing log_path for file store."
} elseif (Test-Path $config.log_path) {
    Remove-Item -Path $config.log_path -Force
    Write-Host "Deleted log: $($config.log_path)" -ForegroundColor Green
} else {
    Write-Host "Log file already clean: $($config.log_path)" -ForegroundColor DarkYellow
}

if (-not (Test-Path $PayloadPath)) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot = Split-Path -Parent $scriptRoot
    $relativeDefault = Join-Path $repoRoot "examples\usergraph.materialize.json"
    if (Test-Path $relativeDefault) {
        $PayloadPath = $relativeDefault
    } else {
        throw "Materialize payload not found: $PayloadPath"
    }
}

$payload = Get-Content -Raw -Path $PayloadPath

try {
    $response = Invoke-RestMethod -Method Post -Uri "$BaseUrl/hydration/materialize" -ContentType "application/json" -Body $payload
    Write-Host "Seed applied successfully." -ForegroundColor Green
    $response | ConvertTo-Json -Depth 8
} catch {
    Write-Host "Seed request failed. Ensure kernel is running at $BaseUrl" -ForegroundColor Red
    throw
}
