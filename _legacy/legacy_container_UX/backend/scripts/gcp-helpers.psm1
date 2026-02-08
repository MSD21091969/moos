# GCP Helper Commands for Phase 2/3 Debugging
# Run these in terminal when Copilot needs GCP data

# ==============================================================================
# Cloud Logging - Recent Errors
# ==============================================================================
function Get-CloudRunErrors {
    param([int]$Limit = 20)
    gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=$Limit --format="table(timestamp,textPayload)" --project=mailmind-ai-djbuw
}

# ==============================================================================
# Cloud Logging - Recent Requests
# ==============================================================================
function Get-CloudRunRequests {
    param([int]$Limit = 20)
    gcloud logging read "resource.type=cloud_run_revision AND httpRequest.requestUrl:*" --limit=$Limit --format="table(timestamp,httpRequest.requestMethod,httpRequest.requestUrl,httpRequest.status)" --project=mailmind-ai-djbuw
}

# ==============================================================================
# Cloud Run - Service Status
# ==============================================================================
function Get-CloudRunStatus {
    gcloud run services describe my-tiny-data-collider --region=europe-west4 --format="table(status.url,status.conditions.type,status.conditions.status)" --project=mailmind-ai-djbuw
}

# ==============================================================================
# Cloud Run - Recent Revisions
# ==============================================================================
function Get-CloudRunRevisions {
    gcloud run revisions list --service=my-tiny-data-collider --region=europe-west4 --format="table(name,active,created)" --project=mailmind-ai-djbuw
}

# ==============================================================================
# Firestore - Collection Stats (requires firebase CLI)
# ==============================================================================
function Get-FirestoreCollections {
    gcloud firestore databases describe --database=my-tiny-data-collider --project=mailmind-ai-djbuw
}

# ==============================================================================
# Trace Explorer - Recent Traces
# ==============================================================================
function Get-RecentTraces {
    param([int]$Limit = 10)
    Write-Host "Open in browser: https://console.cloud.google.com/traces/list?project=mailmind-ai-djbuw"
    Write-Host "Or use: gcloud beta trace list --limit=$Limit --project=mailmind-ai-djbuw"
}

# ==============================================================================
# Quick Health Check
# ==============================================================================
function Test-ProductionHealth {
    $response = Invoke-RestMethod -Uri 'https://my-tiny-data-collider-ng2rb7mwyq-ez.a.run.app/health'
    $response | ConvertTo-Json -Depth 5
}

# Export functions
Export-ModuleMember -Function Get-CloudRunErrors, Get-CloudRunRequests, Get-CloudRunStatus, Get-CloudRunRevisions, Get-FirestoreCollections, Get-RecentTraces, Test-ProductionHealth

Write-Host "GCP Helper Functions Loaded:" -ForegroundColor Green
Write-Host "  Get-CloudRunErrors [-Limit 20]"
Write-Host "  Get-CloudRunRequests [-Limit 20]"
Write-Host "  Get-CloudRunStatus"
Write-Host "  Get-CloudRunRevisions"
Write-Host "  Get-FirestoreCollections"
Write-Host "  Get-RecentTraces"
Write-Host "  Test-ProductionHealth"
