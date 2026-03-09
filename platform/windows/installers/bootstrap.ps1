param(
    [switch]$ValidateOnly,
    [switch]$PrintResolvedConfig
)

$ErrorActionPreference = 'Stop'

function Fail([string]$Message) {
    Write-Error $Message
    exit 1
}

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
}

function Get-SecretsPath([string]$RepoRoot) {
    $candidates = @(
        (Join-Path $RepoRoot 'secrets\api_keys.env'),
        (Join-Path $RepoRoot '..\secrets\api_keys.env')
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    return $candidates[0]
}

function Read-EnvFile([string]$Path) {
    $values = @{}
    if (-not (Test-Path $Path)) {
        return $values
    }

    Get-Content -Path $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#')) {
            return
        }
        $parts = $line -split '=', 2
        if ($parts.Count -eq 2) {
            $values[$parts[0].Trim()] = $parts[1].Trim()
        }
    }

    return $values
}

function Resolve-Placeholders([string]$Value, [hashtable]$Bindings) {
    return ([regex]::Replace($Value, '\$\{([A-Z0-9_]+)\}', {
        param($match)
        $name = $match.Groups[1].Value
        $envValue = [System.Environment]::GetEnvironmentVariable($name)
        if ($envValue) {
            return $envValue
        }
        if ($Bindings.ContainsKey($name) -and $Bindings[$name]) {
            return $Bindings[$name]
        }
        throw "Missing required secret binding: $name"
    }))
}

function Resolve-EnvPath([string]$RepoRoot, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $Value
    }
    if ([System.IO.Path]::IsPathRooted($Value)) {
        return $Value
    }
    return [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $Value))
}

function Test-PortAvailable([int]$Port) {
    $listeners = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
    return -not ($listeners | Where-Object { $_.Port -eq $Port })
}

function Mask-DatabaseUrl([string]$Value) {
    return ($Value -replace ':(.+?)@', ':***@')
}

function Test-FallbackAvailable([string]$FallbackCommand) {
    if ([string]::IsNullOrWhiteSpace($FallbackCommand)) {
        return $false
    }
    if ($FallbackCommand -like 'go *') {
        return [bool](Get-Command go -ErrorAction SilentlyContinue)
    }
    return $true
}

function Invoke-Fallback([string]$FallbackCommand) {
    if ([string]::IsNullOrWhiteSpace($FallbackCommand)) {
        Fail 'Fallback command is empty.'
    }
    Write-Host "Launching fallback: $FallbackCommand"
    Invoke-Expression $FallbackCommand
}

$repoRoot = Get-RepoRoot
$presetPath = Join-Path $repoRoot 'platform\presets\windows-local-dev.json'
$secretsPath = Get-SecretsPath $repoRoot

if (-not (Test-Path $presetPath)) {
    Fail "Preset not found: $presetPath"
}

$preset = Get-Content -Raw -Path $presetPath | ConvertFrom-Json
if ($preset.schemaVersion -ne '1.0.0') {
    Fail "Unsupported preset schemaVersion '$($preset.schemaVersion)'. Expected 1.0.0."
}

$secretBindings = Read-EnvFile $secretsPath
$resolvedEnv = @{}

foreach ($property in $preset.env.PSObject.Properties) {
    if ($property.Name -eq 'MOOS_DATABASE_URL') {
        continue
    }
    try {
        $resolvedEnv[$property.Name] = Resolve-Placeholders $property.Value $secretBindings
    }
    catch {
        Fail $_.Exception.Message
    }
}

$storeKind = 'file'
if ($resolvedEnv.ContainsKey('MOOS_KERNEL_STORE') -and -not [string]::IsNullOrWhiteSpace($resolvedEnv['MOOS_KERNEL_STORE'])) {
    $storeKind = $resolvedEnv['MOOS_KERNEL_STORE']
}

if ($storeKind -notin @('file', 'postgres')) {
    Fail "Unsupported MOOS_KERNEL_STORE '$storeKind'. Expected 'file' or 'postgres'."
}

