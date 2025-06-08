#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale Konfiguration - Multi-Scanner Version
Lädt Einstellungen aus .env - erweiterte Version für parallele Scanner
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


# Multi-Scanner Konfiguration
def parse_camera_indices():
    """Parse CAMERA_INDICES from environment variable"""
    indices_str = os.getenv('CAMERA_INDICES', '0')
    try:
        # Unterstützt verschiedene Formate: "0,1,2" oder "0;1;2" oder "0 1 2"
        indices_str = indices_str.replace(';', ',').replace(' ', ',')
        indices = [int(x.strip()) for x in indices_str.split(',') if x.strip().isdigit()]
        return indices if indices else [0]
    except:
        return [0]


# Anwendungs-Konfiguration
APP_CONFIG = {
    'DEBUG': os.getenv('APP_DEBUG', 'False').lower() == 'true',
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'CAMERA_INDEX': int(os.getenv('CAMERA_INDEX', '0')),  # Fallback für alte Konfiguration
    'CAMERA_INDICES': parse_camera_indices(),  # Neue Multi-Kamera Unterstützung
    'CAMERA_BACKEND': os.getenv('CAMERA_BACKEND', 'DSHOW'),  # DSHOW, V4L2, AUTO
    'MAX_SCANNERS': int(os.getenv('MAX_SCANNERS', '4')),  # Maximale Anzahl Scanner
    'SCANNER_RETRY_DELAY': int(os.getenv('SCANNER_RETRY_DELAY', '5')),  # Sekunden zwischen Versuchen
    'AUTO_START_SCANNERS': os.getenv('AUTO_START_SCANNERS', 'True').lower() == 'true'
}

# QR-Code Assignment Konfiguration
QR_ASSIGNMENT_CONFIG = {
    'DEFAULT_MODE': os.getenv('QR_DEFAULT_ASSIGNMENT_MODE', 'round_robin'),  # round_robin, manual, last_rfid
    'AUTO_ASSIGN_TIMEOUT': int(os.getenv('QR_AUTO_ASSIGN_TIMEOUT', '10')),  # Sekunden für manuelle Auswahl
    'ROUND_ROBIN_RESET': os.getenv('QR_ROUND_ROBIN_RESET', 'session').lower(),  # session, daily, never
}

# QR-Code Duplikat-Verhinderung Konfiguration
QR_CONFIG = {
    'DUPLICATE_CHECK': os.getenv('QR_DUPLICATE_CHECK', 'True').lower() == 'true',
    'GLOBAL_COOLDOWN': int(os.getenv('QR_GLOBAL_COOLDOWN', '300')),  # 5 Minuten
    'SESSION_COOLDOWN': int(os.getenv('QR_SESSION_COOLDOWN', '3600')),  # 1 Stunde
    'CROSS_USER_DUPLICATE_CHECK': os.getenv('QR_CROSS_USER_CHECK', 'True').lower() == 'true'
}

# Scanner-spezifische Konfiguration
SCANNER_CONFIG = {
    'FRAME_WIDTH': int(os.getenv('SCANNER_FRAME_WIDTH', '640')),
    'FRAME_HEIGHT': int(os.getenv('SCANNER_FRAME_HEIGHT', '480')),
    'FPS': int(os.getenv('SCANNER_FPS', '30')),
    'BUFFER_SIZE': int(os.getenv('SCANNER_BUFFER_SIZE', '1')),
    'SCAN_COOLDOWN': float(os.getenv('SCANNER_COOLDOWN', '0.5')),  # Sekunden zwischen Scans
    'FRAME_SKIP': int(os.getenv('SCANNER_FRAME_SKIP', '3')),  # Jeden N-ten Frame analysieren
    'ENABLE_AUTOFOCUS': os.getenv('SCANNER_AUTOFOCUS', 'False').lower() == 'true',
    'VIDEO_DISPLAY': os.getenv('SCANNER_VIDEO_DISPLAY', 'primary').lower()  # primary, all, none
}

# RFID Konfiguration
RFID_CONFIG = {
    'MIN_SCAN_INTERVAL': float(os.getenv('RFID_MIN_SCAN_INTERVAL', '1.0')),
    'INPUT_TIMEOUT': float(os.getenv('RFID_INPUT_TIMEOUT', '0.5')),
    'MAX_BUFFER_LENGTH': int(os.getenv('RFID_MAX_BUFFER_LENGTH', '15')),
    'AUTO_LOGIN_LOGOUT': os.getenv('RFID_AUTO_LOGIN_LOGOUT', 'True').lower() == 'true'
}

