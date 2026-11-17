@echo off
rem AI 服务：FastAPI + LangChain + Chroma
cd /d "%~dp0..\src\ai-service"
set "PYTHONIOENCODING=utf-8"
if not defined LAB_KNOWLEDGE_DIR set "LAB_KNOWLEDGE_DIR=%~dp0..\data\知识库"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
