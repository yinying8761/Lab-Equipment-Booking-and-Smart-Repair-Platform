# 启动 Spring Boot 业务后端（端口 8080）
# 若 jar 不存在、或后端源码/pom 比 jar 新，则先重新构建，避免"改了代码仍跑旧 jar"。
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot 'load-env.ps1')

$backendDir = Join-Path $root 'src/backend'
$jar = Join-Path $backendDir 'target/labcare-backend.jar'

function Test-NeedBuild {
    if (-not (Test-Path $jar)) { return $true }
    $jarTime = (Get-Item $jar).LastWriteTimeUtc
    $sources = @()
    $sources += Get-ChildItem -Path (Join-Path $backendDir 'src/main/java') -Filter *.java -Recurse -File -ErrorAction SilentlyContinue
    $sources += Get-ChildItem -Path (Join-Path $backendDir 'src/main/resources') -File -Recurse -ErrorAction SilentlyContinue
    $pom = Get-Item (Join-Path $backendDir 'pom.xml') -ErrorAction SilentlyContinue
    if ($pom) { $sources += $pom }
    return [bool]($sources | Where-Object { $_.LastWriteTimeUtc -gt $jarTime } | Select-Object -First 1)
}

if (Test-NeedBuild) {
    $listening = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
    if ($listening) {
        Write-Host '错误：8080 端口仍在运行，jar 被占用，无法重新构建。' -ForegroundColor Red
        Write-Host '      请先停止后端进程（如 scripts 或「停止服务.bat」），再重新启动。' -ForegroundColor Yellow
        exit 1
    }
    Write-Host '检测到后端源码有更新，开始重新构建...' -ForegroundColor Yellow
    Push-Location $backendDir
    try {
        & mvn -B -DskipTests clean package
        if ($LASTEXITCODE -ne 0) {
            Write-Host '后端构建失败，请查看上方 Maven 日志。' -ForegroundColor Red
            exit 1
        }
    } finally {
        Pop-Location
    }
}

$java = if ($env:JAVA_HOME) { Join-Path $env:JAVA_HOME 'bin/java.exe' } else { 'java' }
Write-Host "使用 Java：$java" -ForegroundColor Green
& $java -jar $jar
