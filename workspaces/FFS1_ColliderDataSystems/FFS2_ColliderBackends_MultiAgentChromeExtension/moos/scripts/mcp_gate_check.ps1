param(
    [string]$BaseUrl = 'http://127.0.0.1:8080',
    [string]$Token = 'phase3-token',
    [string]$SessionId = 'gate'
)

$ErrorActionPreference = 'Stop'
$auth = @{ Authorization = "Bearer $Token"; 'Content-Type' = 'application/json' }

$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    try {
        $health = Invoke-WebRequest "$BaseUrl/health" -UseBasicParsing -TimeoutSec 2
        if ($health.StatusCode -eq 200) { $ready = $true; break }
    }
    catch {}
    Start-Sleep -Milliseconds 500
}
if (-not $ready) { throw "Kernel not ready at $BaseUrl" }

$results = [ordered]@{}

try {
    $unauth = Invoke-WebRequest "$BaseUrl/mcp/messages?sessionId=$SessionId" -Method Post -Body '{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}' -ContentType 'application/json' -UseBasicParsing -TimeoutSec 5
    $results['unauthorized'] = "unexpected_status_$($unauth.StatusCode)"
}
catch {
    $code = $_.Exception.Response.StatusCode.value__
    $results['unauthorized'] = if ($code -eq 401) { 'pass' } else { "fail_$code" }
}

$init = Invoke-RestMethod "$BaseUrl/mcp/messages?sessionId=$SessionId" -Method Post -Headers $auth -Body '{"jsonrpc":"2.0","id":2,"method":"initialize","params":{}}' -TimeoutSec 8
$results['initialize'] = if ($init.result.protocolVersion -and $init.result.sessionId -eq $SessionId) { 'pass' } else { 'fail' }

$tools = Invoke-RestMethod "$BaseUrl/mcp/messages?sessionId=$SessionId" -Method Post -Headers $auth -Body '{"jsonrpc":"2.0","id":3,"method":"tools/list","params":{}}' -TimeoutSec 8
$toolNames = @($tools.result.tools | ForEach-Object { $_.name })
$results['tools_list'] = if ($toolNames -contains 'echo' -and $toolNames -contains 'list_children' -and $toolNames -contains 'read_kernel' -and $toolNames -contains 'search') { 'pass' } else { 'fail' }

$echoReq = '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"echo","arguments":{"hello":"world"}}}'
$echo = Invoke-RestMethod "$BaseUrl/mcp/messages?sessionId=$SessionId" -Method Post -Headers $auth -Body $echoReq -TimeoutSec 8
$results['tools_call_echo'] = if ($echo.result.output.echo.hello -eq 'world') { 'pass' } else { 'fail' }

$blockedReq = '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"internal_secret","arguments":{}}}'
$blocked = Invoke-RestMethod "$BaseUrl/mcp/messages?sessionId=$SessionId" -Method Post -Headers $auth -Body $blockedReq -TimeoutSec 8
$results['blocked_prefix'] = if ($blocked.error.message -match 'blocked') { 'pass' } else { 'fail' }

$huge = 'x' * 20000
$sizeReq = @{ jsonrpc = '2.0'; id = 6; method = 'tools/call'; params = @{ name = 'echo'; arguments = @{ payload = $huge } } } | ConvertTo-Json -Depth 8 -Compress
$size = Invoke-RestMethod "$BaseUrl/mcp/messages?sessionId=$SessionId" -Method Post -Headers $auth -Body $sizeReq -TimeoutSec 8
$results['size_limit'] = if ($size.error.message -match 'exceeds max bytes') { 'pass' } else { 'fail' }

$cancelReq = '{"jsonrpc":"2.0","id":7,"method":"$/cancelRequest","params":{"id":999}}'
$cancel = Invoke-RestMethod "$BaseUrl/mcp/messages?sessionId=$SessionId" -Method Post -Headers $auth -Body $cancelReq -TimeoutSec 8
$results['cancel_semantics'] = if ($cancel.result.cancelled -eq $false) { 'pass' } else { 'fail' }

$sse = & curl.exe -sS -N --max-time 2 -H "Authorization: Bearer $Token" "$BaseUrl/mcp/sse?sessionId=$SessionId"
$results['sse_endpoint'] = if (($sse -match 'event: endpoint') -and ($sse -match "/mcp/messages\?sessionId=$SessionId")) { 'pass' } else { 'fail' }

$ping = Invoke-RestMethod "$BaseUrl/mcp/messages?sessionId=$SessionId" -Method Post -Headers $auth -Body '{"jsonrpc":"2.0","id":8,"method":"ping","params":{}}' -TimeoutSec 8
$results['ping'] = if ($ping.result.pong -eq $true) { 'pass' } else { 'fail' }

$failed = @()
foreach ($entry in $results.GetEnumerator()) {
    Write-Output ("CHECK {0}: {1}" -f $entry.Key, $entry.Value)
    if ($entry.Value -ne 'pass') { $failed += ("{0}:{1}" -f $entry.Key, $entry.Value) }
}

if ($failed.Count -gt 0) {
    throw ("MCP gate failed: " + ($failed -join ', '))
}

Write-Output 'PHASE3_MCP_GATE_RUNTIME_OK'
