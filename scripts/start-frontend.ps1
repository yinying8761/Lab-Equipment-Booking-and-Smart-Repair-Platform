# 启动 Vue3 前端开发服务（端口 5173，通过 Vite 代理转发 /api 到 8080）
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $root 'src/frontend')

if (-not (Test-Path 'node_modules')) {
    Write-Host '首次运行，安装前端依赖...' -ForegroundColor Yellow
    npm install --registry=https://registry.npmmirror.com --no-audit --no-fund
}

npm run dev
