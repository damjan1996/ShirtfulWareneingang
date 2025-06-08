@echo off
echo ============================================
echo RFID ^& QR Scanner - Wareneingang
echo ============================================
echo.

REM Zum Skript-Verzeichnis wechseln
cd /d "%~dp0"

REM Prüfen ob venv existiert
if exist "venv\Scripts\python.exe" (
    echo Virtual Environment gefunden
    set PYTHON=venv\Scripts\python.exe
) else (
    echo Virtual Environment nicht gefunden
    echo Verwende System-Python
    set PYTHON=python
)

REM Anwendung starten
echo.
echo Starte Anwendung...
echo.
%PYTHON% app.py

REM Bei Fehler pausieren
if errorlevel 1 (
    echo.
    echo ============================================
    echo FEHLER: Anwendung wurde mit Fehler beendet
    echo ============================================
    echo.
    echo Mögliche Ursachen:
    echo - Dependencies nicht installiert (pip install -r requirements.txt^)
    echo - Datenbank nicht erreichbar (.env prüfen^)
    echo - RFID Reader oder Kamera nicht angeschlossen
    echo.
)

pause