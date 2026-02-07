#!/usr/bin/env pwsh
# Stop all dev servers

Write-Host "Stopping all dev servers..." -ForegroundColor Yellow

Get-Process | Where-Object { $_.ProcessName -match "python|node|uvicorn|vite" } | ForEach-Object {
    Write-Host "  Killing $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Red
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 1

Write-Host "✅ All servers stopped" -ForegroundColor Green
