$template = @'
# Bug List

**Last Updated:** YYYY-MM-DD
**Current Cycle:** [Phase 1 | Phase 2 | Phase 3]

## Phase [N] Status: [PASSED | IN PROGRESS | PENDING]

| ID | Description | Status | Priority | Owner | Notes |
|----|-------------|--------|----------|-------|-------|
| P[N]-01 | Description | 🔴 Open | High | Copilot | Notes |
'@

$targetPath = Join-Path $PSScriptRoot "..\..\BUG_LIST.md"
Set-Content -Path $targetPath -Value $template -Encoding UTF8
Write-Host "✅ BUG_LIST.md has been reset to the new template."
