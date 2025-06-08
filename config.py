#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale Konfiguration
Lädt Einstellungen aus .env - erweiterte Version
"""

import os
from dotenv import load_dotenv

# .env laden
load_dotenv()

# Datenbank-Konfiguration
DB_CONFIG = {
    'server': os.getenv('MSSQL_SERVER', 'localhost'),
    'database': os.getenv('MSSQL_DATABASE', 'RdScanner'),
    'user': os.getenv('MSSQL_USER', 'sa'),
    'password': os.getenv('MSSQL_PASSWORD', ''),
    'driver': '{ODBC Driver 18 for SQL Server}',
    'trust_cert': True,
    'encrypt': False
}

# Anwendungs-Konfiguration
APP_CONFIG = {
    'DEBUG': os.getenv('APP_DEBUG', 'False').lower() == 'true',
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'CAMERA_INDEX': int(os.getenv('CAMERA_INDEX', '0')),
    'CAMERA_BACKEND': os.getenv('CAMERA_BACKEND', 'DSHOW')  # DSHOW, V4L2, AUTO
}

# QR-Code Duplikat-Verhinderung Konfiguration
QR_CONFIG = {
    'DUPLICATE_CHECK': os.getenv('QR_DUPLICATE_CHECK', 'True').lower() == 'true',
    'GLOBAL_COOLDOWN': int(os.getenv('QR_GLOBAL_COOLDOWN', '300')),  # 5 Minuten
    'SESSION_COOLDOWN': int(os.getenv('QR_SESSION_COOLDOWN', '3600')),  # 1 Stunde
}

# Pfade
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')

# Dateien
AUTHORIZED_TAGS_FILE = os.path.join(CONFIG_DIR, 'authorized_tags.json')

# Sicherstellen dass Verzeichnisse existieren
for directory in [LOG_DIR, CONFIG_DIR, TEMP_DIR]:
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            print(f"Warnung: Konnte Verzeichnis {directory} nicht erstellen: {e}")


# Konfiguration validieren
def validate_config():
    """Validiert die Konfiguration"""
    errors = []
    warnings = []

    # Datenbank-Konfiguration prüfen
    if not DB_CONFIG['server']:
        errors.append("MSSQL_SERVER nicht konfiguriert")
    if not DB_CONFIG['database']:
        errors.append("MSSQL_DATABASE nicht konfiguriert")
    if not DB_CONFIG['user']:
        errors.append("MSSQL_USER nicht konfiguriert")
    if not DB_CONFIG['password']:
        warnings.append("MSSQL_PASSWORD ist leer")

    # Kamera-Konfiguration prüfen
    if APP_CONFIG['CAMERA_INDEX'] < 0 or APP_CONFIG['CAMERA_INDEX'] > 10:
        warnings.append(f"CAMERA_INDEX {APP_CONFIG['CAMERA_INDEX']} ungewöhnlich")

    if APP_CONFIG['CAMERA_BACKEND'] not in ['DSHOW', 'V4L2', 'AUTO']:
        warnings.append(f"CAMERA_BACKEND '{APP_CONFIG['CAMERA_BACKEND']}' unbekannt")

    # QR-Konfiguration prüfen
    if QR_CONFIG['GLOBAL_COOLDOWN'] < 0 or QR_CONFIG['GLOBAL_COOLDOWN'] > 3600:
        warnings.append(f"QR_GLOBAL_COOLDOWN {QR_CONFIG['GLOBAL_COOLDOWN']}s ungewöhnlich")

    if QR_CONFIG['SESSION_COOLDOWN'] < 0 or QR_CONFIG['SESSION_COOLDOWN'] > 86400:
        warnings.append(f"QR_SESSION_COOLDOWN {QR_CONFIG['SESSION_COOLDOWN']}s ungewöhnlich")

    # Log-Level prüfen
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if APP_CONFIG['LOG_LEVEL'].upper() not in valid_log_levels:
        warnings.append(f"LOG_LEVEL '{APP_CONFIG['LOG_LEVEL']}' unbekannt")

    return errors, warnings


# Konfiguration beim Import validieren
_config_errors, _config_warnings = validate_config()

if _config_errors:
    print("❌ Konfigurationsfehler gefunden:")
    for error in _config_errors:
        print(f"   - {error}")
    print("Bitte überprüfen Sie Ihre .env Datei!")

if _config_warnings:
    print("⚠️ Konfigurationswarnungen:")
    for warning in _config_warnings:
        print(f"   - {warning}")


# Debug-Informationen
def get_config_summary():
    """Gibt eine Zusammenfassung der aktuellen Konfiguration zurück"""
    return {
        'database': {
            'server': DB_CONFIG['server'],
            'database': DB_CONFIG['database'],
            'user': DB_CONFIG['user'],
            'password_set': bool(DB_CONFIG['password'])
        },
        'application': {
            'debug': APP_CONFIG['DEBUG'],
            'log_level': APP_CONFIG['LOG_LEVEL'],
            'camera_index': APP_CONFIG['CAMERA_INDEX'],
            'camera_backend': APP_CONFIG['CAMERA_BACKEND']
        },
        'qr_duplicate_prevention': {
            'enabled': QR_CONFIG['DUPLICATE_CHECK'],
            'global_cooldown_minutes': QR_CONFIG['GLOBAL_COOLDOWN'] // 60,
            'session_cooldown_minutes': QR_CONFIG['SESSION_COOLDOWN'] // 60
        },
        'paths': {
            'base_dir': BASE_DIR,
            'log_dir': LOG_DIR,
            'config_dir': CONFIG_DIR,
            'temp_dir': TEMP_DIR
        }
    }


def print_config_summary():
    """Druckt eine Konfigurationszusammenfassung"""
    summary = get_config_summary()

    print("🔧 Aktuelle Konfiguration:")
    print("=" * 50)

    print("📊 Datenbank:")
    print(f"   Server: {summary['database']['server']}")
    print(f"   Datenbank: {summary['database']['database']}")
    print(f"   Benutzer: {summary['database']['user']}")
    print(f"   Passwort: {'✅ gesetzt' if summary['database']['password_set'] else '❌ nicht gesetzt'}")

    print("\n📱 Anwendung:")
    print(f"   Debug-Modus: {summary['application']['debug']}")
    print(f"   Log-Level: {summary['application']['log_level']}")
    print(f"   Kamera-Index: {summary['application']['camera_index']}")
    print(f"   Kamera-Backend: {summary['application']['camera_backend']}")

    print("\n🚫 QR-Duplikat-Verhinderung:")
    print(f"   Aktiviert: {summary['qr_duplicate_prevention']['enabled']}")
    print(f"   Global Cooldown: {summary['qr_duplicate_prevention']['global_cooldown_minutes']} Min")
    print(f"   Session Cooldown: {summary['qr_duplicate_prevention']['session_cooldown_minutes']} Min")

    print("=" * 50)


# Bei direktem Aufruf Konfiguration anzeigen
if __name__ == "__main__":
    print_config_summary()