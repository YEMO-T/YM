@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   开始推送到 GitHub...
echo ========================================
echo.

cd /d "%~dp0"

REM 显示当前状态
echo [1/4] 检查本地状态...
git status --short
echo.

REM 添加所有更改
echo [2/4] 添加所有更改...
git add .
echo ✓ 完成

REM 创建提交
echo.
echo [3/4] 创建提交...
git commit -m "Fix: 添加 openai-whisper 依赖并优化项目配置

- 添加 openai-whisper 支持语音转文本功能
- 删除无用的导入文件
- 优化项目配置"

if errorlevel 1 (
    echo ✗ 提交失败！
    pause
    exit /b 1
)
echo ✓ 完成

REM 推送到 GitHub
echo.
echo [4/4] 推送到 GitHub...
echo 目标: origin/main
echo.
git push origin main -v

if errorlevel 1 (
    echo.
    echo ✗ 推送失败！
    echo.
    echo 可能的原因：
    echo 1. 网络连接问题
    echo 2. GitHub 认证失败
    echo 3. 无推送权限
    echo.
    echo 请检查后重试或运行命令：
    echo git push origin main
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✓ 推送成功！
echo ========================================
echo.
echo 访问你的 GitHub 仓库确认：
echo https://github.com/YEMO-T/YM
echo.
pause
