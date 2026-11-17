@echo off
rem 业务后端：Spring Boot，JAVA_EXE 由 一键启动.bat 传入，未传则优先 JAVA_HOME
cd /d "%~dp0..\src\backend"
if not defined JAVA_EXE (
    if exist "%JAVA_HOME%\bin\java.exe" set "JAVA_EXE=%JAVA_HOME%\bin\java.exe"
)
if not defined JAVA_EXE set "JAVA_EXE=java"
"%JAVA_EXE%" -jar target\labcare-backend.jar
