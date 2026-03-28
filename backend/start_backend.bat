@echo off
echo ========================================
echo  豆沙包教师助手 - 后端启动脚本
echo ========================================
echo.

REM 检查虚拟环境
if not exist "..\venv\Scripts\python.exe" (
    echo ❌ 错误: 虚拟环境不存在
    echo 请先运行: python -m venv ..\venv
    exit /b 1
)

echo 1. 激活虚拟环境...
call ..\venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 激活虚拟环境失败
    exit /b 1
)

echo 2. 检查依赖...
python -m pip list | find "fastapi" >nul
if errorlevel 1 (
    echo ⚠️  缺少依赖，正在安装...
    python -m pip install -r requirements.txt
)

echo 3. 启动后端服务...
echo 服务启动地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
