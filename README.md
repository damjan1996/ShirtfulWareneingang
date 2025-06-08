# RFID-Login & QR-Wareneingang

Minimalistische Desktop-Anwendung für Zeiterfassung und Wareneingang mit RFID und QR-Code Scanner.

## 🎯 Features

- **RFID-basiertes Login/Logout**: Mitarbeiter melden sich mit RFID-Tags an/ab
- **Automatische Zeiterfassung**: Sessions werden in SQL Server gespeichert
- **QR-Code Scanner**: Erfassung von Wareneingängen per Webcam
- **Multi-User**: Mehrere Mitarbeiter können gleichzeitig angemeldet sein
- **Echtzeit-Anzeige**: Live-Timer für aktive Sessions
- **Direkte SQL-Anbindung**: Keine zusätzliche API notwendig

## 🛠️ Voraussetzungen

### Software
- Python 3.10 oder höher
- Microsoft ODBC Driver 18 for SQL Server
- Windows 10/11

### Hardware
- USB RFID-Reader (HID-Modus, gibt Tag-ID + Enter aus)
- Webcam für QR-Code Scanning

## 📦 Installation

### 1. Repository klonen oder entpacken
```bash
cd C:\Users\damja\PycharmProjects\Wareneingang
```

### 2. Virtuelle Umgebung erstellen
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 4. Konfiguration
Kopieren Sie `.env.example` zu `.env` und passen Sie die Werte an:
```env
MSSQL_SERVER=116.202.224.248
MSSQL_USER=sa
MSSQL_PASSWORD=your_password
MSSQL_DATABASE=RdScanner
```

### 5. Datenbank einrichten
```bash
python database/add_database_rdscannershirtful.py
```

### 6. RFID-Tags importieren
```bash
python database/import_rfid_tags.py
```

## 🚀 Anwendung starten

### Einfacher Start
Doppelklick auf `run.bat`

### Oder über Terminal
```bash
python app.py
```

## 📱 Bedienung

### Anmelden
1. RFID-Tag an den Reader halten
2. Benutzer erscheint in der linken Liste
3. Timer startet automatisch

### QR-Codes scannen
1. Benutzer in der Liste auswählen
2. "Scanner starten" klicken
3. QR-Code vor die Kamera halten
4. Erfasste Codes werden automatisch gespeichert

### Abmelden
- Entweder: Gleichen RFID-Tag erneut scannen
- Oder: Benutzer auswählen und "Logout" klicken

## 🗄️ Datenbankstruktur

### Haupttabellen
- **ScannBenutzer**: Mitarbeiterstammdaten mit RFID-Tags
- **Sessions**: Arbeitszeitsessions (Start/Ende)
- **QrScans**: Erfasste QR-Codes mit Zeitstempel

### Erweiterte Tabellen (optional)
- **ScannTyp**: Verschiedene Scan-Typen (Wareneingang, QK, etc.)
- **ScannKopf**: Scan-Vorgänge
- **ScannPosition**: Detaildaten zu Scans

## 🧪 Tests

### Komponenten testen
```bash
# Datenbankverbindung testen
python database/test_connection.py

# RFID-Reader testen
python hid_listener.py

# QR-Scanner testen
python qr_scanner.py

# Alle Tests ausführen
python -m pytest tests/
```

## 📝 QR-Code Formate

Die Anwendung erkennt verschiedene QR-Code Formate:

### JSON Format
```json
{
  "kunde": "ABC GmbH",
  "auftrag": "12345",
  "paket": "1/3"
}
```

### Key-Value Format
```
Kunde:ABC GmbH^Auftrag:12345^Paket:1/3
```

### Einfacher Text
```
Beliebiger Text wird auch akzeptiert
```

## 🔧 Troubleshooting

### RFID-Reader wird nicht erkannt
- Prüfen Sie ob der Reader im HID-Modus ist
- Testen Sie mit einem Texteditor ob Tags ausgegeben werden

### Kamera wird nicht gefunden
- Prüfen Sie die CAMERA_INDEX Einstellung in .env
- Standard ist 0, bei mehreren Kameras ggf. 1, 2, etc.

### Datenbankverbindung schlägt fehl
- ODBC Driver 18 installiert?
- Firewall-Einstellungen prüfen
- Server erreichbar? (ping)

## 📊 Logs

Logs werden im `logs/` Verzeichnis gespeichert:
- `MainApp_YYYYMMDD.log`: Hauptanwendung
- `Database_YYYYMMDD.log`: Datenbankoperationen
- `HIDListener_YYYYMMDD.log`: RFID-Events
- `QRScanner_YYYYMMDD.log`: QR-Scanner Events

## 🤝 Support

Bei Fragen oder Problemen:
1. Logs prüfen
2. `python database/test_connection.py` ausführen
3. Hardware-Verbindungen prüfen

## 📄 Lizenz

Proprietär - Nur für den internen Gebrauch bei Shirtful