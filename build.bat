@echo off
title WorkBuddy Windows ARM64 一键原生构建工具

echo ================================================================================
echo           WorkBuddy Windows ARM64 原生应用一键构建工具
echo ================================================================================
echo.
echo 本工具将自动检测环境、从官方 API 获取最新 WorkBuddy 发布版本、
echo 解包并重编译 better-sqlite3 C++ 插件、重载 WorkBuddy.exe 图标并打包。
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] 错误: 未检测到 Python 环境！
    echo     请先安装 Python 3.8+ 并勾选 "Add Python to PATH"。
    echo.
    pause
    exit /b 1
)

set "PROXY_PORT="
set /p PROXY_PORT="请输入本地 HTTP/HTTPS 代理端口号 (例如 7890，直接按回车表示不使用代理): "

if not defined PROXY_PORT goto NOPROXY
if "%PROXY_PORT%"=="" goto NOPROXY

echo.
echo [+] 已启用本地代理: http://127.0.0.1:%PROXY_PORT%
python "%~dp0build_workbuddy_arm64.py" --proxy "http://127.0.0.1:%PROXY_PORT%"
goto END

:NOPROXY
echo.
echo [*] 未输入代理端口，使用网络直连模式 (No Proxy)...
python "%~dp0build_workbuddy_arm64.py"
goto END

:END
echo.
echo ================================================================================
echo   一键构建已完成！请检查上方日志或 dist 目录中的安装包文件。
echo ================================================================================
pause
