# ============================================================================
# BATCH-SCRIPT CONTENT (run_tests.bat)
# ============================================================================

BATCH_SCRIPT_CONTENT = """@echo off
REM ============================================================================
REM RFID & QR Scanner - Vollständige Test-Suite
REM Batch-Script für einfache Test-Ausführung unter Windows
REM ============================================================================

echo.
echo ============================================
echo RFID ^& QR Scanner - Test-Suite
echo ============================================
echo.

REM Zum Skript-Verzeichnis wechseln
cd /d "%~dp0"

REM Python-Pfad bestimmen
if exist "venv\\Scripts\\python.exe" (
    set PYTHON=venv\\Scripts\\python.exe
    echo Virtual Environment gefunden
) else (
    set PYTHON=python
    echo Verwende System-Python
)

REM Prüfe ob Python verfügbar
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo ❌ FEHLER: Python nicht gefunden!
    echo Installieren Sie Python oder aktivieren Sie das Virtual Environment
    pause
    exit /b 1
)

REM Test-Modus abfragen
echo Welche Tests möchten Sie ausführen?
echo.
echo 1 = Alle Tests (umfassend, ~10 Minuten)
echo 2 = Quick-Tests (nur kritische, ~3 Minuten)
echo 3 = Hardware-Tests (RFID + Kamera)
echo 4 = Performance-Tests
echo 5 = GUI-Tests
echo 6 = End-to-End Tests
echo 7 = Test-Kategorien auflisten
echo.
set /p choice="Ihre Wahl (1-7): "

echo.
echo ============================================

if "%choice%"=="1" (
    echo Starte vollständige Test-Suite...
    echo ⏱️ Geschätzte Zeit: 8-12 Minuten
    echo.
    %PYTHON% test_runner.py
    set test_result=%errorlevel%
    goto :end_tests
)

if "%choice%"=="2" (
    echo Starte Quick-Tests...
    echo ⏱️ Geschätzte Zeit: 2-4 Minuten
    echo.
    %PYTHON% test_runner.py --quick
    set test_result=%errorlevel%
    goto :end_tests
)

if "%choice%"=="3" (
    echo Starte Hardware-Tests...
    echo 🔧 Prüft RFID-Reader und Kameras
    echo.
    %PYTHON% test_runner.py --category hardware
    set test_result=%errorlevel%
    goto :end_tests
)

if "%choice%"=="4" (
    echo Starte Performance-Tests...
    echo ⚡ Prüft System-Performance und Belastung
    echo.
    %PYTHON% test_runner.py --category performance
    set test_result=%errorlevel%
    goto :end_tests
)

if "%choice%"=="5" (
    echo Starte GUI-Tests...
    echo 🖥️ Prüft Benutzeroberfläche
    echo.
    %PYTHON% test_runner.py --category gui
    set test_result=%errorlevel%
    goto :end_tests
)

if "%choice%"=="6" (
    echo Starte End-to-End Tests...
    echo 🔄 Prüft komplette Workflows
    echo.
    %PYTHON% test_runner.py --category e2e
    set test_result=%errorlevel%
    goto :end_tests
)

if "%choice%"=="7" (
    echo Verfügbare Test-Kategorien:
    echo.
    %PYTHON% test_runner.py --list
    echo.
    echo Drücken Sie eine Taste um fortzufahren...
    pause >nul
    goto :start
)

echo ❌ Ungültige Auswahl: %choice%
echo.
pause
exit /b 1

:end_tests
echo.
echo ============================================
echo TEST-ERGEBNISSE
echo ============================================

if %test_result%==0 (
    echo.
    echo ✅ ALLE TESTS ERFOLGREICH!
    echo ============================================
    echo 🎉 Das System ist bereit für den Einsatz
    echo.
    echo 🚀 Nächste Schritte:
    echo    1. Starten Sie die Anwendung: run.bat
    echo    2. Testen Sie mit echten RFID-Tags
    echo    3. Kalibrieren Sie die Kameras falls nötig
    echo.
    echo 📄 Detaillierte Berichte finden Sie in: logs\\
    echo.
) else (
    echo.
    echo ❌ EINIGE TESTS FEHLGESCHLAGEN
    echo ============================================
    echo ⚠️ Das System hat Probleme die behoben werden müssen
    echo.
    echo 🔧 Nächste Schritte:
    echo    1. Prüfen Sie die Fehlermeldungen oben
    echo    2. Beheben Sie die identifizierten Probleme
    echo    3. Führen Sie die Tests erneut aus
    echo.
    echo 📄 Detaillierte Fehler-Logs: logs\\
    echo.
    echo 💡 Häufige Probleme:
    echo    - Kamera nicht angeschlossen oder verwendet
    echo    - RFID-Reader nicht im HID-Modus
    echo    - Datenbank nicht erreichbar
    echo    - Fehlende Python-Module: pip install -r requirements.txt
    echo.
)

echo Drücken Sie eine Taste um zu beenden...
pause >nul
exit /b %test_result%
"""

# ============================================================================
# POWERSHELL-SCRIPT CONTENT (run_tests.ps1)
# ============================================================================

