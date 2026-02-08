# Quick Help - Workflow Commands
# Usage: .\show-help.ps1 [keyword]
# Example: .\show-help.ps1 snapshot

param(
    [string]$Keyword = ""
)

$commands = @{
    "session" = @{
        Title = "🎯 Testing Session Commands"
        Commands = @(
            "Start Testing Session     - Kill processes + start dev server (demo mode)",
            "Snapshot Edge             - Capture state + diff with previous snapshot",
            "Cleanup Processes         - Kill all Node.js processes",
            "Check localStorage        - Read workspace-storage from Edge",
            "Reset demo data           - Clear localStorage + reload page"
        )
    }
    "mode" = @{
        Title = "🔧 Development Mode Commands"
        Commands = @(
            "Start Demo Mode           - localStorage only (no backend)",
            "Start Cloud Mode          - Cloud Run backend + auth required",
            "Start Local Backend       - localhost:8000 FastAPI backend"
        )
    }
    "debug" = @{
        Title = "🐛 Debugging Commands"
        Commands = @(
            "Debug position persistence       - Investigate drag-not-persisting bug",
            "Debug session count mismatch     - Compare localStorage vs UI counts",
            "Debug marquee multi-delete       - Test multi-select delete flow",
            "Verify [feature-name]            - End-to-end feature validation",
            "Document bug: [description]      - Create bug entry with evidence"
        )
    }
    "inspect" = @{
        Title = "🔍 Inspection Commands"
        Commands = @(
            "Inspect Canvas State      - Dump ReactFlow + Zustand state",
            "Show Edge console errors  - Display console.error messages",
            "Compare with snapshot [timestamp] - Diff against specific snapshot"
        )
    }
    "tasks" = @{
        Title = "⚙️ VS Code Tasks (Ctrl+Shift+P → Tasks: Run Task)"
        Commands = @(
            "Start Testing Session            - Main UX testing workflow",
            "Snapshot Edge Browser            - Run snapshot script",
            "Cleanup Node Processes           - Kill Node processes",
            "Full CI Check                    - Ruff + MyPy + Tests + Coverage",
            "Phase A: Run Full Audit          - Complete audit workflow"
        )
    }
    "scripts" = @{
        Title = "📜 Terminal Scripts"
        Commands = @(
            "npx tsx scripts/snapshot-edge.ts        - Capture + diff Edge state",
            ".\scripts\cleanup-processes.ps1         - Kill Node processes",
            "npx tsx scripts/connect-to-edge.ts      - Read localStorage only",
            "python scripts/logfire_tail.py --hours 6 --min-level warn - Logfire analysis"
        )
    }
}

function Show-All {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          MY TINY DATA COLLIDER - WORKFLOW COMMANDS            ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($category in $commands.Keys | Sort-Object) {
        Write-Host $commands[$category].Title -ForegroundColor Yellow
        Write-Host ("─" * 70) -ForegroundColor DarkGray
        foreach ($cmd in $commands[$category].Commands) {
            Write-Host "  $cmd" -ForegroundColor Gray
        }
        Write-Host ""
    }
    
    Write-Host "📖 Full documentation: frontend/docs/WORKFLOW-COMMANDS.md" -ForegroundColor Green
    Write-Host "🔍 Filter help: .\show-help.ps1 [keyword]" -ForegroundColor Green
    Write-Host "   Examples: .\show-help.ps1 debug" -ForegroundColor DarkGray
    Write-Host "             .\show-help.ps1 snapshot" -ForegroundColor DarkGray
    Write-Host ""
}

function Show-Filtered {
    param([string]$Filter)
    
    Write-Host ""
    Write-Host "🔍 Commands matching '$Filter':" -ForegroundColor Cyan
    Write-Host ("─" * 70) -ForegroundColor DarkGray
    
    $found = $false
    foreach ($category in $commands.Keys) {
        $matchingCommands = $commands[$category].Commands | Where-Object { $_ -like "*$Filter*" }
        if ($matchingCommands.Count -gt 0) {
            $found = $true
            Write-Host ""
            Write-Host $commands[$category].Title -ForegroundColor Yellow
            foreach ($cmd in $matchingCommands) {
                Write-Host "  $cmd" -ForegroundColor Gray
            }
        }
    }
    
    if (-not $found) {
        Write-Host ""
        Write-Host "❌ No commands found matching '$Filter'" -ForegroundColor Red
        Write-Host "💡 Try: session, mode, debug, inspect, tasks, scripts" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# Main
if ($Keyword -eq "") {
    Show-All
} else {
    Show-Filtered -Filter $Keyword
}
