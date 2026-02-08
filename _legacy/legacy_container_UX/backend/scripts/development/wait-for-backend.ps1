param (
    [int]$TimeoutSec = 60
)

$ErrorActionPreference = "SilentlyContinue"
$Uri = "http://localhost:8000/health"
$RetryInterval = 1

Write-Host "🔍 Waiting for Backend at $Uri (Max ${TimeoutSec}s)..." -NoNewline

$sw = [System.Diagnostics.Stopwatch]::StartNew()

for ($i = 0; $i -lt $TimeoutSec; $i++) {
    try {
        $client = [System.Net.Http.HttpClient]::new()
        $client.Timeout = [TimeSpan]::FromSeconds(1)
        
        # Async call with timeout
        $task = $client.GetAsync($Uri)
        
        # Wait for task to complete or timeout (1000ms)
        if ($task.Wait(1000)) {
            $response = $task.Result
            if ($response.IsSuccessStatusCode) {
                $content = $response.Content.ReadAsStringAsync().Result
                # Simple check for "healthy" in JSON response
                if ($content -match "healthy") {
                    $sw.Stop()
                    Write-Host "`n✅ Backend is UP and HEALTHY in $($sw.Elapsed.TotalSeconds.ToString("N2"))s." -ForegroundColor Green
                    $client.Dispose()
                    exit 0
                }
            }
        }
        $client.Dispose()
    } catch {
        # Ignore connection errors
    }
    
    if ($i % 5 -eq 0) {
        Write-Host "." -NoNewline
    }
    Start-Sleep -Seconds $RetryInterval
}

$sw.Stop()
Write-Host "`n❌ Backend failed to start within $TimeoutSec seconds (Elapsed: $($sw.Elapsed.TotalSeconds.ToString("N2"))s)." -ForegroundColor Red
exit 1
