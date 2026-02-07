# Stable server startup script for My Tiny Data Collider
# Ensures clean startup and proper error handling

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "My Tiny Data Collider - Server Startup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Kill any existing Python servers on port 8000
Write-Host "Checking for existing servers..." -ForegroundColor Yellow
$existingProcess = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1
if ($existingProcess) {
    Write-Host "  Stopping existing process on port 8000 (PID: $existingProcess)" -ForegroundColor Yellow
    Stop-Process -Id $existingProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Verify virtual environment
$venvPath = ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPath)) {
    Write-Host "ERROR: Virtual environment not found at $venvPath" -ForegroundColor Red
    exit 1
}

Write-Host "OK: Virtual environment found" -ForegroundColor Green

# Set environment variable
$env:ENVIRONMENT = "development"

# Start server
Write-Host "`nStarting server..." -ForegroundColor Yellow
Write-Host "  URL: http://127.0.0.1:8000" -ForegroundColor Gray
Write-Host "  Docs: http://127.0.0.1:8000/docs" -ForegroundColor Gray
Write-Host "  Press Ctrl+C to stop`n" -ForegroundColor Gray

try {
    & $venvPath -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload --log-level info
} catch {
    Write-Host "`nServer error: $_" -ForegroundColor Red
    exit 1
}
