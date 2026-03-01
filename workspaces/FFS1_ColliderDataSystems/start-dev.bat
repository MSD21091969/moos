@echo off
REM Collider Development Environment Startup Script
REM Runs: DataServer (8000), AgentRunner (8004), NanoClawBridge (18789), Frontend (4200)

echo ============================================
echo   Collider Development Environment
echo ============================================
echo.

SET BASE_DIR=%~dp0
SET FFS2_DIR=%BASE_DIR%FFS2_ColliderBackends_MultiAgentChromeExtension
SET DATA_SERVER_DIR=%FFS2_DIR%\ColliderDataServer
SET AGENT_RUNNER_DIR=%FFS2_DIR%\ColliderAgentRunner
SET NANOCLAW_DIR=%FFS2_DIR%\NanoClawBridge
SET FRONTEND_DIR=%BASE_DIR%FFS3_ColliderApplicationsFrontendServer

REM Check if directories exist
for %%d in ("%DATA_SERVER_DIR%" "%AGENT_RUNNER_DIR%" "%NANOCLAW_DIR%" "%FRONTEND_DIR%") do (
    if not exist "%%~d" (
        echo Error: Directory not found: %%~d
        exit /b 1
    )
)

echo [1/5] Starting Data Server (port 8000)...
start "Collider DataServer" cmd /k "cd /d %DATA_SERVER_DIR% && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000"

echo [2/5] Starting Agent Runner (port 8004)...
start "Collider AgentRunner" cmd /k "cd /d %AGENT_RUNNER_DIR% && uv run uvicorn src.main:app --host 0.0.0.0 --port 8004"

echo [3/5] Starting NanoClaw Bridge (port 18789)...
start "Collider NanoClaw" cmd /k "cd /d %NANOCLAW_DIR% && pnpm run dev"

echo [4/5] Starting SQLite Web Viewer (port 8003)...
start "SQLite Viewer" cmd /k "cd /d %DATA_SERVER_DIR% && uv run sqlite_web collider.db --host 0.0.0.0 --port 8003"

echo [5/5] Starting Frontend (port 4200)...
start "Collider Frontend" cmd /k "cd /d %FRONTEND_DIR% && pnpm nx serve ffs6"

echo.
echo ============================================
echo   NanoClaw SDK + gRPC Stack Active!
echo ============================================
echo.
echo   Data Server:       http://localhost:8000
echo   Agent Runner:      http://localhost:8004
echo   NanoClaw Bridge:   http://localhost:18789
echo   Frontend App:      http://localhost:4200
echo.
echo Close individual windows to stop services.
echo.

pause
