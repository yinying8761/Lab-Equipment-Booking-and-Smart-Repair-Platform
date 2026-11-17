@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LabCare 停止服务

echo ============================================================
echo   停止 LabCare 三个服务
echo ============================================================
echo.

taskkill /FI "WINDOWTITLE eq LabCare-AI*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq LabCare-Backend*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq LabCare-Frontend*" /T /F >nul 2>nul

rem 窗口标题匹配不到时，按端口兜底清理
for %%P in (8080 8100 5173) do (
    for /f "tokens=5" %%I in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do (
        echo [停止] 端口 %%P 上的进程 PID=%%I
        taskkill /PID %%I /F >nul 2>nul
    )
)

echo.
echo 已尝试停止 8080 / 8100 / 5173 三个端口上的服务。
echo 若仍有残留，请手动关闭标题为 LabCare-* 的命令行窗口。
echo.
pause
