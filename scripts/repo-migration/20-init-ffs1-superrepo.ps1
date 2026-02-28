param(
    [Parameter(Mandatory = $true)]
    [string]$Ffs1RepoRoot,

    [Parameter(Mandatory = $true)]
    [string]$Ffs2Remote,

    [Parameter(Mandatory = $true)]
    [string]$Ffs3Remote
)

$ErrorActionPreference = "Stop"
Set-Location $Ffs1RepoRoot

if (-not (Test-Path ".git")) {
    git init
}

Write-Host "Resetting embedded leaf folders before submodule mount..."
if (Test-Path "FFS2_ColliderBackends_MultiAgentChromeExtension") {
    Remove-Item -Recurse -Force "FFS2_ColliderBackends_MultiAgentChromeExtension"
}
if (Test-Path "FFS3_ColliderApplicationsFrontendServer") {
    Remove-Item -Recurse -Force "FFS3_ColliderApplicationsFrontendServer"
}

Write-Host "Adding FFS2 and FFS3 as submodules..."
git submodule add $Ffs2Remote FFS2_ColliderBackends_MultiAgentChromeExtension
git submodule add $Ffs3Remote FFS3_ColliderApplicationsFrontendServer

git add -A
git commit -m "chore: mount FFS2 and FFS3 as submodules"

Write-Host "FFS1 superrepo initialized."
