@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   豆沙包教师助手 - GitHub 推送脚本
echo ========================================
echo.

cd /d "%~dp0"

REM 检查 Git 配置
echo [1] 检查 Git 配置...
git config user.name > nul 2>&1
if errorlevel 1 (
    echo 未配置 Git 用户名，请输入:
    set /p GIT_USER="用户名: "
    git config user.name "!GIT_USER!"
)

git config user.email > nul 2>&1
if errorlevel 1 (
    echo 未配置 Git 邮箱，请输入:
    set /p GIT_EMAIL="邮箱: "
    git config user.email "!GIT_EMAIL!"
)

echo ✓ Git 配置完成
echo.

REM 检查远程仓库
echo [2] 检查远程仓库...
git remote -v | findstr "origin" > nul 2>&1
if errorlevel 1 (
    echo 未配置远程仓库，请输入 GitHub 仓库 URL:
    set /p REPO_URL="仓库 URL (例如: https://github.com/username/repo.git): "
    git remote add origin "!REPO_URL!"
    echo ✓ 远程仓库已添加
) else (
    echo ✓ 远程仓库已配置
    git remote -v | findstr "origin"
)
echo.

REM 检查未提交的更改
echo [3] 检查本地状态...
git status --short
echo.

REM 询问是否提交
echo [4] 添加更改...
set /p CONFIRM="是否添加所有更改？(y/n): "
if /i "!CONFIRM!"=="y" (
    git add .
    echo ✓ 已添加所有更改
) else (
    echo 已跳过
    goto :END
)
echo.

REM 输入提交信息
echo [5] 输入提交信息...
set /p COMMIT_MSG="提交信息 (默认: Fix: 添加 openai-whisper 依赖): "
if "!COMMIT_MSG!"=="" (
    set COMMIT_MSG=Fix: 添加 openai-whisper 依赖
)

REM 提交
git commit -m "!COMMIT_MSG!" --trailer="Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
if errorlevel 1 (
    echo ⚠ 没有更改需要提交或提交失败
    goto :END
)
echo ✓ 提交成功
echo.

REM 获取当前分支
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set CURRENT_BRANCH=%%i

REM 推送
echo [6] 推送到 GitHub...
echo 目标: origin/%CURRENT_BRANCH%
echo.
git push origin %CURRENT_BRANCH%
if errorlevel 1 (
    echo ✗ 推送失败！
    echo 请检查:
    echo   1. 远程仓库 URL 是否正确
    echo   2. 是否有推送权限
    echo   3. 网络连接是否正常
    goto :END
)
echo.
echo ✓ 推送成功！
echo.

:END
echo ========================================
echo   完成
echo ========================================
echo.
pause
