param(
    [switch]$NoFrontends,
    [switch]$SidepanelOnly
)

$ErrorActionPreference = 'Stop'

function Write-Step {
    param([string]$Message)
    Write-Host "[mo:os-start] $Message"
}

function Test-PortListening {
    param([int]$Port)
    try {
        $conn = Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq $Port } | Select-Object -First 1
        return $null -ne $conn
    }
    catch {
        return $false
    }
}

function Stop-ProcessesByPorts {
    param([int[]]$Ports)

    $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $Ports -contains $_.LocalPort }

    $listenerPids = $connections |
    Select-Object -ExpandProperty OwningProcess -Unique |
    Where-Object { $_ -and $_ -ne $PID }

    foreach ($procId in $listenerPids) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Step "Stopped process $procId on managed port(s) $($Ports -join ', ')"
        }
        catch {
            Write-Step "Could not stop process ${procId}: $($_.Exception.Message)"
        }
    }
}

function Start-ServiceWindow {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Command,
        [int[]]$Ports,
        [string]$HealthUrl = ''
    )

    $alreadyListening = $false
    foreach ($port in $Ports) {
        if (Test-PortListening -Port $port) {
            $alreadyListening = $true
            break
        }
    }

    if ($alreadyListening) {
        if ($HealthUrl -and (Wait-ForHttp -Url $HealthUrl -TimeoutSeconds 4)) {
            Write-Step "$Name skipped (already healthy on port: $($Ports -join ', '))"
            return
        }

        Write-Step "$Name found unhealthy listener; restarting port(s) $($Ports -join ', ')"
        Stop-ProcessesByPorts -Ports $Ports
        Start-Sleep -Seconds 1
    }

    $escapedWorkingDirectory = $WorkingDirectory.Replace("'", "''")
    $script = "Set-Location '$escapedWorkingDirectory'; $Command"
    Start-Process -FilePath 'pwsh' -ArgumentList @('-NoLogo', '-NoExit', '-Command', $script) | Out-Null
    Write-Step "$Name started"
}

function Wait-ForHttp {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 90
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 3 -UseBasicParsing
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        }
        catch {
            Start-Sleep -Milliseconds 750
        }
    }

    return $false
}

function Wait-ForTcp {
    param(
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutSeconds = 90
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $client = New-Object System.Net.Sockets.TcpClient
            $iar = $client.BeginConnect($HostName, $Port, $null, $null)
            $ok = $iar.AsyncWaitHandle.WaitOne(1500, $false)
            if ($ok -and $client.Connected) {
                $client.EndConnect($iar)
                $client.Close()
                return $true
            }
            $client.Close()
        }
        catch {
            Start-Sleep -Milliseconds 750
        }
    }

    return $false
}

$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$moosDir = Join-Path $baseDir 'FFS2_ColliderBackends_MultiAgentChromeExtension\moos'
$ffs3Dir = Join-Path $baseDir 'FFS3_ColliderApplicationsFrontendServer'

if (-not (Test-Path $moosDir)) {
    throw "MOOS directory not found: $moosDir"
}

if (-not (Test-Path $ffs3Dir)) {
    throw "FFS3 directory not found: $ffs3Dir"
}

Write-Host '============================================'
Write-Host '  mo:os + FFS3 Unified Startup'
Write-Host '============================================'

Start-ServiceWindow -Name 'MOOS Data+Agent+WS (8000/8004/18789)' -WorkingDirectory $moosDir -Command 'pnpm nx run @moos/data-server:serve' -Ports @(8000, 8004, 18789) -HealthUrl 'http://127.0.0.1:8000/health'
Start-ServiceWindow -Name 'MOOS Tool Server (8001)' -WorkingDirectory $moosDir -Command 'pnpm nx run @moos/tool-server:serve' -Ports @(8001) -HealthUrl 'http://127.0.0.1:8001/health'

