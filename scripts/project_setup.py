#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script zum Erstellen der Projektstruktur für die Wareneingang-Anwendung
"""

import os
import sys


def create_project_structure():
    """Erstellt die komplette Projektstruktur für die Wareneingang-Anwendung"""

    # Basis-Verzeichnis
    base_dir = r"C:\Users\damja\PycharmProjects\Shirtful\Wareneingang"

    # Projektstruktur definieren
    structure = {
        "directories": [
            "",  # Root
            "src",
            "src/gui",
            "src/scanner",
            "src/rfid",
            "src/database",
            "src/utils",
            "src/models",
            "config",
            "assets",
            "assets/images",
            "assets/sounds",
            "logs",
            "tests",
            "docs"
        ],
        "files": [
            # Root-Dateien
            ("main.py", "# Haupteinstiegspunkt der Wareneingang-Anwendung"),
            ("requirements.txt", ""),
            ("README.md", ""),
            (".gitignore", ""),

            # Config-Dateien
            ("config/settings.py", ""),
            ("config/database.py", ""),
            ("config/constants.py", ""),

            # GUI-Module
            ("src/gui/__init__.py", ""),
            ("src/gui/main_window.py", ""),
            ("src/gui/login_screen.py", ""),
            ("src/gui/scanner_screen.py", ""),
            ("src/gui/user_panel.py", ""),
            ("src/gui/widgets.py", ""),
            ("src/gui/styles.py", ""),

            # Scanner-Module
            ("src/scanner/__init__.py", ""),
            ("src/scanner/qr_scanner.py", ""),
            ("src/scanner/camera_handler.py", ""),
            ("src/scanner/decoder.py", ""),

            # RFID-Module
            ("src/rfid/__init__.py", ""),
            ("src/rfid/reader.py", ""),
            ("src/rfid/hid_listener.py", ""),
            ("src/rfid/tag_validator.py", ""),

            # Datenbank-Module
            ("src/database/__init__.py", ""),
            ("src/database/connection.py", ""),
            ("src/database/user_repository.py", ""),
            ("src/database/scan_repository.py", ""),
            ("src/database/queries.py", ""),

            # Models
            ("src/models/__init__.py", ""),
            ("src/models/user.py", ""),
            ("src/models/scan_data.py", ""),
            ("src/models/package.py", ""),

            # Utils
            ("src/utils/__init__.py", ""),
            ("src/utils/logger.py", ""),
            ("src/utils/validators.py", ""),
            ("src/utils/helpers.py", ""),
            ("src/utils/audio_player.py", ""),

            # Tests
            ("tests/__init__.py", ""),
            ("tests/test_rfid.py", ""),
            ("tests/test_scanner.py", ""),
            ("tests/test_database.py", ""),

            # Andere Dateien
            ("src/__init__.py", ""),
        ]
    }

    print("🚀 Erstelle Projektstruktur für Wareneingang-Anwendung")
    print(f"📁 Basis-Verzeichnis: {base_dir}")
    print("=" * 60)

    # Verzeichnisse erstellen
    print("\n📂 Erstelle Verzeichnisse:")
    for directory in structure["directories"]:
        dir_path = os.path.join(base_dir, directory)
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"   ✅ {directory if directory else 'Root'}/")
        except Exception as e:
            print(f"   ❌ Fehler bei {directory}: {e}")

    # Dateien erstellen
    print("\n📄 Erstelle Dateien:")
    for file_path, content in structure["files"]:
        full_path = os.path.join(base_dir, file_path)
        try:
            # Datei nur erstellen, wenn sie nicht existiert
            if not os.path.exists(full_path):
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   ✅ {file_path}")
            else:
                print(f"   ⏭️  {file_path} (existiert bereits)")
        except Exception as e:
            print(f"   ❌ Fehler bei {file_path}: {e}")

    print("\n" + "=" * 60)
    print("✅ Projektstruktur erfolgreich erstellt!")
    print("\n📋 Nächste Schritte:")
    print("1. Wechseln Sie zum Projektverzeichnis:")
    print(f"   cd {base_dir}")
    print("2. Erstellen Sie eine virtuelle Umgebung:")
    print("   python -m venv venv")
    print("3. Aktivieren Sie die virtuelle Umgebung:")
    print("   venv\\Scripts\\activate")
    print("4. Installieren Sie die Abhängigkeiten:")
    print("   pip install -r requirements.txt")


def create_readme():
    """Erstellt eine detaillierte README.md"""
    readme_content = """# Wareneingang Scanner Anwendung

