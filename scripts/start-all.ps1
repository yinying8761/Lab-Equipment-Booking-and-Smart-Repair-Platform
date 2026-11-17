# 一键启动三个服务（各自打开一个 PowerShell 窗口）
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot

Write-Host '启动 AI 服务（8100）...' -ForegroundColor Cyan
Start-Process pwsh -ArgumentList '-NoExit', '-File', (Join-Path $here 'start-ai.ps1')

Write-Host '启动业务后端（8080）...' -ForegroundColor Cyan
Start-Process pwsh -ArgumentList '-NoExit', '-File', (Join-Path $here 'start-backend.ps1')

Start-Sleep -Seconds 8
Write-Host '启动前端（5173）...' -ForegroundColor Cyan
Start-Process pwsh -ArgumentList '-NoExit', '-File', (Join-Path $here 'start-frontend.ps1')

Start-Sleep -Seconds 6
Write-Host ''
Write-Host '服务启动中，请在浏览器打开：http://localhost:5173' -ForegroundColor Green
Write-Host '演示账号：student01 / Student@123，student02 / Student@123，admin / Admin@123'
