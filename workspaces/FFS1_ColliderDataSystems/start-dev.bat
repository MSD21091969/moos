@echo off
REM Collider Development Environment Startup Script
REM Runs: Backend API (8000), SQLite Viewer (8003), Frontend (4200)

echo ============================================
echo   Collider Development Environment
echo ============================================
echo.

SET BASE_DIR=%~dp0
SET BACKEND_DIR=%BASE_DIR%FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
SET FRONTEND_DIR=%BASE_DIR%FFS3_ColliderApplicationsFrontendServer

REM Check if directories exist
if not exist "%BACKEND_DIR%" (
    echo Error: Backend directory not found
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    echo Error: Frontend directory not found
    exit /b 1
)

echo [1/4] Installing backend dependencies...
cd /d "%BACKEND_DIR%"
call uv sync
if errorlevel 1 (
    echo Error: Failed to install backend dependencies
    exit /b 1
)

echo.
echo [2/4] Starting Backend API (port 8000)...
start "Collider Backend" cmd /k "cd /d %BACKEND_DIR% && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000"

echo Done! Backend API starting on http://localhost:8000
timeout /t 2 >nul

echo.
echo [3/4] Starting SQLite Web Viewer (port 8003)...
start "SQLite Viewer" cmd /k "cd /d %BACKEND_DIR% && uv run sqlite_web collider.db --host 0.0.0.0 --port 8003"

echo Done! SQLite Viewer starting on http://localhost:8003
timeout /t 2 >nul

echo.
echo [4/4] Starting Frontend (port 4200)...
start "Collider Frontend" cmd /k "cd /d %FRONTEND_DIR% && pnpm nx serve ffs6"

echo Done! Frontend starting on http://localhost:4200
timeout /t 2 >nul

echo.
echo ============================================
echo   All services running!
echo ============================================
echo.
echo   Backend API:       http://localhost:8000
echo   Database Viewer:   http://localhost:8003
echo   Frontend App:      http://localhost:4200
echo.
echo   API Docs:          http://localhost:8000/docs
echo.
echo Close the individual windows to stop services
echo.

pause
