# Bootstrap: Windows Local Development
# Loads the windows-local-dev preset, resolves paths, and launches the kernel.

param(
    [string]$Preset = "windows-local-dev",
    [switch]$Seed
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$PresetPath = Join-Path $WorkspaceRoot "platform\presets\$Preset.json"

if (-not (Test-Path $PresetPath)) {
    Write-Error "Preset not found: $PresetPath"
    return
}

$preset = Get-Content $PresetPath -Raw | ConvertFrom-Json

# Set environment variables from preset (resolve relative paths to absolute)
foreach ($prop in $preset.environment.PSObject.Properties) {
    $val = $prop.Value
    # Resolve relative paths against workspace root
    if ($val -match '\.jsonl$|\.json$') {
        $val = Join-Path $WorkspaceRoot $val
    }
    [System.Environment]::SetEnvironmentVariable($prop.Name, $val, "Process")
    Write-Host "  $($prop.Name) = $val"
}

# Build kernel binary
$KernelDir = Join-Path $WorkspaceRoot "platform\kernel"
Write-Host "`nBuilding kernel..."
Push-Location $KernelDir
go build -o "$KernelDir\moos.exe" ./cmd/moos
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Error "Kernel build failed"
    return
}
Pop-Location
Write-Host "  Built: $KernelDir\moos.exe"

# Launch
Write-Host "`nLaunching kernel on $($preset.environment.MOOS_KERNEL_LISTEN_ADDR)..."
& "$KernelDir\moos.exe"
