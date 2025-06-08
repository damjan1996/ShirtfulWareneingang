#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimalistisches Projekt-Setup für RFID-Login & QR-Wareneingang
Erstellt die komplette Projektstruktur
"""

import os
import sys
from pathlib import Path


def create_project_structure():
    """Erstellt die minimalistische Projektstruktur"""

    # Basis-Verzeichnis - verwende raw string oder Path
    base_path = Path(r"C:\Users\damja\PycharmProjects\Wareneingang")

    # Projektstruktur definieren
    structure = {
        # Hauptverzeichnis-Dateien
        "app.py": "Tkinter GUI Hauptanwendung",
        "hid_listener.py": "RFID Keyboard Listener",
        "qr_scanner.py": "Webcam QR Scanner",
        "connection.py": "Datenbank Connection Pool",
        "models.py": "Datenbank Models",
        "config.py": "Konfiguration und Settings",
        ".env": "Umgebungsvariablen",
        ".env.example": "Beispiel Umgebungsvariablen",
        "requirements.txt": "Python Dependencies",
        "README.md": "Projekt Dokumentation",
        ".gitignore": "Git Ignore Datei",
        "run.bat": "Windows Start Script",

        # Database Verzeichnis
        "database/": "Datenbank Scripts",
        "database/add_database_rdscannershirtful.py": "Datenbank Setup Script",
        "database/schema.sql": "SQL DDL Schema",
        "database/import_rfid_tags.py": "RFID Tags Import Script",
        "database/test_connection.py": "Datenbank Verbindungstest",

        # Config Verzeichnis
        "config/": "Konfigurationsdateien",
        "config/authorized_tags.json": "Autorisierte RFID Tags",

        # Logs Verzeichnis
        "logs/": "Log Dateien",
        "logs/.gitkeep": "Placeholder für Git",

        # Utils Verzeichnis (optional, aber hilfreich)
        "utils/": "Hilfsfunktionen",
        "utils/__init__.py": "Utils Package Init",
        "utils/logger.py": "Logging Funktionen",
        "utils/validators.py": "Validierungs Funktionen",

        # Tests (minimal)
        "tests/": "Test Dateien",
        "tests/test_rfid.py": "RFID Tests",
        "tests/test_qr.py": "QR Scanner Tests",
        "tests/test_db.py": "Datenbank Tests",
    }

    print("=" * 60)
    print("🔨 Erstelle minimalistische Projektstruktur")
    print(f"📁 Zielverzeichnis: {base_path}")
    print("=" * 60)

    # Struktur erstellen
    created_dirs = 0
    created_files = 0

    for path, description in structure.items():
        full_path = base_path / path

        try:
            if path.endswith('/'):
                # Verzeichnis erstellen
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"📁 Verzeichnis erstellt: {path}")
                created_dirs += 1
            else:
                # Datei erstellen (leer)
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()
                print(f"📄 Datei erstellt: {path}")
                created_files += 1

        except Exception as e:
            print(f"❌ Fehler bei {path}: {e}")

    # Spezielle Dateien mit Basis-Inhalt
    special_files = {
        ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Logs
logs/*.log
logs/*.txt

# Environment
.env
!.env.example

# Database
*.db
*.sqlite3

# Temp
temp/
tmp/
""",

        ".env.example": """# Datenbank Konfiguration
MSSQL_SERVER=116.202.224.248
MSSQL_USER=sa
MSSQL_PASSWORD=your_password_here
MSSQL_DATABASE=RdScanner

# Anwendungs-Einstellungen
APP_DEBUG=False
LOG_LEVEL=INFO
""",

        "requirements.txt": """# Core Dependencies
pynput>=1.7.6
opencv-python>=4.8.0
pyzbar>=0.1.9
python-dotenv>=1.0.0
pyodbc>=5.0.0

# Optional aber empfohlen
Pillow>=10.0.0
numpy>=1.24.0
""",

        "README.md": """# RFID-Login & QR-Wareneingang

Minimalistische Desktop-Anwendung für Zeiterfassung und Wareneingang.

## Features
- RFID-basiertes Login/Logout
- QR-Code Scanner für Wareneingänge
- Direkte SQL Server Anbindung
- Multi-User fähig auf einem PC

## Installation
1. Python 3.10+ installieren
2. ODBC Driver 18 for SQL Server installieren
3. Dependencies installieren: `pip install -r requirements.txt`
4. `.env` Datei konfigurieren (siehe `.env.example`)
5. Datenbank einrichten: `python database/add_database_rdscannershirtful.py`
6. Anwendung starten: `python app.py`

## Hardware
- USB RFID Reader (HID Modus)
- Webcam für QR-Codes
""",

        "run.bat": """@echo off
echo Starting RFID & QR Scanner Application...
cd /d "%~dp0"
python app.py
pause
""",

        "utils/__init__.py": """# Utils Package
""",

        "config/authorized_tags.json": """{
  "53004ECD68": {
    "name": "Test-Tag-1",
    "access_level": "user",
    "added_date": "2025-06-02T21:57:16.124545"
  },
  "53004E114B": {
    "name": "Test-Tag-2",
    "access_level": "user",
    "added_date": "2025-06-02T21:57:04.941038"
  }
}
"""
    }

    # Spezielle Dateien mit Inhalt schreiben
    print("\n📝 Schreibe Basis-Inhalte...")
    for filename, content in special_files.items():
        try:
            file_path = base_path / filename
            file_path.write_text(content, encoding='utf-8')
            print(f"✅ {filename} mit Basis-Inhalt erstellt")
        except Exception as e:
            print(f"❌ Fehler bei {filename}: {e}")

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("📊 Projekt-Setup abgeschlossen!")
    print(f"✅ Verzeichnisse erstellt: {created_dirs}")
    print(f"✅ Dateien erstellt: {created_files}")
    print(f"📁 Projektpfad: {base_path}")
    print("\n🚀 Nächste Schritte:")
    print("1. Wechseln Sie zum Projektverzeichnis")
    print("2. Erstellen Sie eine virtuelle Umgebung: python -m venv venv")
    print("3. Aktivieren Sie die Umgebung: venv\\Scripts\\activate")
    print("4. Installieren Sie Dependencies: pip install -r requirements.txt")
    print("5. Konfigurieren Sie die .env Datei")
    print("6. Richten Sie die Datenbank ein")
    print("=" * 60)

    return True


def main():
    """Hauptfunktion"""
    print("🔷 Minimalistisches RFID & QR Scanner Projekt Setup")
    print("🏗️  Erstelle Projektstruktur...")

    # Sicherheitsabfrage
    base_path = r"C:\Users\damja\PycharmProjects\Wareneingang"
    if os.path.exists(base_path):
        # Da das Verzeichnis bereits existiert, keine Abfrage
        print(f"📁 Arbeite in existierendem Verzeichnis: {base_path}")

    # Struktur erstellen
    if create_project_structure():
        print("\n✅ Projektstruktur erfolgreich erstellt!")

        # Prüfe ob wir bereits im venv sind
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("\n✅ Virtual Environment bereits aktiv!")
        else:
            print("\n⚠️  Hinweis: Virtual Environment noch nicht aktiv")
            print("   Aktivieren Sie es mit: venv\\Scripts\\activate")
    else:
        print("\n❌ Fehler beim Erstellen der Projektstruktur")
        sys.exit(1)


if __name__ == "__main__":
    main()