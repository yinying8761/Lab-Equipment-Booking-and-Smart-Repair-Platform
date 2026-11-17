# 读取 config/local.env 并注入当前进程环境变量
param(
    [string]$ConfigFile = (Join-Path (Split-Path -Parent $PSScriptRoot) 'config/local.env')
)

if (-not (Test-Path $ConfigFile)) {
    Write-Host "未找到 $ConfigFile，将使用默认配置（应从 config/local.env.example 复制）" -ForegroundColor Yellow
    return
}

Get-Content $ConfigFile -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith('#')) {
        $index = $line.IndexOf('=')
        if ($index -gt 0) {
            $name = $line.Substring(0, $index).Trim()
            $value = $line.Substring($index + 1).Trim()
            Set-Item -Path "env:$name" -Value $value
        }
    }
}
Write-Host "已加载本地配置：$ConfigFile" -ForegroundColor Green
