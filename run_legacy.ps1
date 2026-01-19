#!/usr/bin/env pwsh
# Run Legacy Container UX in Factory Environment (DEMO MODE)

Write-Host "🚀 Starting Legacy Container UX (Available for Demo)" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:5174" -ForegroundColor Gray
Write-Host "   NOTE: Backend is DISABLED (Demo Mode)" -ForegroundColor Yellow

$LegacyRoot = "$PSScriptRoot\legacy_container_UX"
$FrontendRoot = "$LegacyRoot\frontend"

# 1. Setup Frontend
Write-Host "`n📦 Setting up Frontend..." -ForegroundColor Yellow
Push-Location $FrontendRoot
if (-not (Test-Path "node_modules")) {
    Write-Host "   Installing node modules..."
    npm install
}

# 2. Start Frontend
Write-Host "   Starting Frontend on port 5174 (Demo Mode)..." -ForegroundColor Green
# Using dev:demo to ensure VITE_MODE=demo and no backend expectation
$FrontendProcess = Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$FrontendRoot'; npm run dev:demo" -PassThru
Pop-Location

Write-Host "`n✅ Legacy Container UX Started (Demo Mode)!" -ForegroundColor Green