# UI Konfiguration
UI_CONFIG = {
    'WINDOW_WIDTH': int(os.getenv('UI_WINDOW_WIDTH', '1200')),
    'WINDOW_HEIGHT': int(os.getenv('UI_WINDOW_HEIGHT', '800')),
    'MIN_WIDTH': int(os.getenv('UI_MIN_WIDTH', '1000')),
    'MIN_HEIGHT': int(os.getenv('UI_MIN_HEIGHT', '600')),
    'THEME': os.getenv('UI_THEME', 'default'),  # default, dark, light
    'SHOW_DEBUG_INFO': os.getenv('UI_SHOW_DEBUG', 'False').lower() == 'true',
    'UPDATE_INTERVAL': int(os.getenv('UI_UPDATE_INTERVAL', '1000')),  # Millisekunden
    'STATUS_MESSAGE_TIMEOUT': int(os.getenv('UI_STATUS_TIMEOUT', '5000'))  # Millisekunden
}

# Pfade
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')

# Dateien
AUTHORIZED_TAGS_FILE = os.path.join(CONFIG_DIR, 'authorized_tags.json')
SCANNER_PROFILES_FILE = os.path.join(CONFIG_DIR, 'scanner_profiles.json')

# Sicherstellen dass Verzeichnisse existieren
for directory in [LOG_DIR, CONFIG_DIR, TEMP_DIR]:
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            print(f"Warnung: Konnte Verzeichnis {directory} nicht erstellen: {e}")


# Erweiterte Konfiguration validieren
def validate_config():
    """Validiert die erweiterte Konfiguration"""
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

    # Multi-Scanner Konfiguration prüfen
    if not APP_CONFIG['CAMERA_INDICES']:
        errors.append("Keine gültigen CAMERA_INDICES konfiguriert")

    if len(APP_CONFIG['CAMERA_INDICES']) > APP_CONFIG['MAX_SCANNERS']:
        warnings.append(
            f"Mehr Kameras ({len(APP_CONFIG['CAMERA_INDICES'])}) als MAX_SCANNERS ({APP_CONFIG['MAX_SCANNERS']})")

    for idx in APP_CONFIG['CAMERA_INDICES']:
        if idx < 0 or idx > 10:
            warnings.append(f"Kamera-Index {idx} ist ungewöhnlich")

    # Backend prüfen
    if APP_CONFIG['CAMERA_BACKEND'] not in ['DSHOW', 'V4L2', 'AUTO']:
        warnings.append(f"CAMERA_BACKEND '{APP_CONFIG['CAMERA_BACKEND']}' unbekannt")

    # QR-Assignment Konfiguration prüfen
    if QR_ASSIGNMENT_CONFIG['DEFAULT_MODE'] not in ['round_robin', 'manual', 'last_rfid']:
        errors.append(f"QR_DEFAULT_ASSIGNMENT_MODE '{QR_ASSIGNMENT_CONFIG['DEFAULT_MODE']}' ungültig")

    if QR_ASSIGNMENT_CONFIG['AUTO_ASSIGN_TIMEOUT'] < 1 or QR_ASSIGNMENT_CONFIG['AUTO_ASSIGN_TIMEOUT'] > 60:
        warnings.append(f"QR_AUTO_ASSIGN_TIMEOUT {QR_ASSIGNMENT_CONFIG['AUTO_ASSIGN_TIMEOUT']}s ungewöhnlich")

    # Scanner-Konfiguration prüfen
    if SCANNER_CONFIG['FRAME_WIDTH'] < 320 or SCANNER_CONFIG['FRAME_WIDTH'] > 1920:
        warnings.append(f"SCANNER_FRAME_WIDTH {SCANNER_CONFIG['FRAME_WIDTH']} ungewöhnlich")

    if SCANNER_CONFIG['FRAME_HEIGHT'] < 240 or SCANNER_CONFIG['FRAME_HEIGHT'] > 1080:
        warnings.append(f"SCANNER_FRAME_HEIGHT {SCANNER_CONFIG['FRAME_HEIGHT']} ungewöhnlich")

    if SCANNER_CONFIG['FPS'] < 10 or SCANNER_CONFIG['FPS'] > 60:
        warnings.append(f"SCANNER_FPS {SCANNER_CONFIG['FPS']} ungewöhnlich")

    if SCANNER_CONFIG['SCAN_COOLDOWN'] < 0.1 or SCANNER_CONFIG['SCAN_COOLDOWN'] > 5.0:
        warnings.append(f"SCANNER_COOLDOWN {SCANNER_CONFIG['SCAN_COOLDOWN']}s ungewöhnlich")

    # UI-Konfiguration prüfen
    if UI_CONFIG['WINDOW_WIDTH'] < 800 or UI_CONFIG['WINDOW_WIDTH'] > 3840:
        warnings.append(f"UI_WINDOW_WIDTH {UI_CONFIG['WINDOW_WIDTH']} ungewöhnlich")

    if UI_CONFIG['WINDOW_HEIGHT'] < 600 or UI_CONFIG['WINDOW_HEIGHT'] > 2160:
        warnings.append(f"UI_WINDOW_HEIGHT {UI_CONFIG['WINDOW_HEIGHT']} ungewöhnlich")

    # QR-Konfiguration prüfen
    if QR_CONFIG['GLOBAL_COOLDOWN'] < 0 or QR_CONFIG['GLOBAL_COOLDOWN'] > 3600:
        warnings.append(f"QR_GLOBAL_COOLDOWN {QR_CONFIG['GLOBAL_COOLDOWN']}s ungewöhnlich")

    if QR_CONFIG['SESSION_COOLDOWN'] < 0 or QR_CONFIG['SESSION_COOLDOWN'] > 86400:
        warnings.append(f"QR_SESSION_COOLDOWN {QR_CONFIG['SESSION_COOLDOWN']}s ungewöhnlich")

    # RFID-Konfiguration prüfen
    if RFID_CONFIG['MIN_SCAN_INTERVAL'] < 0.1 or RFID_CONFIG['MIN_SCAN_INTERVAL'] > 10.0:
        warnings.append(f"RFID_MIN_SCAN_INTERVAL {RFID_CONFIG['MIN_SCAN_INTERVAL']}s ungewöhnlich")

    # Log-Level prüfen
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if APP_CONFIG['LOG_LEVEL'].upper() not in valid_log_levels:
        warnings.append(f"LOG_LEVEL '{APP_CONFIG['LOG_LEVEL']}' unbekannt")

    return errors, warnings


