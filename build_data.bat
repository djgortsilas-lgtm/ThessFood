@echo off
setlocal
cd /d "%~dp0"
set PY=
python -c "import sys" >NUL 2>&1 && set PY=python
if not defined PY py -3 -c "import sys" >NUL 2>&1 && set PY=py -3
if not defined PY ( echo [X] Python not found. & pause & exit /b 1 )
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
%PY% scripts\build_data.py
echo.
pause
