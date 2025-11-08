@echo off
setlocal ENABLEDELAYEDEXPANSION
chcp 65001 >nul
title 一键打包（修复文件复制问题）- LED_Voltage_Calculator_V3

REM ========== 0) 基本环境 ==========
cd /d "%~dp0"
set "PROJ_ROOT=%CD%"

echo [INFO] 项目根目录: %PROJ_ROOT%

REM 确保日志目录存在
if not exist "%PROJ_ROOT%\build_logs" mkdir "%PROJ_ROOT%\build_logs"
for /f %%i in ('powershell -NoProfile -Command "(Get-Date).ToString(\"yyyyMMdd_HHmmss\")"') do set TS=%%i
set "LOG=%PROJ_ROOT%\build_logs\build_%TS%.log"

echo [INFO] 日志文件: %LOG%

REM 关键环境变量
set PYINSTALLER_STRICT_QT_HOOKS=0
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ===== 打包开始 %DATE% %TIME% ===== > "%LOG%"
echo 项目根目录: %PROJ_ROOT% >> "%LOG%"

REM ========== 1) 检查 Python 环境 ==========
echo [STEP 1] 检查 Python 环境...
echo [STEP 1] 检查 Python 环境... >> "%LOG%"
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 未找到 Python，请安装并加入 PATH >> "%LOG%"
    echo [ERROR] 未找到 Python，请安装并加入 PATH
    pause
    exit /b 1
)

REM ========== 2) 创建英文临时工作目录 ==========
echo [STEP 2] 创建英文临时工作目录...
echo [STEP 2] 创建英文临时工作目录... >> "%LOG%"
set "TEMP_WORK=C:\LEDVC_BUILD_TEMP"
set "TEMP_SRC=%TEMP_WORK%\src"

REM 清理临时目录
if exist "%TEMP_WORK%" (
    echo 清理旧临时目录... >> "%LOG%"
    rmdir /s /q "%TEMP_WORK%" 2>nul
)

mkdir "%TEMP_SRC%" 2>nul
if not exist "%TEMP_SRC%" (
    echo [ERROR] 无法创建临时工作目录 >> "%LOG%"
    echo [ERROR] 无法创建临时工作目录
    pause
    exit /b 2
)

REM ========== 3) 复制项目文件到临时目录 ==========
echo [STEP 3] 复制项目文件到临时目录...
echo [STEP 3] 复制项目文件到临时目录... >> "%LOG%"

REM 使用robocopy替代xcopy，更可靠
robocopy "%PROJ_ROOT%" "%TEMP_SRC%" /E /XD .venv build dist __pycache__ .git .idea *.egg-info build_logs /XF *.spec /NJH /NJS >> "%LOG%" 2>&1

REM 检查复制是否成功
set "ENTRY_CHECK=%TEMP_SRC%\main_app\gui_mainwindow.py"
if not exist "%ENTRY_CHECK%" (
    echo [ERROR] 文件复制失败，未找到入口文件 >> "%LOG%"
    echo [ERROR] 文件复制失败，未找到入口文件
    echo 请检查源文件是否存在: %PROJ_ROOT%\main_app\gui_mainwindow.py >> "%LOG%"
    echo 请检查源文件是否存在: %PROJ_ROOT%\main_app\gui_mainwindow.py
    goto :cleanup
)

echo [OK] 文件复制成功 >> "%LOG%"

REM ========== 4) 在临时目录创建虚拟环境 ==========
echo [STEP 4] 在临时目录创建虚拟环境...
echo [STEP 4] 在临时目录创建虚拟环境... >> "%LOG%"
cd /d "%TEMP_SRC%"

python -m venv ".venv" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 创建虚拟环境失败 >> "%LOG%"
    echo [ERROR] 创建虚拟环境失败
    goto :cleanup
)

REM ========== 5) 安装依赖 ==========
echo [STEP 5] 安装依赖包...
echo [STEP 5] 安装依赖包... >> "%LOG%"

REM 升级pip和PyInstaller
".venv\Scripts\python.exe" -m pip install --upgrade pip >> "%LOG%" 2>&1
".venv\Scripts\python.exe" -m pip install --upgrade pyinstaller >> "%LOG%" 2>&1

REM 安装核心依赖
echo 安装项目依赖... >> "%LOG%"
".venv\Scripts\python.exe" -m pip install PyQt5 matplotlib numpy pandas openpyxl pillow scipy >> "%LOG%" 2>&1

