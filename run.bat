@echo off
chcp 65001 >nul
title MiniRead - 阅读工具

echo ========================================
echo    MiniRead - Windows阅读工具
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查依赖是否安装
echo [信息] 检查依赖...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装依赖，请稍候...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请手动执行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo [信息] 启动 MiniRead...
echo.

:: 运行主程序
python main.py

if errorlevel 1 (
    echo.
    echo [错误] 程序异常退出
    pause
)
