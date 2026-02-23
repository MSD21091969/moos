---
description: Stop all running Collider services and clean up ports
---

# Stopping Collider Services

This workflow safely stops all backend and frontend services associated with the
Collider ecosystem, freeing up the required ports before starting a new test
session.

It is recommended to run this workflow before executing `/dev-start` to avoid "Port already in use" errors.

## Commands to Stop Servers

If you are running the servers in separate terminal panes, the easiest way to stop them is to click into each pane and press `Ctrl+C`.

If services are running in the background or are stuck, you can force-kill them
by port using this PowerShell one-liner.

### Kill by Port (PowerShell)

```powershell
// turbo-all
# Kills processes listening on the standard Collider service ports
$ports = @(8000, 8001, 8002, 8003, 8004, 18789, 4200)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $pidToKill = $conn.OwningProcess
            if ($pidToKill) {
                Write-Host "Killing process $pidToKill on port $port"
                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
            }
        }
    } else {
        Write-Host "Port $port is free."
    }
}
```

## Ports Cleaned

| Port | Service |
| --- | --- |
| 8000 | ColliderDataServer |
| 8001 | ColliderGraphToolServer |
| 8002 | ColliderVectorDbServer |
| 8003 | SQLite Web (dev) |
| 8004 | ColliderAgentRunner |
| 18789 | NanoClawBridge |
| 4200 | FFS6 Frontend |
