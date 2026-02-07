# scripts/start-dev-environment.ps1
# Golden Path: Starts Backend and Frontend in separate terminal windows, then launches Edge.

Write-Host "🚀 Starting Dev Environment (Golden Path)..." -ForegroundColor Green

# 1. Cleanup
Write-Host "🧹 Cleaning up old processes..." -ForegroundColor Yellow
Get-Process -Name 'node','python','msedge' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 2. Start Backend (New Window)
Write-Host "🔥 Starting Backend (Port 8000)..." -ForegroundColor Cyan
$backendCmd = "Set-Location '$PSScriptRoot/../backend'; `$env:USE_FIRESTORE_MOCKS='false'; `$env:ENVIRONMENT='development'; `$env:SKIP_AUTH_FOR_TESTING='true'; py -3.11 -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "$backendCmd"

# 3. Start Frontend (New Window)
Write-Host "⚛️ Starting Frontend (Port 5173)..." -ForegroundColor Cyan
$frontendCmd = "Set-Location '$PSScriptRoot/../frontend'; npm run dev"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "$frontendCmd"

# 4. Wait for services
Write-Host "⏳ Waiting 5s for services to warm up..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 5. Launch Edge
Write-Host "🌐 Launching Edge (CDP 9222)..." -ForegroundColor Green
& "$PSScriptRoot/launch-edge.ps1"

Write-Host "✅ Environment Started! Run 'npx tsx frontend/scripts/mcp/tail-console.ts' to observe logs." -ForegroundColor Green