## Übersicht
Desktop-Anwendung für die Wareneingangsverwaltung mit RFID-Login und QR-Code-Scanning.

## Features
- 🔐 RFID-basierter Login (HID-Modus)
- 📷 QR-Code Scanner für Pakete
- 👥 Multi-User Support
- 🗄️ MSSQL Datenbank-Integration
- 🎨 Moderne Tkinter GUI

## Projektstruktur
```
Wareneingang/
├── main.py                 # Haupteinstiegspunkt
├── requirements.txt        # Python-Abhängigkeiten
├── config/                 # Konfigurationsdateien
│   ├── settings.py
│   ├── database.py
│   └── constants.py
├── src/                    # Quellcode
│   ├── gui/               # GUI-Komponenten
│   ├── scanner/           # QR-Scanner Module
│   ├── rfid/             # RFID-Reader Module
│   ├── database/         # Datenbank-Layer
│   ├── models/           # Datenmodelle
│   └── utils/            # Hilfsfunktionen
├── assets/                # Ressourcen
│   ├── images/
│   └── sounds/
├── logs/                  # Log-Dateien
├── tests/                 # Unit-Tests
└── docs/                  # Dokumentation
```

## Installation
1. Python 3.10+ installieren
2. Projekt klonen
3. Virtuelle Umgebung erstellen: `python -m venv venv`
4. Aktivieren: `venv\\Scripts\\activate`
5. Abhängigkeiten installieren: `pip install -r requirements.txt`

## Konfiguration
1. Datenbank-Verbindung in `config/database.py` konfigurieren
2. RFID-Reader COM-Port in `config/settings.py` einstellen
3. Kamera-Index für QR-Scanner anpassen

## Verwendung
```bash
python main.py
```

## Hardware-Anforderungen
- TSHRW380BZMP RFID-Reader (HID-Modus)
- Webcam für QR-Code-Scanning
- Windows 10/11

## Entwickler
Shirtful GmbH
"""
    return readme_content


def create_requirements():
    """Erstellt die requirements.txt"""
    requirements = """# Core Dependencies
tkinter  # Built-in
customtkinter==5.2.0
pyodbc==4.0.39
pynput==1.7.6

# QR-Code Scanner
opencv-python==4.8.1.78
pyzbar==0.1.9
numpy==1.24.3
Pillow==10.1.0

# Utilities
python-dotenv==1.0.0
pytz==2023.3

# Development
pytest==7.4.0
black==23.7.0
pylint==2.17.5
"""
    return requirements


def create_gitignore():
    """Erstellt die .gitignore"""
    gitignore = """# Python
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
*.sublime-project
*.sublime-workspace

# Project specific
logs/*.log
config/local_settings.py
*.db
*.sqlite

# OS
.DS_Store
Thumbs.db
desktop.ini

# Testing
.pytest_cache/
.coverage
htmlcov/

# Distribution
dist/
build/
*.egg-info/
"""
    return gitignore


if __name__ == "__main__":
    try:
        create_project_structure()

        # Zusätzliche Dateien mit Inhalt erstellen
        base_dir = r"C:\Users\damja\PycharmProjects\Shirtful\Wareneingang"

        # README.md
        with open(os.path.join(base_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(create_readme())

        # requirements.txt
        with open(os.path.join(base_dir, "requirements.txt"), 'w', encoding='utf-8') as f:
            f.write(create_requirements())

        # .gitignore
        with open(os.path.join(base_dir, ".gitignore"), 'w', encoding='utf-8') as f:
            f.write(create_gitignore())

        print("\n📝 README.md, requirements.txt und .gitignore wurden mit Inhalt erstellt!")

    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        sys.exit(1)
