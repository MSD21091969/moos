$ErrorActionPreference = "Stop"

# Get current branch
$branch = git rev-parse --abbrev-ref HEAD
if (-not $branch) {
    Write-Error "Could not determine current git branch."
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Synchronizing Branch: $branch" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Define our known remotes
$remotes = @("origin", "ffs1", "ffs2", "ffs3")

foreach ($remote in $remotes) {
    # Check if remote exists
    $remoteExists = git remote 2>$null | Select-String -Pattern "^$remote$" -Quiet
    
    if ($remoteExists) {
        Write-Host "`n>>> Pushing to '$remote'..." -ForegroundColor Green
        git push $remote $branch
    } else {
        Write-Host "`n>>> Skipping '$remote' (remote not configured)." -ForegroundColor Yellow
    }
}

Write-Host "`nAll configured remotes have been updated!" -ForegroundColor Green
