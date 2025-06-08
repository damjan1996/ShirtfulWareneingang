@echo off
echo ============================================
echo RFID ^& QR Scanner - Tab Version (Shared)
echo ============================================
echo.
echo Ein gemeinsamer Scanner für alle Benutzer
echo.

cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
)

echo Starte Tab-basierte Anwendung mit geteiltem Scanner...
echo.
%PYTHON% app_tabs_shared.py

if errorlevel 1 (
    echo.
    echo ============================================
    echo FEHLER: Anwendung wurde mit Fehler beendet
    echo ============================================
)

pause