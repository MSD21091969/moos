# Start Debug Session - One-Click Full Stack + Edge Debug
# Launches backend, frontend, and Edge with debugging in one command
# Usage: .\start-debug-session.ps1

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🎮 Starting Full Debug Session" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Split-Path -Parent $scriptDir
$backendDir = Join-Path (Split-Path -Parent $frontendDir) "backend"

# Step 1: Kill existing processes
Write-Host "🧹 Step 1: Cleaning up existing processes..." -ForegroundColor Yellow
& "$scriptDir\cleanup-processes.ps1"
Write-Host ""

# Step 2: Start Backend
Write-Host "🐍 Step 2: Starting Backend (FastAPI)..." -ForegroundColor Yellow
$backendJob = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$backendDir'; `$env:USE_FIRESTORE_MOCKS='true'; `$env:ENVIRONMENT='development'; `$env:SKIP_AUTH_FOR_TESTING='true'; python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000"
) -PassThru
Write-Host "   Backend PID: $($backendJob.Id)" -ForegroundColor Gray

# Wait for backend to start
Write-Host "   Waiting for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Step 3: Start Frontend
Write-Host "⚛️  Step 3: Starting Frontend (Vite)..." -ForegroundColor Yellow
$frontendJob = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$frontendDir'; npm run dev"
) -PassThru
Write-Host "   Frontend PID: $($frontendJob.Id)" -ForegroundColor Gray

# Wait for frontend to start
Write-Host "   Waiting for frontend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Step 4: Launch Chromium with debugging (Playwright uses Chromium, not Edge)
Write-Host "🌐 Step 4: Launching Chromium with Remote Debugging (CDP port 9222)..." -ForegroundColor Yellow
Write-Host "   (Using Chromium so Playwright debugging stays synchronized)" -ForegroundColor Gray

$chromiumPath = & npx -y which chromium 2>$null
if (-not $chromiumPath) {
    $chromiumPath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
}

if (Test-Path $chromiumPath) {
    Start-Process -FilePath $chromiumPath -ArgumentList @(
        "--remote-debugging-port=9222",
        "--auto-open-devtools-for-tabs",
        "--user-data-dir=$env:TEMP\chromium-debug-profile",
        "http://localhost:5173/workspace"
    )
    Start-Sleep -Milliseconds 2000
    Write-Host "   ✅ Chromium launched on port 9222" -ForegroundColor Green
} else {
    Write-Host "⚠️  Could not find Chromium/Edge, but backend and frontend are ready" -ForegroundColor Yellow
    Write-Host "   Visit: http://localhost:5173/workspace manually" -ForegroundColor Gray
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ Debug Session Ready!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  🌐 Frontend:  http://localhost:5173/workspace" -ForegroundColor White
Write-Host "  🐍 Backend:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  🔍 Edge CDP:  http://localhost:9222" -ForegroundColor White
Write-Host ""
Write-Host "  Quick Commands:" -ForegroundColor Cyan
Write-Host "    • Debug: Watch Console  - Live stream Edge logs" -ForegroundColor Gray
Write-Host "    • Debug: Snapshot Edge  - Capture current state" -ForegroundColor Gray
Write-Host "    • Clean: Kill All       - Stop everything" -ForegroundColor Gray
Write-Host ""
