# health-check.ps1 — Check health of all Collider backend services
# Usage: .\scripts\health-check.ps1

$ErrorActionPreference = "Continue"

$services = @(
    @{ Name = "DataServer"; Url = "http://localhost:8000/health" },
    @{ Name = "GraphToolServer"; Url = "http://localhost:8001/health" },
    @{ Name = "VectorDbServer"; Url = "http://localhost:8002/health" }
)

$allHealthy = $true

Write-Host "Checking Collider service health..." -ForegroundColor Cyan
Write-Host ""

foreach ($service in $services) {
    try {
        $response = Invoke-RestMethod -Uri $service.Url -TimeoutSec 5 -ErrorAction Stop
        if ($response.status -eq "ok") {
            Write-Host "  [OK]   $($service.Name) — $($response.service)" -ForegroundColor Green
        }
        else {
            Write-Host "  [WARN] $($service.Name) — unexpected response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Yellow
            $allHealthy = $false
        }
    }
    catch {
        Write-Host "  [FAIL] $($service.Name) — $($_.Exception.Message)" -ForegroundColor Red
        $allHealthy = $false
    }
}

Write-Host ""
if ($allHealthy) {
    Write-Host "All services are healthy!" -ForegroundColor Green
}
else {
    Write-Host "Some services failed health checks." -ForegroundColor Red
    exit 1
}
