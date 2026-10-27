@echo off
chcp 65001 >nul
title Πού πάμε; - τοπικός server
cd /d "%~dp0public"

set PORT=8000
set PY=
where python >nul 2>&1 && set PY=python
if not defined PY ( where py >nul 2>&1 && set PY=py )
if not defined PY (
  echo Δεν βρέθηκε Python. Εγκατάστησέ το από https://www.python.org/downloads/
  echo ^(στην εγκατάσταση τσέκαρε το "Add python.exe to PATH"^)
  pause
  exit /b 1
)

echo.
echo  Ο χάρτης τρέχει στο http://localhost:%PORT%
echo  Για να τον σταματήσεις, κλείσε αυτό το παράθυρο ή πάτα Ctrl+C.
echo.

start "" /b cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:%PORT%"
%PY% -m http.server %PORT% --bind 127.0.0.1
pause
