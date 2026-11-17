# 启动 Spring Boot 业务后端（端口 8080）
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot 'load-env.ps1')

$jar = Join-Path $root 'src/backend/target/labcare-backend.jar'
if (-not (Test-Path $jar)) {
    Write-Host '未找到 jar，开始构建后端...' -ForegroundColor Yellow
    Push-Location (Join-Path $root 'src/backend')
    mvn -B -DskipTests package
    Pop-Location
}

$java = if ($env:JAVA_HOME) { Join-Path $env:JAVA_HOME 'bin/java.exe' } else { 'java' }
Write-Host "使用 Java：$java" -ForegroundColor Green
& $java -jar $jar
