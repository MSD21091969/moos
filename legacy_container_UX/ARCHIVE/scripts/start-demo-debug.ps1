# Start Demo Mode + Edge Debug - One Command
# Starts frontend in demo mode, waits for it, then launches Edge
# Usage: .\start-demo-debug.ps1

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🎮 Starting Demo Mode + Edge Debug Session" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Split-Path -Parent $scriptDir

# Step 1: Kill existing processes
Write-Host "🧹 Step 1: Cleaning up existing processes..." -ForegroundColor Yellow
& "$scriptDir\cleanup-processes.ps1"
Start-Sleep -Seconds 1
Write-Host ""

# Step 2: Start Frontend in Demo Mode (background)
Write-Host "⚛️  Step 2: Starting Frontend (Demo Mode)..." -ForegroundColor Yellow
$frontendJob = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$frontendDir'; `$env:VITE_MODE='demo'; npm run dev"
) -PassThru
Write-Host "   Frontend PID: $($frontendJob.Id)" -ForegroundColor Gray

# Step 3: Wait for frontend to be ready
Write-Host "   Waiting for Vite server..." -ForegroundColor Gray
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    Start-Sleep -Milliseconds 500
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -Method Head -TimeoutSec 1 -ErrorAction Stop
        $ready = $true
    } catch {
        Write-Host "   ... attempt $attempt/$maxAttempts" -ForegroundColor Gray -NoNewline
        Write-Host "`r" -NoNewline
    }
}

if ($ready) {
    Write-Host "   ✅ Frontend ready at http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Frontend may still be starting..." -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Launch Edge with debugging
Write-Host "🌐 Step 3: Launching Edge with Remote Debugging..." -ForegroundColor Yellow

$edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edgePath)) {
    $edgePath = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
}

Start-Process -FilePath $edgePath -ArgumentList @(
    "--remote-debugging-port=9222",
    "--auto-open-devtools-for-tabs",
    "--user-data-dir=$env:TEMP\edge-debug-profile",
    "http://localhost:5173/workspace"
)

Start-Sleep -Seconds 2

# Verify
$listening = Get-NetTCPConnection -LocalPort 9222 -ErrorAction SilentlyContinue
if ($listening) {
    Write-Host "   ✅ Edge ready on CDP port 9222" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Edge started but CDP port not confirmed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅ Demo Debug Session Ready!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Frontend: http://localhost:5173 (Demo Mode)" -ForegroundColor White
Write-Host "  Edge CDP: localhost:9222" -ForegroundColor White
Write-Host ""
Write-Host "  Next: Click Menu → Voice to test ChatAgent" -ForegroundColor Cyan
Write-Host ""