if (-not $NoFrontends) {
    if ($SidepanelOnly) {
        Start-ServiceWindow -Name 'FFS4 Sidepanel (4201)' -WorkingDirectory $ffs3Dir -Command 'pnpm exec vite --config apps/ffs4/vite.config.mts --host 0.0.0.0 --port 4201 --strictPort' -Ports @(4201) -HealthUrl 'http://127.0.0.1:4201'
    }
    else {
        Start-ServiceWindow -Name 'FFS6 IDE (4200)' -WorkingDirectory $ffs3Dir -Command 'pnpm exec vite --config apps/ffs6/vite.config.mts --host 0.0.0.0 --port 4200 --strictPort' -Ports @(4200) -HealthUrl 'http://127.0.0.1:4200'
        Start-ServiceWindow -Name 'FFS4 Sidepanel (4201)' -WorkingDirectory $ffs3Dir -Command 'pnpm exec vite --config apps/ffs4/vite.config.mts --host 0.0.0.0 --port 4201 --strictPort' -Ports @(4201) -HealthUrl 'http://127.0.0.1:4201'
        Start-ServiceWindow -Name 'FFS5 PiP (4202)' -WorkingDirectory $ffs3Dir -Command 'pnpm exec vite --config apps/ffs5/vite.config.mts --host 0.0.0.0 --port 4202 --strictPort' -Ports @(4202) -HealthUrl 'http://127.0.0.1:4202'
    }
}

Write-Step 'Waiting for health/readiness checks...'

$checks = @(
    @{ Name = 'Data Server'; Ready = { Wait-ForHttp -Url 'http://127.0.0.1:8000/health' } },
    @{ Name = 'Tool Server'; Ready = { Wait-ForHttp -Url 'http://127.0.0.1:8001/health' } },
    @{ Name = 'Agent Compat'; Ready = { Wait-ForHttp -Url 'http://127.0.0.1:8004/health' } },
    @{ Name = 'NanoClaw WS'; Ready = { Wait-ForTcp -HostName '127.0.0.1' -Port 18789 } }
)

if (-not $NoFrontends) {
    if ($SidepanelOnly) {
        $checks += @{ Name = 'FFS4 Sidepanel'; Ready = { Wait-ForHttp -Url 'http://127.0.0.1:4201' } }
    }
    else {
        $checks += @{ Name = 'FFS6 IDE'; Ready = { Wait-ForHttp -Url 'http://127.0.0.1:4200' } }
        $checks += @{ Name = 'FFS4 Sidepanel'; Ready = { Wait-ForHttp -Url 'http://127.0.0.1:4201' } }
        $checks += @{ Name = 'FFS5 PiP'; Ready = { Wait-ForHttp -Url 'http://127.0.0.1:4202' } }
    }
}

$failed = @()
foreach ($check in $checks) {
    $ok = & $check.Ready
    if ($ok) {
        Write-Step "$($check.Name): READY"
    }
    else {
        Write-Step "$($check.Name): NOT READY"
        $failed += $check.Name
    }
}

Write-Host ''
Write-Host 'Endpoints:'
Write-Host '  Data Server:     http://localhost:8000/health'
Write-Host '  Tool Server:     http://localhost:8001/health'
Write-Host '  Agent Compat:    http://localhost:8004/health'
Write-Host '  NanoClaw WS:     ws://localhost:18789'
if (-not $NoFrontends) {
    if ($SidepanelOnly) {
        Write-Host '  FFS4 Sidepanel:  http://localhost:4201'
    }
    else {
        Write-Host '  FFS6 IDE:        http://localhost:4200'
        Write-Host '  FFS4 Sidepanel:  http://localhost:4201'
        Write-Host '  FFS5 PiP:        http://localhost:4202'
    }
}

if ($failed.Count -gt 0) {
    Write-Host ''
    Write-Host "Startup completed with warnings. Not ready: $($failed -join ', ')" -ForegroundColor Yellow
    exit 1
}

Write-Host ''
Write-Host 'Startup complete. All requested services are ready.' -ForegroundColor Green