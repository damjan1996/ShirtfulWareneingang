@echo off
echo ============================================
echo RFID ^& QR Scanner - Paralleles Multi-User System
echo ============================================
echo.
echo Alle Benutzer können parallel alle Scanner nutzen
echo QR-Codes werden automatisch oder manuell zugeordnet
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

REM Konfiguration prüfen
echo Prüfe Konfiguration...
if not exist ".env" (
    if exist ".env.example" (
        echo.
        echo ⚠️ WARNUNG: .env Datei nicht gefunden!
        echo Kopieren Sie .env.example zu .env und passen Sie die Werte an.
        echo.
        echo Beispiel-Konfiguration für Multi-Scanner:
        echo   CAMERA_INDICES=0,1,2
        echo   QR_DEFAULT_ASSIGNMENT_MODE=round_robin
        echo   SCANNER_VIDEO_DISPLAY=primary
        echo.
        pause
    )
)

REM System-Test anbieten
echo.
echo Möchten Sie einen System-Test durchführen? (Empfohlen beim ersten Start)
echo 1 = Ja, System-Test starten
echo 2 = Nein, direkt zur Anwendung
echo.
set /p choice="Ihre Wahl (1/2): "

if "%choice%"=="1" (
    echo.
    echo ============================================
    echo Starte umfassenden System-Test...
    echo ============================================
    echo.
    %PYTHON% test_all_components.py

    if errorlevel 1 (
        echo.
        echo ❌ System-Test fehlgeschlagen!
        echo Bitte beheben Sie die oben genannten Probleme.
        echo.
        pause
        exit /b 1
    )

    echo.
    echo ✅ System-Test erfolgreich! Starte Anwendung...
    timeout /t 3 >nul
)

REM Anwendung starten
echo.
echo ============================================
echo Starte Paralleles Multi-User Scanner System
echo ============================================
echo.
echo 💡 Funktionen:
echo   - Mehrere Benutzer können gleichzeitig angemeldet sein
echo   - Alle können parallel alle verfügbaren Scanner nutzen
echo   - QR-Code Zuordnung: Round-Robin, Manuell oder Letzter RFID
echo   - Live-Übersicht über alle Scanner und Benutzer
echo.
echo 🔧 Steuerung:
echo   - RFID-Tag scannen = Anmelden/Abmelden
echo   - QR-Code scannen = Automatische oder manuelle Zuordnung
echo   - Scanner können dynamisch gestartet/gestoppt werden
echo.

%PYTHON% app.py

REM Bei Fehler pausieren
if errorlevel 1 (
    echo.
    echo ============================================
    echo FEHLER: Anwendung wurde mit Fehler beendet
    echo ============================================
    echo.
    echo Häufige Probleme und Lösungen:
    echo.
    echo 🔧 Kamera-Probleme:
    echo   - Prüfen Sie CAMERA_INDICES in .env (z.B. 0,1,2)
    echo   - Versuchen Sie anderen CAMERA_BACKEND (DSHOW/V4L2/AUTO)
    echo   - Stellen Sie sicher, dass Kameras nicht von anderen Apps verwendet werden
    echo.
    echo 🔧 RFID-Reader-Probleme:
    echo   - Reader muss im HID-Modus arbeiten
    echo   - Testen Sie mit Texteditor ob Tags ausgegeben werden
    echo   - Prüfen Sie RFID-Einstellungen in .env
    echo.
    echo 🔧 Datenbank-Probleme:
    echo   - Prüfen Sie Server-Erreichbarkeit (ping)
    echo   - Validieren Sie Zugangsdaten in .env
    echo   - ODBC Driver 18 installiert?
    echo.
    echo 🔧 Performance-Probleme:
    echo   - Reduzieren Sie SCANNER_FRAME_WIDTH/HEIGHT
    echo   - Erhöhen Sie SCANNER_FRAME_SKIP
    echo   - Setzen Sie SCANNER_VIDEO_DISPLAY=none
    echo.
    echo Führen Sie 'python test_all_components.py' für detaillierte Diagnose aus.
    echo.
)

pause