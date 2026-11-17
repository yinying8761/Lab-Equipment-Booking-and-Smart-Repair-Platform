@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title LabCare 启动器

echo ============================================================
echo   LabCare 实验室设备预约与智能报修平台 - 一键启动
echo ============================================================
echo.

rem ========== 1. 读取本地配置 ==========
if not exist "config\local.env" (
    echo [提示] 未找到 config\local.env，正在从模板生成...
    copy "config\local.env.example" "config\local.env" >nul
    echo.
    echo 请在弹出的记事本中填写本机 MySQL 密码 LAB_DB_PASSWORD，保存后重新双击本文件。
    notepad "config\local.env"
    pause
    exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in ("config\local.env") do (
    set "LC_KEY=%%A"
    if not "!LC_KEY!"=="" if not "!LC_KEY:~0,1!"=="#" set "!LC_KEY!=%%B"
)

if "%LAB_DB_PASSWORD%"=="" (
    echo [错误] config\local.env 中的 LAB_DB_PASSWORD 为空，请先填写 MySQL 密码。
    pause
    exit /b 1
)

rem 知识库目录固定为项目内绝对路径，避免相对路径随启动目录变化
set "LAB_KNOWLEDGE_DIR=%CD%\data\知识库"
set "MYSQL_PWD=%LAB_DB_PASSWORD%"
echo [配置] 数据库：%LAB_DB_USERNAME%@127.0.0.1:3306/labcare
echo [配置] 知识库：%LAB_KNOWLEDGE_DIR%
echo.

rem ========== 2. 端口占用检查 ==========
set "PORT_BUSY="
for %%P in (8080 8100 5173) do (
    for /f "tokens=5" %%I in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do set "PORT_BUSY=%%P"
)
if defined PORT_BUSY (
    echo [提示] 端口 %PORT_BUSY% 已被占用，可能是上次启动的服务还在运行。
    echo        如需重启，请先双击「停止服务.bat」。
    echo.
    choice /c YN /m "仍然继续启动吗"
    if errorlevel 2 exit /b 1
)
echo.

rem ========== 3. 检查 Java ==========
set "JAVA_EXE="
if exist "%JAVA_HOME%\bin\java.exe" set "JAVA_EXE=%JAVA_HOME%\bin\java.exe"
if not defined JAVA_EXE (
    for /f "delims=" %%J in ('where java 2^>nul') do if not defined JAVA_EXE set "JAVA_EXE=%%J"
)
if not defined JAVA_EXE (
    echo [错误] 未找到 Java。请安装 JDK 21 并设置 JAVA_HOME。
    pause
    exit /b 1
)
echo [环境] Java：%JAVA_EXE%
"%JAVA_EXE%" -version > "%TEMP%\labcare_java.txt" 2>&1
findstr /c:"1.8." "%TEMP%\labcare_java.txt" >nul 2>nul
if not errorlevel 1 (
    del "%TEMP%\labcare_java.txt" >nul 2>nul
    echo [错误] 当前 Java 是 1.8，本项目需要 JDK 21 及以上。
    echo        请安装 JDK 21 并把 JAVA_HOME 指向它，例如：
    echo        setx JAVA_HOME "D:\Java\Java21"
    pause
    exit /b 1
)
del "%TEMP%\labcare_java.txt" >nul 2>nul

rem ========== 4. 检查 Node.js / Python / MySQL ==========
where node >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请安装 Node 18 及以上版本。
    pause
    exit /b 1
)
where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 Python，请安装 Python 3.11 及以上版本。
    pause
    exit /b 1
)
where mysql >nul 2>nul
if errorlevel 1 (
    echo [警告] PATH 中没有 mysql 客户端，跳过数据库连通性检查。
) else (
    mysql -h 127.0.0.1 -u %LAB_DB_USERNAME% -e "use labcare;" >nul 2>nul
    if errorlevel 1 (
        echo [错误] 无法连接数据库 labcare。
        echo        请确认 MySQL 已启动，并先运行「初始化数据库.bat」。
        pause
        exit /b 1
    )
)
echo [环境] Node / Python / MySQL 检查通过
echo.

rem ========== 5. 首次运行准备 ==========
if not exist "src\backend\target\labcare-backend.jar" (
    echo [准备] 未找到后端 jar，开始构建（首次约 1-2 分钟）...
    where mvn >nul 2>nul
    if errorlevel 1 (
        echo [错误] 未找到 Maven，无法自动构建。请安装 Maven 或在 IDEA 中打包后重试。
        pause
        exit /b 1
    )
    pushd "src\backend"
    call mvn -B -q -DskipTests package
    if errorlevel 1 (
        echo [错误] 后端构建失败，请查看上方日志。
        popd
        pause
        exit /b 1
    )
    popd
)

if not exist "src\frontend\node_modules" (
    echo [准备] 未找到前端依赖，开始安装（首次约 1-2 分钟）...
    pushd "src\frontend"
    call npm install --userconfig="%CD%\..\..\scripts\npmrc.clean" --no-audit --no-fund
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败，请检查网络。
        popd
        pause
        exit /b 1
    )
    popd
)
echo.

rem ========== 6. 启动三个服务 ==========
echo [启动] AI 服务（8100）...
start "LabCare-AI" cmd /k "scripts\run-ai.bat"

echo [启动] 业务后端（8080）...
start "LabCare-Backend" cmd /k "scripts\run-backend.bat"

echo [启动] 前端（5173）...
start "LabCare-Frontend" cmd /k "scripts\run-frontend.bat"

echo.
echo 正在等待服务就绪（最多 60 秒）...
set "READY=0"
for /l %%N in (1,1,30) do (
    if "!READY!"=="0" (
        ping -n 3 127.0.0.1 >nul
        curl -s -o nul http://127.0.0.1:8080/api/health
        if not errorlevel 1 (
            curl -s -o nul http://localhost:5173/
            if not errorlevel 1 set "READY=1"
        )
    )
)

echo.
if "!READY!"=="1" (
    echo [成功] 服务已启动，浏览器将自动打开。
) else (
    echo [提示] 等待超时，请查看三个服务窗口中的报错信息。
)
echo.
echo ------------------------------------------------------------
echo   访问地址：http://localhost:5173
echo   演示账号：student01 / Student@123    普通用户
echo             student02 / Student@123    普通用户
echo             admin     / Admin@123      管理员
echo   停止服务：双击「停止服务.bat」
echo ------------------------------------------------------------
echo.
start "" http://localhost:5173
pause
