# 启动 LangChain AI 服务（端口 8100）
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot 'load-env.ps1')

Set-Location (Join-Path $root 'src/ai-service')
$env:PYTHONIOENCODING = 'utf-8'
if (-not $env:LAB_KNOWLEDGE_DIR) {
    $env:LAB_KNOWLEDGE_DIR = (Join-Path $root 'data/知识库')
}
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100 --log-level info
