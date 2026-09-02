@echo off
setlocal

echo =======================================================
echo     TradeAudit Release and Installer Build Wrapper
echo =======================================================

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_installer.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo [DONE] Build completed successfully.
