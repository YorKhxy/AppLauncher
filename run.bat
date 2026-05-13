@echo off
REM 从源码启动当前目录下的 VrLauncher（金属朋克主题以 src\ui 为准）
cd /d "%~dp0"
python src\main.py
if errorlevel 1 pause
