<#
.SYNOPSIS
    Factory Development Orchestrator

.DESCRIPTION
    Central dev script for all Factory workspaces.

.PARAMETER Project
    Which project: collider, studio, all

.PARAMETER Service
    Which service: all, backend, frontend, runtime

.PARAMETER Stop
    Stop all services

.PARAMETER Status
    Show service status

.EXAMPLE
    .\dev.ps1 collider
    .\dev.ps1 studio
    .\dev.ps1 -Stop
    .\dev.ps1 -Status
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet("collider", "studio", "all")]
    [string]$Project = "collider",

    [ValidateSet("all", "backend", "frontend", "runtime")]
    [string]$Service = "all",

    [switch]$Stop,
    [switch]$Status
)

$ErrorActionPreference = "Continue"

# =============================================================================
# Configuration
# =============================================================================

$Config = @{
    collider = @{
        Name     = "Collider"
        Root     = "$PSScriptRoot\workspaces\collider_apps\applications\my-tiny-data-collider"
        Backend  = @{ Port = 8000; Cmd = "uv run uvicorn backend.main:app --reload --port 8000" }
        Runtime  = @{ Port = 8001; Cmd = "uv run python -m runtime.main" }
        Frontend = @{ Port = 5173; Cmd = "cd frontend && npm run dev -- --port 5173 --strictPort"; EnvDest = "frontend\.env.development" }
    }
    studio   = @{
        Name     = "Agent Studio"
        Root     = "$PSScriptRoot\agent-studio"
        Backend  = @{ Port = 8000; Cmd = "cd backend && uv run uvicorn app.main:app --reload --port 8000" }
        Frontend = @{ Port = 3000; Cmd = "cd frontend && npm run dev"; EnvDest = "frontend\.env.development" }
    }
}

$GlobalEnvFile = "$PSScriptRoot\.env.development"

# =============================================================================
# Functions
# =============================================================================

function Stop-PortProcess {
    param([int]$Port)
    $tcp = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($tcp) {
        $ids = $tcp.OwningProcess | Select-Object -Unique
        foreach ($id in $ids) {
            $p = Get-Process -Id $id -ErrorAction SilentlyContinue
            if ($p) {
                Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
                Write-Host "  Stopped $($p.Name) (PID $id) on :$Port" -ForegroundColor Gray
            }
        }
    }
}

function Get-PortStatus {
    param([int]$Port)
    $tcp = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return [bool]$tcp
}

function Show-Status {
    Write-Host "`nFACTORY STATUS" -ForegroundColor Cyan
    Write-Host "==============" -ForegroundColor Cyan

    foreach ($key in $Config.Keys) {
        $proj = $Config[$key]
        Write-Host "`n$($proj.Name)" -ForegroundColor Yellow

        if ($proj.Backend) {
            $ok = Get-PortStatus -Port $proj.Backend.Port
            $icon = if ($ok) { "[OK]" } else { "[--]" }
            $color = if ($ok) { "Green" } else { "DarkGray" }
            Write-Host "  $icon Backend  :$($proj.Backend.Port)" -ForegroundColor $color
        }
        if ($proj.Runtime) {
            $ok = Get-PortStatus -Port $proj.Runtime.Port
            $icon = if ($ok) { "[OK]" } else { "[--]" }
            $color = if ($ok) { "Green" } else { "DarkGray" }
            Write-Host "  $icon Runtime  :$($proj.Runtime.Port)" -ForegroundColor $color
        }
        if ($proj.Frontend) {
            $ok = Get-PortStatus -Port $proj.Frontend.Port
            $icon = if ($ok) { "[OK]" } else { "[--]" }
            $color = if ($ok) { "Green" } else { "DarkGray" }
            Write-Host "  $icon Frontend :$($proj.Frontend.Port)" -ForegroundColor $color
        }
    }
    Write-Host ""
}

function Stop-AllServices {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    @(8000, 8001, 3000, 3001, 5173) | ForEach-Object { Stop-PortProcess -Port $_ }
    Write-Host "Done.`n" -ForegroundColor Green
}

function Start-Project {
    param([string]$Key, [string]$Svc)

    $proj = $Config[$Key]
    if (-not $proj) { Write-Host "Unknown: $Key" -ForegroundColor Red; return }

    Write-Host "`nStarting $($proj.Name)..." -ForegroundColor Cyan

    # Sync env file from factory root
    if ($proj.Frontend.EnvDest -and (Test-Path $GlobalEnvFile)) {
        $destPath = Join-Path $proj.Root $proj.Frontend.EnvDest
        Copy-Item $GlobalEnvFile $destPath -Force
        Write-Host "  Synced .env.development" -ForegroundColor Gray
    }

    # Stop existing
    if ($Svc -eq "all" -or $Svc -eq "backend") { if ($proj.Backend) { Stop-PortProcess -Port $proj.Backend.Port } }
    if ($Svc -eq "all" -or $Svc -eq "runtime") { if ($proj.Runtime) { Stop-PortProcess -Port $proj.Runtime.Port } }
    if ($Svc -eq "all" -or $Svc -eq "frontend") { if ($proj.Frontend) { Stop-PortProcess -Port $proj.Frontend.Port } }

    Start-Sleep -Milliseconds 500

    # Start services
    if (($Svc -eq "all" -or $Svc -eq "backend") -and $proj.Backend) {
        Write-Host "  Backend  :$($proj.Backend.Port)" -ForegroundColor White
        Start-Process cmd -ArgumentList "/k", "title [$($proj.Name)] Backend && $($proj.Backend.Cmd)" -WorkingDirectory $proj.Root
    }
    if (($Svc -eq "all" -or $Svc -eq "runtime") -and $proj.Runtime) {
        Write-Host "  Runtime  :$($proj.Runtime.Port)" -ForegroundColor White
        Start-Process cmd -ArgumentList "/k", "title [$($proj.Name)] Runtime && $($proj.Runtime.Cmd)" -WorkingDirectory $proj.Root
    }
    if (($Svc -eq "all" -or $Svc -eq "frontend") -and $proj.Frontend) {
        Write-Host "  Frontend :$($proj.Frontend.Port)" -ForegroundColor White
        Start-Process cmd -ArgumentList "/k", "title [$($proj.Name)] Frontend && $($proj.Frontend.Cmd)" -WorkingDirectory $proj.Root
    }

    Write-Host "`nReady!" -ForegroundColor Green
    if ($proj.Frontend) { Write-Host "  http://localhost:$($proj.Frontend.Port)" -ForegroundColor White }
    if ($proj.Backend) { Write-Host "  http://localhost:$($proj.Backend.Port)/docs" -ForegroundColor White }
    Write-Host ""
}

# =============================================================================
# Main
# =============================================================================

Write-Host "`nFACTORY DEV" -ForegroundColor Magenta
Write-Host "===========" -ForegroundColor Magenta

if ($Status) { Show-Status; exit 0 }
if ($Stop) { Stop-AllServices; exit 0 }

if ($Project -eq "all") {
    Start-Project -Key "collider" -Svc $Service
    Start-Project -Key "studio" -Svc $Service
}
else {
    Start-Project -Key $Project -Svc $Service
}
