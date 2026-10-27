@echo off
setlocal
title Pou pame - local server
cd /d "%~dp0public"
set PORT=8000

rem --- find a Python that really runs (skips the Microsoft Store alias)
set PY=
python -c "import sys" >nul 2>&1 && set PY=python
if not defined PY py -3 -c "import sys" >nul 2>&1 && set PY=py -3
if not defined PY (
  echo.
  echo  [X] Python not found.
  echo      Install it from https://www.python.org/downloads/
  echo      and tick "Add python.exe to PATH" during setup.
  echo.
  pause
  exit /b 1
)

echo.
echo  Using: %PY%
echo  Folder: %cd%
echo  Map:   http://localhost:%PORT%
echo  Close this window (or Ctrl+C) to stop.
echo.

rem --- open the browser a few seconds after the server starts
start "" cmd /c "ping -n 4 127.0.0.1 >nul & start http://localhost:%PORT%/"

%PY% -m http.server %PORT% --bind 127.0.0.1
echo.
echo  [X] The server stopped. Read the message above.
pause
