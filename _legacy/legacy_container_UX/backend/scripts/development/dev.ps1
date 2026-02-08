#!/usr/bin/env pwsh
# Quick dev startup - no approval needed

Write-Host "🚀 Starting My Tiny Data Collider Dev Environment" -ForegroundColor Cyan

# Kill existing processes
Write-Host "Cleaning up old processes..." -ForegroundColor Yellow
Get-Process | Where-Object { $_.ProcessName -match "python|node" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Set environment
$env:USE_FIRESTORE_MOCKS = "true"
$env:ENVIRONMENT = "development"
$env:JWT_SECRET_KEY = "dev-secret-key-change-in-production-min-32-characters"
$env:OPENAI_API_KEY = "sk-test-key"

# Start backend
Write-Host "Starting backend on port 8000..." -ForegroundColor Green
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$PWD'; `$env:USE_FIRESTORE_MOCKS='true'; `$env:ENVIRONMENT='development'; `$env:JWT_SECRET_KEY='dev-secret-key-change-in-production-min-32-characters'; `$env:OPENAI_API_KEY='sk-test-key'; py -3.11 -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000"

Start-Sleep -Seconds 3

# Start frontend
Write-Host "Starting frontend on port 5173..." -ForegroundColor Green
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"

Start-Sleep -Seconds 2

Write-Host "`n✅ Dev environment started!" -ForegroundColor Green
Write-Host "📱 Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "⚙️  Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop this script (servers will keep running)`n" -ForegroundColor Yellow
