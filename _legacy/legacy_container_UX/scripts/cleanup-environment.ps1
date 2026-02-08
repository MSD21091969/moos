# scripts/cleanup-environment.ps1
# Kills all development processes (Node, Python, Edge)

Write-Host "🧹 Cleaning up development environment..." -ForegroundColor Yellow

# Kill processes
$processes = Get-Process -Name 'node','python','msedge' -ErrorAction SilentlyContinue
if ($processes) {
    $processes | Stop-Process -Force
    Write-Host "✅ Killed $($processes.Count) processes." -ForegroundColor Green
} else {
    Write-Host "✨ No processes found to kill." -ForegroundColor Cyan
}

# Clear Vite cache (optional, good for stability)
if (Test-Path "frontend/node_modules/.vite") {
    Remove-Item -Recurse -Force "frontend/node_modules/.vite" -ErrorAction SilentlyContinue
    Write-Host "🗑️ Cleared Vite cache." -ForegroundColor Gray
}

Write-Host "✅ Environment clean." -ForegroundColor Green
