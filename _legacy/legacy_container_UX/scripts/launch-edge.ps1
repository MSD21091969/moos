# Launch Edge with Remote Debugging
# Kills existing Edge instances first to ensure port 9222 is available
# Usage: .\launch-debug-edge.ps1

param(
    [string]$Url = "http://localhost:5174/workspace"
)

Write-Host "🌐 Launching Edge with Remote Debugging..." -ForegroundColor Cyan

# Check if Edge is running
$edgeProcesses = Get-Process msedge -ErrorAction SilentlyContinue
if ($edgeProcesses) {
    $count = @($edgeProcesses).Count
    Write-Host "⚠️  Found $count Edge process(es) - closing them..." -ForegroundColor Yellow
    Stop-Process -Name msedge -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 1000
}

# Find Edge executable
$edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edgePath)) {
    $edgePath = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
}

if (-not (Test-Path $edgePath)) {
    Write-Host "❌ Could not find Edge at expected paths" -ForegroundColor Red
    exit 1
}

Write-Host "📍 Using Edge at: $edgePath" -ForegroundColor Gray

# Launch Edge with debugging
$arguments = @(
    "--remote-debugging-port=9222",
    "--auto-open-devtools-for-tabs",
    "--user-data-dir=$env:TEMP\edge-debug-profile",
    $Url
)

Write-Host "🚀 Starting Edge with debugging on port 9222..." -ForegroundColor Green
Start-Process -FilePath $edgePath -ArgumentList $arguments

# Wait for Edge to start
Start-Sleep -Milliseconds 2000

# Verify port is listening
$listening = Get-NetTCPConnection -LocalPort 9222 -ErrorAction SilentlyContinue
if ($listening) {
    Write-Host "✅ Edge launched successfully - port 9222 is ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Run 'Debug: Watch Console' to stream logs" -ForegroundColor White
    Write-Host "  2. Run 'Debug: Snapshot Edge' anytime to capture state" -ForegroundColor White
} else {
    Write-Host "⚠️  Edge started but port 9222 not yet available - may need a moment" -ForegroundColor Yellow
}
