@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === 1/3 Λήψη από ΓΕΜΗ (περίπου 6-8 λεπτά, όριο 8 κλήσεις/λεπτό) ===
python -X utf8 -u scripts\fetch_gemi.py || goto :err
echo === 2/3 Αντιστοίχιση με τα σημεία του χάρτη ===
python -X utf8 -u scripts\enrich_gemi.py || goto :err
echo === 3/3 Δημιουργία places.json ===
python -X utf8 -u scripts\build_data.py || goto :err
echo.
echo Ολοκληρώθηκε.
pause
exit /b 0
:err
echo.
echo ΣΦΑΛΜΑ - δες τα μηνύματα παραπάνω.
pause
exit /b 1
