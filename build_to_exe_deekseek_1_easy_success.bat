@echo off
chcp 65001
echo 修复版打包脚本
echo.

cd /d "D:\3_非项目任务\20251010-软件设计-电压计算器\LED_Voltage_Calculator_V3"

echo 当前目录: %CD%
echo.

pyinstaller --onefile --windowed ^
  --name "电压计算器" ^
  --add-data "main_app;main_app" ^
  --add-data "core_functions;core_functions" ^
  --add-data "data_files;data_files" ^
  --add-data "resources;resources" ^
  "main_app\gui_mainwindow.py"

if exist "dist\电压计算器.exe" (
    echo ✅ 打包成功！EXE文件: dist\电压计算器.exe
) else (
    echo ❌ 打包失败！
)

pause