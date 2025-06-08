# RFID-Login & QR-Wareneingang - Paralleles Multi-User System

🚀 **Neu**: Alle Benutzer können jetzt parallel alle verfügbaren Scanner nutzen! 

Erweiterte Desktop-Anwendung für Zeiterfassung und Wareneingang mit parallelem Multi-Scanner-Support.

## ✨ Neue Features (Multi-Scanner System)

- **🔄 Paralleles Scannen**: Alle angemeldeten Benutzer können gleichzeitig alle verfügbaren Scanner nutzen
- **📸 Multi-Kamera-Support**: Unterstützung für mehrere USB-Kameras gleichzeitig
- **🎯 Flexible QR-Zuordnung**: Round-Robin, manuelle Auswahl oder letzter RFID-Benutzer
- **📊 Live-Scanner-Status**: Echtzeit-Übersicht über alle aktiven Scanner
- **⚡ Optimierte Performance**: Intelligente Frame-Verarbeitung und Cross-Scanner Duplikat-Verhinderung
- **🔧 Dynamische Steuerung**: Scanner können zur Laufzeit gestartet/gestoppt werden

## 🎯 Core Features

- **RFID-basiertes Login/Logout**: Mitarbeiter melden sich mit RFID-Tags an/ab
- **Automatische Zeiterfassung**: Sessions werden in SQL Server gespeichert
- **Multi-User parallel**: Mehrere Mitarbeiter können gleichzeitig arbeiten
- **QR-Code Scanner**: Erfassung von Wareneingängen per Webcam(s)
- **Echtzeit-Anzeige**: Live-Timer für aktive Sessions
- **Direkte SQL-Anbindung**: Keine zusätzliche API notwendig

## 🛠️ Voraussetzungen

### Software
- Python 3.10 oder höher
- Microsoft ODBC Driver 18 for SQL Server
- Windows 10/11

### Hardware
- USB RFID-Reader (HID-Modus, gibt Tag-ID + Enter aus)
- **1-4 Webcams** für QR-Code Scanning (Neu: Multi-Kamera Support!)

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

### 4. Konfiguration für Multi-Scanner System
Kopieren Sie `.env.example` zu `.env` und konfigurieren Sie:

```env
# Datenbank
MSSQL_SERVER=116.202.224.248
MSSQL_USER=sa
MSSQL_PASSWORD=your_password
MSSQL_DATABASE=RdScanner

# Multi-Scanner Konfiguration (NEU!)
CAMERA_INDICES=0,1,2                    # Mehrere Kameras
QR_DEFAULT_ASSIGNMENT_MODE=round_robin   # Automatische Zuordnung
SCANNER_VIDEO_DISPLAY=primary            # Video nur von erster Kamera
MAX_SCANNERS=4                          # Max. gleichzeitige Scanner

# Scanner-Optimierung
SCANNER_FRAME_WIDTH=640
SCANNER_FRAME_HEIGHT=480
SCANNER_FPS=30
SCANNER_COOLDOWN=0.5
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

### Paralleles Multi-User System (Empfohlen)
```bash
# Mit System-Test (empfohlen beim ersten Start)
run_parallel.bat

# Oder direkt
python app.py
```

### Klassische Versionen (noch verfügbar)
```bash
# Vereinfachte Version
python app.py

# Tab-basierte Version  
python app_tabs.py
```

## 📱 Bedienung - Paralleles System

### 🔑 Benutzer-Anmeldung
1. **RFID-Tag scannen** → Benutzer wird angemeldet und erscheint in der Liste
2. **Mehrere Benutzer** können gleichzeitig angemeldet sein
3. **Erneuter RFID-Scan** → Benutzer wird abgemeldet

### 📸 QR-Code Scanning (Parallel)
1. **Automatisch (Round-Robin)**: QR-Codes werden automatisch reihum an alle angemeldeten Benutzer verteilt
2. **Manuell**: Bei jedem QR-Code erscheint Auswahl für Benutzer-Zuordnung  
3. **Letzter RFID**: QR-Codes gehen an den Benutzer, der zuletzt seinen RFID-Tag gescannt hat
4. **Multi-Scanner**: Alle Kameras scannen parallel - egal welche Kamera den Code erkennt

### ⚙️ Scanner-Verwaltung
- **Live-Status**: Übersicht über alle aktiven Scanner
- **Start/Stop**: Scanner können zur Laufzeit gestartet/gestoppt werden
- **Automatischer Neustart**: Fehlerhafte Scanner werden automatisch neu gestartet
- **Performance-Monitoring**: FPS und Scan-Statistiken pro Scanner

## 🔧 Konfiguration

### QR-Zuordnungsmodi

| Modus | Beschreibung | Ideal für |
|-------|--------------|-----------|
| `round_robin` | Automatische Verteilung reihum | Gleichmäßige Arbeitsverteilung |
| `manual` | Manuelle Auswahl bei jedem Scan | Spezifische Zuordnungen |
| `last_rfid` | Zuordnung an letzten RFID-Benutzer | Ein Hauptbearbeiter |

### Multi-Scanner Szenarien

```env
# Szenario 1: Einzelarbeitsplatz
CAMERA_INDICES=0
QR_DEFAULT_ASSIGNMENT_MODE=manual

