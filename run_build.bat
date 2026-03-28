@echo off
chcp 65001 > nul
cd /d "c:\Users\Lenovo\Desktop\豆沙包教师助手"
echo.
echo ========================================
echo Running TypeScript Lint Check...
echo ========================================
call npm run lint
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Lint check failed!
    exit /b 1
)
echo.
echo ✅ Lint check passed!
echo.
echo ========================================
echo Running Frontend Build...
echo ========================================
call npm run build
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Build failed!
    exit /b 1
)
echo.
echo ✅ Build completed successfully!
exit /b 0
