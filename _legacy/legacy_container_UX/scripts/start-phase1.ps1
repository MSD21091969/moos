# ============================================
# Phase 1: Start Frontend + Edge with CDP
# Fully automated - no prompts, no interaction
# ============================================
param(
    [switch]$SkipBrowser  # Use if Edge already open
)

$ErrorActionPreference = 'SilentlyContinue'
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n🚀 Phase 1: Demo Mode" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor DarkGray

# 1. Kill existing
Write-Host "[1/4] Cleaning up..." -ForegroundColor Gray
Get-Process -Name 'node' -ErrorAction SilentlyContinue | Stop-Process -Force 2>$null
if (-not $SkipBrowser) {
    Get-Process -Name 'msedge' -ErrorAction SilentlyContinue | Stop-Process -Force 2>$null
}
Start-Sleep -Seconds 1

# 2. Start Vite (background, non-interactive)
Write-Host "[2/4] Starting Vite in Demo Mode..." -ForegroundColor Gray
$env:CI = 'true'
$env:VITE_MODE = 'demo'
Start-Process -FilePath "cmd" -ArgumentList "/c","cd /d `"$WorkspaceRoot\frontend`" && set VITE_MODE=demo && npm run dev:demo" -WindowStyle Minimized

# 3. Wait for server (port 5174 for demo mode)
Write-Host "[3/4] Waiting for server on port 5174..." -ForegroundColor Gray
$maxWait = 20
$waited = 0
while ($waited -lt $maxWait) {
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:5174" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
        break
    } catch { }
    Start-Sleep -Seconds 1
    $waited++
    Write-Host "." -NoNewline -ForegroundColor DarkGray
}
Write-Host ""

if ($waited -ge $maxWait) {
    Write-Host "❌ Server failed to start after ${maxWait}s" -ForegroundColor Red
    exit 1
}

# 4. Launch Edge with CDP
if (-not $SkipBrowser) {
    Write-Host "[4/4] Launching Edge with CDP..." -ForegroundColor Gray
    $edgeArgs = @(
        "--remote-debugging-port=9222",
        "--user-data-dir=$env:TEMP\edge-phase1-cdp",
        "--no-first-run",
        "--no-default-browser-check",
        "http://localhost:5174"
    )
    Start-Process "msedge" -ArgumentList $edgeArgs
    Start-Sleep -Seconds 2
} else {
    Write-Host "[4/4] Skipping browser launch" -ForegroundColor Gray
}

# 5. Verify CDP
try {
    $cdp = Invoke-RestMethod -Uri "http://localhost:9222/json" -ErrorAction Stop
    $appPage = $cdp | Where-Object { $_.url -like "*localhost:5174*" }
    Write-Host "`n==========================================" -ForegroundColor DarkGray
    Write-Host "✅ Phase 1 Ready (Demo Mode)!" -ForegroundColor Green
    Write-Host "   Frontend:  http://localhost:5174" -ForegroundColor White
    Write-Host "   Mode:      demo (no backend)" -ForegroundColor White
    Write-Host "   CDP Port:  9222" -ForegroundColor White
    if ($appPage) {
        Write-Host "   Page:      $($appPage.title)" -ForegroundColor White
    }
    Write-Host "   MCP:       Playwright MCP can connect" -ForegroundColor White
    Write-Host "==========================================" -ForegroundColor DarkGray
} catch {
    Write-Host "`n⚠️  CDP not responding" -ForegroundColor Yellow
    Write-Host "   Server is running but Edge CDP may need restart" -ForegroundColor Gray
}
