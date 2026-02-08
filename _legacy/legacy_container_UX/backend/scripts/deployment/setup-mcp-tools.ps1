#!/usr/bin/env pwsh
# Setup MCP Tools and CLI Configuration for VS Code Copilot

Write-Host "=== MCP Tools & CLI Setup (VS Code Copilot) ===" -ForegroundColor Cyan

# Check GitHub CLI authentication
Write-Host "`n1. Checking GitHub CLI..." -ForegroundColor Yellow
$ghPath = Get-Command gh -ErrorAction SilentlyContinue
if ($ghPath) {
    Write-Host "  Installed: $($ghPath.Source)" -ForegroundColor Green
    $ghAuth = gh auth status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Status: Authenticated" -ForegroundColor Green
    } else {
        Write-Host "  Status: Not authenticated - run 'gh auth login'" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Not installed - run 'winget install GitHub.cli'" -ForegroundColor Red
}

# Check GitKraken CLI
Write-Host "`n2. Checking GitKraken CLI..." -ForegroundColor Yellow
$gkPath = Get-Command gk -ErrorAction SilentlyContinue
if ($gkPath) {
    Write-Host "  Installed: $($gkPath.Source)" -ForegroundColor Green
    Write-Host "  Commands: gk status, gk log, gk pr list" -ForegroundColor Gray
} else {
    Write-Host "  Not found - restart terminal or run 'winget install gitkraken.cli'" -ForegroundColor Yellow
}

# Check VS Code workspace MCP settings
Write-Host "`n3. Checking VS Code MCP settings..." -ForegroundColor Yellow
$workspaceFile = "dev-workspace.code-workspace"
if (Test-Path $workspaceFile) {
    $workspaceContent = Get-Content $workspaceFile -Raw
    if ($workspaceContent -match 'copilot-mcp.mcpServers') {
        Write-Host "  MCP servers configured in workspace" -ForegroundColor Green
        if ($workspaceContent -match 'filesystem') { Write-Host "    - filesystem" -ForegroundColor Gray }
        if ($workspaceContent -match '"github"') { Write-Host "    - github" -ForegroundColor Gray }
        if ($workspaceContent -match '"git"') { Write-Host "    - git" -ForegroundColor Gray }
        if ($workspaceContent -match 'sequential-thinking') { Write-Host "    - sequential-thinking" -ForegroundColor Gray }
    } else {
        Write-Host "  No MCP servers configured" -ForegroundColor Red
    }
} else {
    Write-Host "  Workspace file not found" -ForegroundColor Red
}

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Install extension: automatalabs.copilot-mcp" -ForegroundColor White
Write-Host "2. Restart VS Code to load MCP servers" -ForegroundColor White
Write-Host "3. Restart terminal to use 'gk' command" -ForegroundColor White
Write-Host "4. Test with: @workspace in Copilot Chat" -ForegroundColor White

Write-Host "`n=== Quick Reference ===" -ForegroundColor Cyan
Write-Host "GitHub CLI:    gh repo view | gh pr list" -ForegroundColor Gray
Write-Host "GitKraken CLI: gk status | gk log | gk pr list" -ForegroundColor Gray
Write-Host "GitLens:       Ctrl+Shift+P -> GitLens commands" -ForegroundColor Gray
