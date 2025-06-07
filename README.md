# Wareneingang Scanner Anwendung

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![License](https://img.shields.io/badge/license-proprietary-red.svg)

## 📋 Übersicht

Die **Wareneingang Scanner Anwendung** ist eine Desktop-Lösung für die effiziente Verwaltung des Wareneingangs bei Shirtful. Die Anwendung kombiniert RFID-basierte Benutzerauthentifizierung mit QR-Code-Scanning für eine nahtlose Paketerfassung.

### 🌟 Hauptfunktionen

- **🔐 RFID-Login**: Sichere Anmeldung per RFID-Karte (HID-Modus)
- **📷 QR-Code Scanner**: Automatische Erkennung von Paketinformationen
- **👥 Multi-User Support**: Mehrere Benutzer können gleichzeitig arbeiten
- **⏱️ Zeiterfassung**: Automatische Arbeitszeiterfassung
- **🗄️ Datenbank-Integration**: Direkte Anbindung an MSSQL Server
- **🎨 Moderne GUI**: Benutzerfreundliche Tkinter-Oberfläche

## 🚀 Schnellstart

### Voraussetzungen

- Windows 10/11
- Python 3.10 oder höher
- MSSQL Server Zugang
- TSHRW380BZMP RFID-Reader (HID-Modus)
- Webcam für QR-Code-Scanning

### Installation

1. **Repository klonen**
   ```bash
   cd C:\Users\damja\PycharmProjects\Shirtful\Wareneingang
   ```

2. **Virtuelle Umgebung erstellen**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Konfiguration anpassen**
   - Kopieren Sie `config/settings.example.py` nach `config/settings.py`
   - Passen Sie die Datenbankverbindung an
   - Konfigurieren Sie den RFID-Reader

5. **Anwendung starten**
   ```bash
   python main.py
   ```

## 📁 Projektstruktur

```
Wareneingang/
├── main.py                 # Haupteinstiegspunkt
├── requirements.txt        # Python-Abhängigkeiten
├── README.md              # Diese Datei
├── .gitignore             # Git-Ignorierliste
│
├── config/                # Konfigurationsdateien
│   ├── settings.py        # Hauptkonfiguration
│   ├── database.py        # Datenbankeinstellungen
│   └── constants.py       # Konstanten
│
├── src/                   # Quellcode
│   ├── gui/              # GUI-Komponenten
│   │   ├── main_window.py
│   │   ├── login_screen.py
│   │   ├── scanner_screen.py
│   │   └── widgets.py
│   │
│   ├── scanner/          # QR-Scanner Module
│   │   ├── qr_scanner.py
│   │   ├── camera_handler.py
│   │   └── decoder.py
│   │
│   ├── rfid/            # RFID-Reader Module
│   │   ├── reader.py
│   │   ├── hid_listener.py
│   │   └── tag_validator.py
│   │
│   ├── database/        # Datenbank-Layer
│   │   ├── connection.py
│   │   ├── user_repository.py
│   │   └── scan_repository.py
│   │
│   ├── models/          # Datenmodelle
│   │   ├── user.py
│   │   ├── scan_data.py
│   │   └── package.py
│   │
│   └── utils/           # Hilfsfunktionen
│       ├── logger.py
│       ├── validators.py
│       └── helpers.py
│
├── assets/              # Ressourcen
│   ├── images/         # Bilder und Icons
│   └── sounds/         # Soundeffekte
│
├── logs/               # Log-Dateien
├── tests/              # Unit-Tests
└── docs/               # Dokumentation
```

## 💻 Verwendung

### 1. Anmeldung

1. Starten Sie die Anwendung
2. Der Login-Bildschirm erscheint
3. Halten Sie Ihre RFID-Karte an den Reader
4. Bei erfolgreicher Authentifizierung öffnet sich ein neuer Tab

### 2. Pakete scannen

1. Klicken Sie auf "Paket scannen" oder drücken Sie die Leertaste
2. Halten Sie den QR-Code des Pakets vor die Kamera
3. Die Paketinformationen werden automatisch erfasst:
   - Auftragsnummer
   - Paketnummer
   - Kundenname (falls vorhanden)

### 3. Multi-User-Betrieb

- Mehrere Benutzer können sich gleichzeitig anmelden
- Jeder Benutzer erhält einen eigenen Tab
- Tabs können unabhängig voneinander arbeiten

### 4. Abmeldung

- Klicken Sie auf "Logout" in Ihrem Tab
- Oder schließen Sie den Tab direkt
- Die Arbeitszeit wird automatisch erfasst

## ⌨️ Tastenkombinationen

| Taste | Funktion |
|-------|----------|
| F11 | Vollbildmodus ein/aus |
| ESC | Vollbild verlassen |
| F1 | Hilfe anzeigen |
| Ctrl+Q | Programm beenden |
| Leertaste | Paket scannen (wenn fokussiert) |

## 🗄️ Datenbank-Schema

### ScannBenutzer
- Speichert Benutzerinformationen und RFID-Tags
- Verknüpfung über EPC-Feld (decimal)

### ScannKopf
- Haupttabelle für Scan-Sessions
- Enthält Zeitstempel und Arbeitsplatz

### ScannPosition
- Detailinformationen zu gescannten Paketen
- Verknüpft mit ScannKopf über Foreign Key

### ScannTyp
- Definiert verschiedene Scan-Typen
- Wareneingang hat ID = 1

## 🔧 Konfiguration

### config/settings.py

```python
# Datenbankverbindung
DB_SERVER = "116.202.224.248"
DB_NAME = "RdScanner"
DB_USER = "sa"
DB_PASSWORD = "your_password"

# RFID-Einstellungen
RFID_TIMEOUT = 30  # Sekunden

# Scanner-Einstellungen
CAMERA_INDEX = 0
SCAN_COOLDOWN = 2  # Sekunden

# GUI-Einstellungen
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
THEME = "modern"
```

## 🐛 Fehlerbehebung

### RFID-Reader wird nicht erkannt
- Prüfen Sie, ob der Reader im HID-Modus ist
- Testen Sie mit einem Texteditor
- Starten Sie die Anwendung neu

### Kamera wird nicht gefunden
- Prüfen Sie die Kameraverbindung
- Ändern Sie CAMERA_INDEX in settings.py
- Installieren Sie Kameratreiber neu

### Datenbankverbindung fehlgeschlagen
- Prüfen Sie die Netzwerkverbindung
- Verifizieren Sie die Zugangsdaten
- Testen Sie mit SQL Server Management Studio

## 📊 Logging

Log-Dateien werden im `logs/`-Verzeichnis gespeichert:
- `wareneingang.log` - Hauptlog
- `wareneingang_error.log` - Nur Fehler

Debug-Modus aktivieren:
```bash
python main.py --debug
```

## 🧪 Tests ausführen

```bash
# Alle Tests
pytest tests/

# Spezifische Test-Datei
pytest tests/test_rfid.py -v

# Mit Coverage
pytest tests/ --cov=src --cov-report=html
```

## 📝 Entwickler-Hinweise

### Code-Stil
- Befolgen Sie PEP 8
- Verwenden Sie Type Hints wo möglich
- Dokumentieren Sie alle öffentlichen Methoden

### Neue Features
1. Erstellen Sie einen Feature-Branch
2. Implementieren Sie Tests
3. Aktualisieren Sie die Dokumentation
4. Erstellen Sie einen Pull Request

### Bekannte Einschränkungen
- Windows-only (wegen MSSQL und HID-Treiber)
- Maximal 10 gleichzeitige Benutzer empfohlen
- QR-Codes müssen gut beleuchtet sein

## 🤝 Support

Bei Fragen oder Problemen:
- 📧 Email: it@shirtful.com
- 📞 Telefon: +49 XXX XXXXX
- 💬 Slack: #wareneingang-support

## 📄 Lizenz

Copyright © 2024 Shirtful GmbH. Alle Rechte vorbehalten.

Diese Software ist Eigentum der Shirtful GmbH und nur für den internen Gebrauch lizenziert.

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** Juni 2024  
**Entwickelt von:** Shirtful IT-Team