# Szenario 2: Team-Arbeitsplatz (2-3 Personen)  
CAMERA_INDICES=0,1
QR_DEFAULT_ASSIGNMENT_MODE=round_robin
MAX_SCANNERS=2

# Szenario 3: Hochdurchsatz-Station (4+ Personen)
CAMERA_INDICES=0,1,2,3
QR_DEFAULT_ASSIGNMENT_MODE=round_robin
SCANNER_VIDEO_DISPLAY=none  # Kein Video für bessere Performance
MAX_SCANNERS=4
```

## 📊 QR-Code Formate

Das System erkennt automatisch verschiedene Formate:

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

## 🧪 System-Test

Führen Sie vor dem ersten Produktiveinsatz einen umfassenden Test durch:

```bash
python test_all_components.py
```

Der Test prüft:
- ✅ Python-Module und Dependencies
- ✅ Datenbank-Verbindung und Struktur  
- ✅ RFID-Tags Import
- ✅ **Multi-Kamera-Erkennung**
- ✅ **Scanner-Performance**
- ✅ Models und Konfiguration

## 🔧 Troubleshooting

### Multi-Scanner Probleme

#### 🚫 Kameras werden nicht erkannt
```env
# Verschiedene Indizes testen
CAMERA_INDICES=0,1,2,3

# Backend wechseln  
CAMERA_BACKEND=AUTO  # oder DSHOW, V4L2
```

#### 🐌 Langsame Performance mit mehreren Scannern
```env
# Auflösung reduzieren
SCANNER_FRAME_WIDTH=320
SCANNER_FRAME_HEIGHT=240

# Frame-Skip erhöhen
SCANNER_FRAME_SKIP=5

# Video deaktivieren
SCANNER_VIDEO_DISPLAY=none
```

#### ⚡ Zu viele QR-Code Duplikate
```env
# Globales Cooldown erhöhen
QR_GLOBAL_COOLDOWN=600  # 10 Minuten

# Cross-Scanner Check aktivieren
QR_CROSS_USER_CHECK=True
```

### Klassische Probleme

#### RFID-Reader wird nicht erkannt
- Prüfen Sie ob der Reader im HID-Modus ist
- Testen Sie mit einem Texteditor ob Tags ausgegeben werden

#### Datenbankverbindung schlägt fehl
- ODBC Driver 18 installiert?
- Firewall-Einstellungen prüfen
- Server erreichbar? (`ping 116.202.224.248`)

## 📊 Logs und Monitoring

Logs werden im `logs/` Verzeichnis gespeichert:
- `ParallelApp_YYYYMMDD.log`: Hauptanwendung
- `QRScanner_YYYYMMDD.log`: Scanner-Events  
- `Database_YYYYMMDD.log`: Datenbankoperationen
- `HIDListener_YYYYMMDD.log`: RFID-Events

### Live-Monitoring
- **Scanner-Status**: Echtzeit-Übersicht in der Anwendung
- **Performance-Metriken**: FPS, Scan-Rate, Verarbeitungszeit
- **Benutzer-Aktivität**: Live-Timer, Scan-Counts
- **System-Statistiken**: Gesamtscans, aktive Sessions

## 🆚 Version Comparison

| Feature | Klassisch | **Parallel (NEU)** |
|---------|-----------|---------------------|
| Benutzer pro Scanner | 1 | ∞ |
| Gleichzeitige Scanner | 1 | 1-4 |
| QR-Zuordnung | Fest | Flexibel |
| Live-Scanner-Status | ❌ | ✅ |
| Cross-Scanner Duplikat-Check | ❌ | ✅ |
| Performance-Monitoring | ❌ | ✅ |

## 🤝 Support

Bei Fragen oder Problemen:
1. **System-Test ausführen**: `python test_all_components.py`
2. **Logs prüfen** im `logs/` Verzeichnis
3. **Konfiguration validieren**: `python config.py`
4. **Hardware-Verbindungen prüfen**

## 📄 Lizenz

Proprietär - Nur für den internen Gebrauch bei Shirtful

---

🎉 **Das parallele Multi-User System ermöglicht es jedem Mitarbeiter, jeden verfügbaren Scanner zu nutzen - maximale Flexibilität und Effizienz!**