@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title LabCare 初始化数据库

echo ============================================================
echo   初始化数据库 labcare（首次部署 / 重置演示数据）
echo ============================================================
echo.
echo 警告：该操作会删除并重建 labcare 库中的全部业务表，
echo       已有预约、工单、账号数据都会丢失。
echo.

if not exist "config\local.env" (
    echo [错误] 未找到 config\local.env，请先从 config\local.env.example 复制并填写 MySQL 密码。
    pause
    exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in ("config\local.env") do (
    set "LC_KEY=%%A"
    if not "!LC_KEY!"=="" if not "!LC_KEY:~0,1!"=="#" set "!LC_KEY!=%%B"
)

if "%LAB_DB_PASSWORD%"=="" (
    echo [错误] config\local.env 中的 LAB_DB_PASSWORD 为空。
    pause
    exit /b 1
)

where mysql >nul 2>nul
if errorlevel 1 (
    echo [错误] PATH 中没有 mysql 客户端，请把 MySQL 的 bin 目录加入 PATH。
    pause
    exit /b 1
)

choice /c YN /m "确认继续并重建数据库吗"
if errorlevel 2 exit /b 1

set "MYSQL_PWD=%LAB_DB_PASSWORD%"
echo.
echo 正在执行 db\init.sql ...
mysql -h 127.0.0.1 -P 3306 -u %LAB_DB_USERNAME% --default-character-set=utf8mb4 < "db\init.sql"
if errorlevel 1 (
    echo.
    echo [错误] 初始化失败，请检查上面的错误信息（常见原因：MySQL 未启动、密码错误）。
    pause
    exit /b 1
)

echo.
echo [完成] 数据库已重建，当前数据量：
mysql -h 127.0.0.1 -P 3306 -u %LAB_DB_USERNAME% --default-character-set=utf8mb4 -e "use labcare; select (select count(*) from app_user) as users, (select count(*) from equipment) as equipments, (select count(*) from reservation) as reservations, (select count(*) from repair_ticket) as repairs;"
echo.
echo 演示账号：student01 / Student@123，student02 / Student@123，admin / Admin@123
echo 提示：若后端正在运行，请先双击「停止服务.bat」再重新启动，让知识库索引与数据库一致。
echo.
pause
