@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "LAUNCHER=%SCRIPT_DIR%start-moos-stack.ps1"

if not exist "%LAUNCHER%" (
    echo Error: launcher not found: %LAUNCHER%
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%LAUNCHER%"
exit /b %ERRORLEVEL%
