@echo off
rem 前端：Vite 开发服务器（/api 通过代理转发到 8080）
cd /d "%~dp0..\src\frontend"
if not exist node_modules (
    echo 未找到 node_modules，正在安装依赖...
    call npm install --userconfig="%~dp0npmrc.clean" --no-audit --no-fund
)
call npm run dev