if ($storeKind -eq 'postgres') {
    if (-not ($preset.env.PSObject.Properties.Name -contains 'MOOS_DATABASE_URL')) {
        Fail 'Preset is missing MOOS_DATABASE_URL for postgres store mode.'
    }
    try {
        $resolvedEnv['MOOS_DATABASE_URL'] = Resolve-Placeholders $preset.env.MOOS_DATABASE_URL $secretBindings
    }
    catch {
        Fail $_.Exception.Message
    }
}

foreach ($pathKey in @('MOOS_KERNEL_LOG_PATH', 'MOOS_KERNEL_REGISTRY_PATH')) {
    if ($resolvedEnv.ContainsKey($pathKey)) {
        $resolvedEnv[$pathKey] = Resolve-EnvPath $repoRoot $resolvedEnv[$pathKey]
    }
}

foreach ($required in @('MOOS_HTTP_PORT', 'MOOS_AGENT_PORT', 'MOOS_MCP_PORT', 'MOOS_NANOCLAW_PORT')) {
    if (-not $resolvedEnv.ContainsKey($required) -or [string]::IsNullOrWhiteSpace($resolvedEnv[$required])) {
        Fail "Resolved environment value is missing: $required"
    }
}

if ($storeKind -eq 'postgres' -and (-not $resolvedEnv.ContainsKey('MOOS_DATABASE_URL') -or [string]::IsNullOrWhiteSpace($resolvedEnv['MOOS_DATABASE_URL']))) {
    Fail 'Resolved environment value is missing: MOOS_DATABASE_URL'
}

if ($storeKind -eq 'postgres' -and $resolvedEnv['MOOS_DATABASE_URL'] -notmatch 'postgres://.+@.+/.+') {
    Fail 'MOOS_DATABASE_URL does not look like a valid Postgres connection string.'
}

foreach ($portKey in @('MOOS_HTTP_PORT', 'MOOS_AGENT_PORT', 'MOOS_MCP_PORT', 'MOOS_NANOCLAW_PORT')) {
    $port = [int]$resolvedEnv[$portKey]
    if (-not (Test-PortAvailable $port)) {
        Fail "Port $port ($portKey) is already in use."
    }
}

$binaryPath = Join-Path $repoRoot $preset.launcher.path
$binaryExists = Test-Path $binaryPath
$fallbackCommand = [string]$preset.launcher.fallback

if (-not $binaryExists -and -not (Test-FallbackAvailable $fallbackCommand)) {
    Fail "Neither binary '$binaryPath' nor fallback '$fallbackCommand' is available."
}

if ($PrintResolvedConfig) {
    Write-Host 'Resolved non-secret config:'
    Write-Host "  preset: $($preset.id)"
    Write-Host "  store: $storeKind"
    Write-Host "  http: $($resolvedEnv['MOOS_HTTP_PORT'])"
    Write-Host "  agent: $($resolvedEnv['MOOS_AGENT_PORT'])"
    Write-Host "  mcp: $($resolvedEnv['MOOS_MCP_PORT'])"
    Write-Host "  nanoclaw: $($resolvedEnv['MOOS_NANOCLAW_PORT'])"
    if ($storeKind -eq 'postgres') {
        Write-Host "  db: $(Mask-DatabaseUrl $resolvedEnv['MOOS_DATABASE_URL'])"
    }
}

if ($ValidateOnly) {
    Write-Host 'Preflight validation passed.'
    exit 0
}

foreach ($key in $resolvedEnv.Keys) {
    [System.Environment]::SetEnvironmentVariable($key, $resolvedEnv[$key], 'Process')
}

Push-Location $repoRoot
try {
    if ($binaryExists) {
        Write-Host "Launching kernel binary: $binaryPath"
        & $binaryPath
    }
    else {
        Invoke-Fallback $fallbackCommand
    }
}
finally {
    Pop-Location
}
