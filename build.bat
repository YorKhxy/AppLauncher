@echo off
REM 始终在「本脚本所在目录」打包，避免误用 g:\ 等其他路径的旧工程
cd /d "%~dp0"
python build.py
pause
