# 启动 LangChain AI 服务（端口 8100）
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot 'load-env.ps1')

Set-Location (Join-Path $root 'src/ai-service')
$env:PYTHONIOENCODING = 'utf-8'
if (-not $env:LAB_KNOWLEDGE_DIR) {
    $env:LAB_KNOWLEDGE_DIR = (Join-Path $root 'data/知识库')
}

# uvicorn 会把运行日志写到 stderr。若保持 ErrorActionPreference='Stop'，
# PowerShell 会把这些正常的 INFO 日志当成终止性错误并杀掉进程，
# 因此这里临时放宽，仅对本条原生命令生效。
$ErrorActionPreference = 'Continue'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100 --log-level info 2>&1 |
    ForEach-Object { Write-Host $_ }
exit $LASTEXITCODE