REM ========== 6) 检查入口文件 ==========
echo [STEP 6] 检查入口文件...
echo [STEP 6] 检查入口文件... >> "%LOG%"
set "ENTRY=main_app\gui_mainwindow.py"
if not exist "%ENTRY%" (
    echo [ERROR] 未找到入口脚本: %ENTRY% >> "%LOG%"
    echo [ERROR] 未找到入口脚本: %ENTRY%
    goto :cleanup
)
echo [OK] 找到入口文件: %ENTRY% >> "%LOG%"

REM ========== 7) 执行目录式打包 ==========
echo [STEP 7] 开始目录式打包...
echo [STEP 7] 开始目录式打包... >> "%LOG%"

REM 清理旧的打包结果
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul
del "*.spec" 2>nul

REM 使用目录式打包（去掉--onefile），简化Qt处理
echo 执行PyInstaller命令... >> "%LOG%"
".venv\Scripts\python.exe" -m PyInstaller ^
    --name "LED_Voltage_Calculator" ^
    --noconsole ^
    --clean ^
    --log-level=INFO ^
    --paths . ^
    --paths main_app ^
    --paths core_functions ^
    --add-data "resources;resources" ^
    --add-data "data_files;data_files" ^
    --add-data "main_app\styles;main_app/styles" ^
    --add-data "main_app\icons;main_app/icons" ^
    --add-data "core_functions\input;core_functions/input" ^
    --add-data "core_functions\output;core_functions/output" ^
    --add-data "core_functions\temp;core_functions/temp" ^
    --collect-all PyQt5 ^
    --collect-all matplotlib ^
    --collect-all numpy ^
    --collect-all pandas ^
    "%ENTRY%" >> "%LOG%" 2>&1

set BUILD_ERR=%ERRORLEVEL%
if %BUILD_ERR% NEQ 0 (
    echo [ERROR] 打包失败，错误码: %BUILD_ERR% >> "%LOG%"
    echo [ERROR] 打包失败，错误码: %BUILD_ERR%
    echo 请查看日志文件: %LOG%
    goto :cleanup
)

REM ========== 8) 复制结果回原项目 ==========
echo [STEP 8] 复制打包结果...
echo [STEP 8] 复制打包结果... >> "%LOG%"

REM 确保目标目录存在
if not exist "%PROJ_ROOT%\dist" mkdir "%PROJ_ROOT%\dist"
if not exist "%PROJ_ROOT%\build" mkdir "%PROJ_ROOT%\build"

REM 复制打包结果
robocopy "%TEMP_SRC%\dist" "%PROJ_ROOT%\dist" /E /NJH /NJS >> "%LOG%" 2>&1
robocopy "%TEMP_SRC%\build" "%PROJ_ROOT%\build" /E /NJH /NJS >> "%LOG%" 2>&1

REM ========== 9) 重命名输出目录为中文（可选） ==========
cd /d "%PROJ_ROOT%"
if exist "dist\LED_Voltage_Calculator" (
    if not exist "dist\电压计算器" (
        ren "dist\LED_Voltage_Calculator" "电压计算器" 2>nul
    )
)

REM ========== 10) 完成 ==========
echo [SUCCESS] 打包完成！ >> "%LOG%"
echo [SUCCESS] 打包完成！
if exist "dist\电压计算器" (
    echo 可执行文件: %PROJ_ROOT%\dist\电压计算器\LED_Voltage_Calculator.exe
) else if exist "dist\LED_Voltage_Calculator" (
    echo 可执行文件: %PROJ_ROOT%\dist\LED_Voltage_Calculator\LED_Voltage_Calculator.exe
)
echo 详细日志: %LOG%
echo.

REM 清理临时目录
if exist "%TEMP_WORK%" (
    echo 清理临时目录... >> "%LOG%"
    rmdir /s /q "%TEMP_WORK%" 2>nul
)

echo 按任意键退出...
pause
exit /b 0

:cleanup
echo.
echo [INFO] 清理临时文件...
echo [INFO] 清理临时文件... >> "%LOG%"
if exist "%TEMP_WORK%" (
    rmdir /s /q "%TEMP_WORK%" 2>nul
)
echo [ERROR] 构建过程失败，请检查日志: %LOG%
echo 按任意键退出...
pause
exit /b 1