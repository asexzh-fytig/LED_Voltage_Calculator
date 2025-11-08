@echo off
chcp 65001
echo 目录结构分析工具
echo ===============================
echo.

:: 获取当前目录和上一级目录
set "CURRENT_DIR=%~dp0"
set "PARENT_DIR=%~dp0..\"

echo 当前目录: %CURRENT_DIR%
echo 上一级目录: %PARENT_DIR%
echo.

echo 上一级目录的完整结构:
echo ===============================
tree "%PARENT_DIR%" /F /A
echo.

echo 主要子文件夹内容:
echo ===============================
for /d %%i in ("%PARENT_DIR%*") do (
    echo.
    echo [文件夹] %%i
    dir "%%i" /B
)

echo.
echo 按文件类型统计:
echo ===============================
echo Python文件 (.py):
dir "%PARENT_DIR%*.py" /B /S 2>nul | find /c /v "" >nul && (
    dir "%PARENT_DIR%*.py" /B /S
) || echo 无Python文件

echo.
echo 批处理文件 (.bat):
dir "%PARENT_DIR%*.bat" /B /S 2>nul | find /c /v "" >nul && (
    dir "%PARENT_DIR%*.bat" /B /S
) || echo 无批处理文件

echo.
echo 可执行文件 (.exe):
dir "%PARENT_DIR%*.exe" /B /S 2>nul | find /c /v "" >nul && (
    dir "%PARENT_DIR%*.exe" /B /S
) || echo 无可执行文件

echo.
echo 按关键文件名搜索:
echo ===============================
for %%F in (gui_mainwindow.py main_app core_functions data_files resources) do (
    echo 搜索 "%%F": 
    dir "%PARENT_DIR%" /S /B | findstr /I "%%F" 2>nul
    if errorlevel 1 echo   - 未找到
    echo.
)

echo 分析完成！
echo 请将上面的输出内容复制给我分析
pause