param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = "D:/FFS0_Factory",

    [Parameter(Mandatory = $true)]
    [string]$Ffs2Remote,

    [Parameter(Mandatory = $true)]
    [string]$Ffs3Remote
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

Write-Host "[1/4] Splitting FFS2 history branch..."
if (-not (git branch --list split/ffs2)) {
    git subtree split --prefix=workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension -b split/ffs2
}

Write-Host "[2/4] Splitting FFS3 history branch..."
if (-not (git branch --list split/ffs3)) {
    git subtree split --prefix=workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer -b split/ffs3
}

Write-Host "[3/4] Pushing FFS2 split to remote main..."
$null = git remote get-url ffs2 2>$null
if ($LASTEXITCODE -ne 0) { git remote add ffs2 $Ffs2Remote }
git push ffs2 split/ffs2:main

Write-Host "[4/4] Pushing FFS3 split to remote main..."
$null = git remote get-url ffs3 2>$null
if ($LASTEXITCODE -ne 0) { git remote add ffs3 $Ffs3Remote }
git push ffs3 split/ffs3:main

Write-Host "Done. Leaf repositories initialized from monorepo history."
