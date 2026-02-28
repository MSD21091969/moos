param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = "D:/FFS0_Factory",

    [Parameter(Mandatory = $true)]
    [string]$Ffs1Remote
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

Write-Host "Replacing embedded FFS1 workspace with submodule..."
if (Test-Path "workspaces/FFS1_ColliderDataSystems") {
    Remove-Item -Recurse -Force "workspaces/FFS1_ColliderDataSystems"
}

if (-not (Test-Path "workspaces")) {
    New-Item -ItemType Directory -Path "workspaces" | Out-Null
}

git submodule add $Ffs1Remote workspaces/FFS1_ColliderDataSystems
git add -A
git commit -m "chore: mount FFS1 as submodule"

Write-Host "FFS0 superrepo ready."
