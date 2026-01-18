
# Agent Studio Development Startup Script

write-host "--- Agent Studio Dev Environment ---" -ForegroundColor Cyan

# 1. Kill Check Ports
$ports = 8000, 3000, 3001, 5173
foreach ($port in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        $id = $conn.OwningProcess
        Write-Host "Killing process $id on port $port" -ForegroundColor Yellow
        Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
    }
}

# 2. Start Backend
Write-Host "Starting Backend (Port 8000)..." -ForegroundColor Green
Start-Process -FilePath "cmd" -ArgumentList "/k title BACKEND & cd backend && uv run uvicorn app.main:app --reload --port 8000 --host 0.0.0.0" -WorkingDirectory $PSScriptRoot

# 3. Start Frontend
Write-Host "Starting Frontend (Port 3000/3001)..." -ForegroundColor Green
Start-Process -FilePath "cmd" -ArgumentList "/k title FRONTEND & cd frontend && npm run dev" -WorkingDirectory $PSScriptRoot

Write-Host "Services started! Access at http://localhost:3000 or http://localhost:3001" -ForegroundColor Cyan
