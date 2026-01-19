#!/usr/bin/env pwsh
# Run Agent Studio in Factory Environment

Write-Host "🚀 Starting Agent Studio" -ForegroundColor Cyan
Write-Host "   Backend: http://localhost:9001" -ForegroundColor Gray
Write-Host "   Frontend: http://localhost:3001" -ForegroundColor Gray

$StudioRoot = "$PSScriptRoot\agent-studio"
$BackendRoot = "$StudioRoot\backend"
$FrontendRoot = "$StudioRoot\frontend"

# 1. Setup Backend
Write-Host "`n📦 Setting up Backend..." -ForegroundColor Yellow
Push-Location $BackendRoot
if (-not (Test-Path ".venv")) {
    Write-Host "   Creating .venv..."
    uv venv
}
Write-Host "   Syncing dependencies..."
uv sync

# 2. Start Backend
Write-Host "   Starting Backend on port 9001..." -ForegroundColor Green
# Starting uvicorn on port 9001
$BackendProcess = Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$BackendRoot'; uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 9001" -PassThru
Pop-Location

# 3. Setup Frontend
Write-Host "`n📦 Setting up Frontend..." -ForegroundColor Yellow
Push-Location $FrontendRoot
if (-not (Test-Path "node_modules")) {
    Write-Host "   Installing node modules..."
    npm install
}

# 4. Start Frontend
Write-Host "   Starting Frontend on port 3001..." -ForegroundColor Green
# Setting env vars for custom backend URL and port
$env:PORT = "3001"
$env:NEXT_PUBLIC_API_URL = "http://localhost:9001"
$env:NEXT_PUBLIC_WS_URL = "ws://localhost:9001"

$FrontendProcess = Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$FrontendRoot'; `$env:PORT='3001'; `$env:NEXT_PUBLIC_API_URL='http://localhost:9001'; `$env:NEXT_PUBLIC_WS_URL='ws://localhost:9001'; npm run dev" -PassThru
Pop-Location

Write-Host "`n✅ Agent Studio Started!" -ForegroundColor Green
