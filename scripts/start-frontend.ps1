# 启动 Vue3 前端开发服务（端口 5173，通过 Vite 代理转发 /api 到 8080）
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $root 'src/frontend')

if (-not (Test-Path 'node_modules')) {
    Write-Host '首次运行，安装前端依赖...' -ForegroundColor Yellow
    npm install --registry=https://registry.npmmirror.com --no-audit --no-fund
}

# npm 会把 "npm notice" 之类的正常运行提示写到 stderr，
# 在 ErrorActionPreference='Stop' 下会被 PowerShell 当成终止性错误并结束进程，
# 因此对本条命令临时放宽并显式合并输出。
$ErrorActionPreference = 'Continue'
npm run dev 2>&1 | ForEach-Object { Write-Host $_ }
exit $LASTEXITCODE
