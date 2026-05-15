@echo off
REM 从源码启动当前目录下的 ClickDone（界面以 src\web 为准）
cd /d "%~dp0"
python src\main.py
if errorlevel 1 pause
