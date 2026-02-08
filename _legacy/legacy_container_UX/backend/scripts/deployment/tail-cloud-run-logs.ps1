param(
    [string]$ProjectId,
    [string]$ServiceName = "my-tiny-data-collider",
    [int]$Limit = 50,
    [switch]$Tail
)

# Attempt to hydrate project id from environment if not provided explicitly.
if (-not $ProjectId) {
    $ProjectId = $env:GCP_PROJECT_ID
}

if (-not $ProjectId) {
    Write-Error "GCP project id not provided. Pass -ProjectId or set GCP_PROJECT_ID environment variable."
    exit 1
}

# Build logging filter with proper quoting for gcloud filter syntax
$filter = 'resource.type="cloud_run_revision" AND resource.labels.service_name="{0}"' -f $ServiceName

if ($Tail) {
    Write-Host "Tailing Cloud Run logs for service '$ServiceName' in project '$ProjectId'..." -ForegroundColor Cyan
    $args = @(
        'beta', 'logging', 'tail',
        $filter,
        '--project', $ProjectId
    )
    Write-Host "Command: gcloud $($args -join ' ')" -ForegroundColor DarkGray
    & gcloud @args
    return
}

Write-Host "Fetching last $Limit log entries for Cloud Run service '$ServiceName' in project '$ProjectId'..." -ForegroundColor Cyan
$args = @(
    'logging', 'read',
    $filter,
    '--project', $ProjectId,
    '--limit', $Limit,
    '--format', 'json'
)
Write-Host "Command: gcloud $($args -join ' ')" -ForegroundColor DarkGray
& gcloud @args