# Multi-Scanner Helper Funktionen
def get_primary_camera_index():
    """Gibt den primären Kamera-Index zurück"""
    return APP_CONFIG['CAMERA_INDICES'][0] if APP_CONFIG['CAMERA_INDICES'] else 0


def get_scanner_profile(camera_index):
    """Gibt Scanner-Profil für spezifische Kamera zurück"""
    return {
        'camera_index': camera_index,
        'frame_width': SCANNER_CONFIG['FRAME_WIDTH'],
        'frame_height': SCANNER_CONFIG['FRAME_HEIGHT'],
        'fps': SCANNER_CONFIG['FPS'],
        'buffer_size': SCANNER_CONFIG['BUFFER_SIZE'],
        'backend': APP_CONFIG['CAMERA_BACKEND'],
        'scan_cooldown': SCANNER_CONFIG['SCAN_COOLDOWN'],
        'frame_skip': SCANNER_CONFIG['FRAME_SKIP'],
        'enable_autofocus': SCANNER_CONFIG['ENABLE_AUTOFOCUS']
    }


def should_show_video_for_camera(camera_index):
    """Bestimmt ob Video für Kamera angezeigt werden soll"""
    video_display = SCANNER_CONFIG['VIDEO_DISPLAY']

    if video_display == 'none':
        return False
    elif video_display == 'primary':
        return camera_index == get_primary_camera_index()
    elif video_display == 'all':
        return True
    else:
        return camera_index == get_primary_camera_index()  # Fallback


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
        'multi_scanner': {
            'camera_indices': APP_CONFIG['CAMERA_INDICES'],
            'max_scanners': APP_CONFIG['MAX_SCANNERS'],
            'camera_backend': APP_CONFIG['CAMERA_BACKEND'],
            'auto_start': APP_CONFIG['AUTO_START_SCANNERS'],
            'video_display': SCANNER_CONFIG['VIDEO_DISPLAY']
        },
        'qr_assignment': {
            'default_mode': QR_ASSIGNMENT_CONFIG['DEFAULT_MODE'],
            'auto_timeout': QR_ASSIGNMENT_CONFIG['AUTO_ASSIGN_TIMEOUT'],
            'cross_user_check': QR_CONFIG['CROSS_USER_DUPLICATE_CHECK']
        },
        'application': {
            'debug': APP_CONFIG['DEBUG'],
            'log_level': APP_CONFIG['LOG_LEVEL'],
            'window_size': f"{UI_CONFIG['WINDOW_WIDTH']}x{UI_CONFIG['WINDOW_HEIGHT']}"
        },
        'scanner_settings': {
            'resolution': f"{SCANNER_CONFIG['FRAME_WIDTH']}x{SCANNER_CONFIG['FRAME_HEIGHT']}",
            'fps': SCANNER_CONFIG['FPS'],
            'scan_cooldown': SCANNER_CONFIG['SCAN_COOLDOWN'],
            'frame_skip': SCANNER_CONFIG['FRAME_SKIP']
        },
        'duplicate_prevention': {
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

    print("🔧 Multi-Scanner Konfiguration:")
    print("=" * 60)

    print("📊 Datenbank:")
    print(f"   Server: {summary['database']['server']}")
    print(f"   Datenbank: {summary['database']['database']}")
    print(f"   Benutzer: {summary['database']['user']}")
    print(f"   Passwort: {'✅ gesetzt' if summary['database']['password_set'] else '❌ nicht gesetzt'}")

    print("\n📸 Multi-Scanner:")
    print(f"   Kamera-Indizes: {summary['multi_scanner']['camera_indices']}")
    print(f"   Max Scanner: {summary['multi_scanner']['max_scanners']}")
    print(f"   Backend: {summary['multi_scanner']['camera_backend']}")
    print(f"   Auto-Start: {summary['multi_scanner']['auto_start']}")
    print(f"   Video-Anzeige: {summary['multi_scanner']['video_display']}")

    print("\n🎯 QR-Code Zuordnung:")
    print(f"   Standard-Modus: {summary['qr_assignment']['default_mode']}")
    print(f"   Auto-Timeout: {summary['qr_assignment']['auto_timeout']}s")
    print(f"   Cross-User Check: {summary['qr_assignment']['cross_user_check']}")

    print("\n⚙️ Scanner-Einstellungen:")
    print(f"   Auflösung: {summary['scanner_settings']['resolution']}")
    print(f"   FPS: {summary['scanner_settings']['fps']}")
    print(f"   Scan-Cooldown: {summary['scanner_settings']['scan_cooldown']}s")
    print(f"   Frame-Skip: {summary['scanner_settings']['frame_skip']}")

    print("\n📱 Anwendung:")
    print(f"   Debug-Modus: {summary['application']['debug']}")
    print(f"   Log-Level: {summary['application']['log_level']}")
    print(f"   Fenstergröße: {summary['application']['window_size']}")

    print("\n🚫 QR-Duplikat-Verhinderung:")
    print(f"   Aktiviert: {summary['duplicate_prevention']['enabled']}")
    print(f"   Global Cooldown: {summary['duplicate_prevention']['global_cooldown_minutes']} Min")
    print(f"   Session Cooldown: {summary['duplicate_prevention']['session_cooldown_minutes']} Min")

    print("=" * 60)


# Konfiguration für verschiedene Szenarien
def get_single_scanner_config():
    """Konfiguration für Single-Scanner Modus"""
    config = get_config_summary()
    config['multi_scanner']['camera_indices'] = [get_primary_camera_index()]
    config['qr_assignment']['default_mode'] = 'manual'
    return config


def get_multi_scanner_config():
    """Konfiguration für Multi-Scanner Modus"""
    return get_config_summary()


def is_multi_scanner_mode():
    """Prüft ob Multi-Scanner Modus aktiv ist"""
    return len(APP_CONFIG['CAMERA_INDICES']) > 1


# Bei direktem Aufruf Konfiguration anzeigen
if __name__ == "__main__":
    print_config_summary()
    print(f"\n📋 Multi-Scanner Modus: {'✅ Aktiv' if is_multi_scanner_mode() else '❌ Single Scanner'}")
    if is_multi_scanner_mode():
        print(f"   Primäre Kamera: {get_primary_camera_index()}")
        print(f"   Alle Kameras: {APP_CONFIG['CAMERA_INDICES']}")

    print(f"\n🎮 Empfohlene .env Einstellungen für Multi-Scanner:")
    print("   CAMERA_INDICES=0,1,2")
    print("   QR_DEFAULT_ASSIGNMENT_MODE=round_robin")
    print("   SCANNER_VIDEO_DISPLAY=primary")
    print("   MAX_SCANNERS=4")