POWERSHELL_SCRIPT_CONTENT = """
# ============================================================================
# RFID & QR Scanner - Test-Suite (PowerShell Version)
# ============================================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "RFID & QR Scanner - Test-Suite" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Zum Skript-Verzeichnis wechseln
Set-Location $PSScriptRoot

# Python-Pfad bestimmen
if (Test-Path "venv\\Scripts\\python.exe") {
    $Python = "venv\\Scripts\\python.exe"
    Write-Host "✅ Virtual Environment gefunden" -ForegroundColor Green
} else {
    $Python = "python"
    Write-Host "ℹ️ Verwende System-Python" -ForegroundColor Yellow
}

# Prüfe Python-Verfügbarkeit
try {
    & $Python --version | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Python nicht gefunden" }
} catch {
    Write-Host "❌ FEHLER: Python nicht verfügbar!" -ForegroundColor Red
    Write-Host "Installieren Sie Python oder aktivieren Sie das Virtual Environment" -ForegroundColor Yellow
    Read-Host "Drücken Sie Enter um zu beenden"
    exit 1
}

# Test-Optionen anzeigen
Write-Host "Welche Tests möchten Sie ausführen?" -ForegroundColor White
Write-Host ""
Write-Host "1 = Alle Tests (umfassend, ~10 Minuten)" -ForegroundColor White
Write-Host "2 = Quick-Tests (nur kritische, ~3 Minuten)" -ForegroundColor Green
Write-Host "3 = Hardware-Tests (RFID + Kamera)" -ForegroundColor Blue
Write-Host "4 = Performance-Tests" -ForegroundColor Magenta
Write-Host "5 = GUI-Tests" -ForegroundColor Cyan
Write-Host "6 = End-to-End Tests" -ForegroundColor Yellow
Write-Host "7 = Test-Kategorien auflisten" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Ihre Wahl (1-7)"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan

$testResult = 0

switch ($choice) {
    "1" {
        Write-Host "Starte vollständige Test-Suite..." -ForegroundColor Green
        Write-Host "⏱️ Geschätzte Zeit: 8-12 Minuten" -ForegroundColor Yellow
        Write-Host ""
        & $Python test_runner.py
        $testResult = $LASTEXITCODE
    }
    "2" {
        Write-Host "Starte Quick-Tests..." -ForegroundColor Green
        Write-Host "⏱️ Geschätzte Zeit: 2-4 Minuten" -ForegroundColor Yellow
        Write-Host ""
        & $Python test_runner.py --quick
        $testResult = $LASTEXITCODE
    }
    "3" {
        Write-Host "Starte Hardware-Tests..." -ForegroundColor Blue
        Write-Host "🔧 Prüft RFID-Reader und Kameras" -ForegroundColor Gray
        Write-Host ""
        & $Python test_runner.py --category hardware
        $testResult = $LASTEXITCODE
    }
    "4" {
        Write-Host "Starte Performance-Tests..." -ForegroundColor Magenta
        Write-Host "⚡ Prüft System-Performance und Belastung" -ForegroundColor Gray
        Write-Host ""
        & $Python test_runner.py --category performance
        $testResult = $LASTEXITCODE
    }
    "5" {
        Write-Host "Starte GUI-Tests..." -ForegroundColor Cyan
        Write-Host "🖥️ Prüft Benutzeroberfläche" -ForegroundColor Gray
        Write-Host ""
        & $Python test_runner.py --category gui
        $testResult = $LASTEXITCODE
    }
    "6" {
        Write-Host "Starte End-to-End Tests..." -ForegroundColor Yellow
        Write-Host "🔄 Prüft komplette Workflows" -ForegroundColor Gray
        Write-Host ""
        & $Python test_runner.py --category e2e
        $testResult = $LASTEXITCODE
    }
    "7" {
        Write-Host "Verfügbare Test-Kategorien:" -ForegroundColor White
        Write-Host ""
        & $Python test_runner.py --list
        Write-Host ""
        Read-Host "Drücken Sie Enter um fortzufahren"
        exit 0
    }
    default {
        Write-Host "❌ Ungültige Auswahl: $choice" -ForegroundColor Red
        Read-Host "Drücken Sie Enter um zu beenden"
        exit 1
    }
}

# Ergebnisse anzeigen
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "TEST-ERGEBNISSE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if ($testResult -eq 0) {
    Write-Host ""
    Write-Host "✅ ALLE TESTS ERFOLGREICH!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "🎉 Das System ist bereit für den Einsatz" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Nächste Schritte:" -ForegroundColor White
    Write-Host "   1. Starten Sie die Anwendung: .\\run.bat" -ForegroundColor Gray
    Write-Host "   2. Testen Sie mit echten RFID-Tags" -ForegroundColor Gray
    Write-Host "   3. Kalibrieren Sie die Kameras falls nötig" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📄 Detaillierte Berichte finden Sie in: logs\\" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "❌ EINIGE TESTS FEHLGESCHLAGEN" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "⚠️ Das System hat Probleme die behoben werden müssen" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🔧 Nächste Schritte:" -ForegroundColor White
    Write-Host "   1. Prüfen Sie die Fehlermeldungen oben" -ForegroundColor Gray
    Write-Host "   2. Beheben Sie die identifizierten Probleme" -ForegroundColor Gray
    Write-Host "   3. Führen Sie die Tests erneut aus" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📄 Detaillierte Fehler-Logs: logs\\" -ForegroundColor Gray
}

Write-Host ""
Read-Host "Drücken Sie Enter um zu beenden"
exit $testResult
"""

# Erstelle die Batch- und PowerShell-Scripts
def create_test_scripts():
    """Erstellt die Test-Scripts"""
    # Batch-Script
    with open('run_tests.bat', 'w', encoding='utf-8') as f:
        f.write(BATCH_SCRIPT_CONTENT)
    print("📄 run_tests.bat erstellt")

    # PowerShell-Script
    with open('run_tests.ps1', 'w', encoding='utf-8') as f:
        f.write(POWERSHELL_SCRIPT_CONTENT)
    print("📄 run_tests.ps1 erstellt")

if __name__ == "__main__":
    # Erstelle Scripts wenn direkt ausgeführt
    if len(sys.argv) > 1 and sys.argv[1] == '--create-scripts':
        create_test_scripts()
    else:
        main()