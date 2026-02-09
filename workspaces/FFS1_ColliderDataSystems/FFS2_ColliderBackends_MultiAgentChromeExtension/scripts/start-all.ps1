# start-all.ps1 — Start all Collider backend services in parallel
# Usage: .\scripts\start-all.ps1

$ErrorActionPreference = "Continue"
$FFS2 = Split-Path -Parent $PSScriptRoot

Write-Host "Starting Collider backend services..." -ForegroundColor Cyan

# Start DataServer (port 8000)
$dataServer = Start-Process -FilePath "uv" `
    -ArgumentList "run", "uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory "$FFS2\ColliderDataServer" `
    -PassThru -NoNewWindow
Write-Host "  DataServer started (PID: $($dataServer.Id), port 8000)" -ForegroundColor Green

# Start GraphToolServer (port 8001)
$graphServer = Start-Process -FilePath "uv" `
    -ArgumentList "run", "uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8001" `
    -WorkingDirectory "$FFS2\ColliderGraphToolServer" `
    -PassThru -NoNewWindow
Write-Host "  GraphToolServer started (PID: $($graphServer.Id), port 8001)" -ForegroundColor Green

# Start VectorDbServer (port 8002)
$vectorServer = Start-Process -FilePath "uv" `
    -ArgumentList "run", "uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8002" `
    -WorkingDirectory "$FFS2\ColliderVectorDbServer" `
    -PassThru -NoNewWindow
Write-Host "  VectorDbServer started (PID: $($vectorServer.Id), port 8002)" -ForegroundColor Green

Write-Host ""
Write-Host "All services started. PIDs:" -ForegroundColor Cyan
Write-Host "  DataServer:      $($dataServer.Id)"
Write-Host "  GraphToolServer: $($graphServer.Id)"
Write-Host "  VectorDbServer:  $($vectorServer.Id)"
Write-Host ""
Write-Host "Run .\scripts\health-check.ps1 to verify services are running." -ForegroundColor Yellow
Write-Host "Press Ctrl+C or close this window to stop all services." -ForegroundColor Yellow

# Wait for any process to exit
try {
    Wait-Process -Id $dataServer.Id, $graphServer.Id, $vectorServer.Id
}
finally {
    Write-Host "Stopping all services..." -ForegroundColor Red
    Stop-Process -Id $dataServer.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $graphServer.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $vectorServer.Id -ErrorAction SilentlyContinue
}
