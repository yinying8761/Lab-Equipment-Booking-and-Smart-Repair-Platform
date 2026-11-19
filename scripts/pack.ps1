# 打包提交材料：生成以“系统名称-组长班级-组长姓名”为第一层的 zip
param(
    [string]$ClassName = '【组长班级】',
    [string]$LeaderName = '【组长姓名】',
    [string]$SystemName = '实验室设备预约与智能报修平台'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$folderName = "$SystemName-$ClassName-$LeaderName"
$staging = Join-Path $env:TEMP "labcare-pack-$([guid]::NewGuid().ToString('N').Substring(0,8))"
$target = Join-Path $staging $folderName
New-Item -ItemType Directory -Force -Path $target | Out-Null

Write-Host "复制源码到 $target ..." -ForegroundColor Cyan
# 排除依赖、构建产物、本地密钥、向量库与版本库
$excludeDirs = @('node_modules', 'target', 'dist', '.git', '.idea', '.vscode', 'chroma', '__pycache__', '.pytest_cache', 'uploads')
robocopy $root $target /E /NFL /NDL /NJH /NJS /NP /XD `
    (Join-Path $root 'src\frontend\node_modules') `
    (Join-Path $root 'src\backend\target') `
    (Join-Path $root 'src\frontend\dist') `
    (Join-Path $root 'data\chroma') `
    (Join-Path $root '.git') | Out-Null

# 兜底清理
$cleanup = @(
    'src\frontend\node_modules', 'src\backend\target', 'src\frontend\dist',
    'data\chroma', 'config\local.env', '.git'
)
foreach ($item in $cleanup) {
    $path = Join-Path $target $item
    if (Test-Path $path) { Remove-Item -LiteralPath $path -Recurse -Force }
}
Get-ChildItem $target -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force
Get-ChildItem $target -Recurse -Directory -Filter 'uploads' -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force

# 校验：不得残留真实密钥（只匹配真实形态，配置模板中的占位符不算）
$patterns = @('sk-[A-Za-z0-9]{20,}', 'LAB_DB_PASSWORD=(?!请填写)[^\s]+')
$hits = Get-ChildItem $target -Recurse -File -Include *.env,*.yml,*.yaml,*.md,*.py,*.java,*.js,*.vue |
    Select-String -Pattern $patterns -SimpleMatch:$false -ErrorAction SilentlyContinue
if ($hits) {
    Write-Host '警告：以下文件疑似包含真实密钥或密码，请检查后再提交：' -ForegroundColor Red
    $hits | ForEach-Object { Write-Host ("  " + $_.Path.Replace($target, '')) }
} else {
    Write-Host '密钥检查：未发现真实密码或 API Key' -ForegroundColor Green
}

$zip = Join-Path $root "$folderName.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $target -DestinationPath $zip -CompressionLevel Optimal

$size = [math]::Round((Get-Item $zip).Length / 1MB, 1)
$files = (Get-ChildItem $target -Recurse -File).Count
Write-Host "已生成 $zip（$size MB，$files 个文件）" -ForegroundColor Green
Remove-Item -LiteralPath $staging -Recurse -Force
