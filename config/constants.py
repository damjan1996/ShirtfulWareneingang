#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konstanten für die Wareneingang-Anwendung
==========================================

Zentrale Definition aller Konstanten und Konfigurationswerte.
"""

# Anwendungsinformationen
APP_NAME = "Wareneingang Scanner"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Shirtful GmbH"
APP_EMAIL = "it@shirtful.com"
COMPANY_NAME = "Shirtful GmbH"

# GUI-Konstanten
WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"
DEFAULT_WINDOW_WIDTH = 1024
DEFAULT_WINDOW_HEIGHT = 768
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# Farben (Hex-Codes)
COLORS = {
    'PRIMARY': '#2196F3',  # Blau
    'SUCCESS': '#4CAF50',  # Grün
    'WARNING': '#FF9800',  # Orange
    'ERROR': '#F44336',  # Rot
    'INFO': '#00BCD4',  # Cyan
    'DARK': '#212529',  # Dunkelgrau
    'LIGHT': '#F8F9FA',  # Hellgrau
    'WHITE': '#FFFFFF',  # Weiß
    'BLACK': '#000000',  # Schwarz
    'BACKGROUND': '#F0F2F5',  # Hintergrund
    'SURFACE': '#FFFFFF',  # Oberfläche
    'BORDER': '#E0E0E0',  # Rahmen
}

# Schriftarten
FONTS = {
    'DEFAULT': ('Segoe UI', 10),
    'HEADING1': ('Segoe UI', 24, 'bold'),
    'HEADING2': ('Segoe UI', 18, 'bold'),
    'HEADING3': ('Segoe UI', 14, 'bold'),
    'BUTTON': ('Segoe UI', 12),
    'LABEL': ('Segoe UI', 10),
    'SMALL': ('Segoe UI', 8),
    'MONOSPACE': ('Consolas', 10),
}

# Button-Größen
BUTTON_SIZES = {
    'LARGE': {'width': 200, 'height': 60},
    'MEDIUM': {'width': 150, 'height': 45},
    'SMALL': {'width': 100, 'height': 35},
    'ICON': {'width': 40, 'height': 40},
}

# RFID-Konstanten
RFID_TAG_MIN_LENGTH = 8
RFID_TAG_MAX_LENGTH = 20
RFID_TIMEOUT_SECONDS = 30
RFID_BEEP_ON_SUCCESS = True
RFID_BEEP_ON_ERROR = True

# Scanner-Konstanten
CAMERA_DEFAULT_INDEX = 0
CAMERA_RESOLUTION = (640, 480)
CAMERA_FPS = 30
SCAN_COOLDOWN_MS = 2000  # Millisekunden zwischen Scans
QR_CODE_MIN_SIZE = 50  # Minimale Pixelgröße für QR-Code-Erkennung

# Datenbank-Konstanten
DB_TIMEOUT_SECONDS = 30
DB_MAX_RETRIES = 3
DB_RETRY_DELAY_SECONDS = 5

# ScannTyp IDs (aus der Datenbank)
SCAN_TYP_WARENEINGANG = 1
SCAN_TYP_RAHMENSPANNEN = 2
SCAN_TYP_STICKEN = 3
SCAN_TYP_VERSAEUBERN = 4
SCAN_TYP_QUALITAETSKONTROLLE = 5
SCAN_TYP_WARENAUSGANG = 6

# Arbeitsplatz-Bezeichnungen
ARBEITSPLATZ_PREFIX = "WE"  # Wareneingang
DEFAULT_ARBEITSPLATZ = f"{ARBEITSPLATZ_PREFIX}-01"

# Status-Codes
STATUS_AKTIV = 0
STATUS_INAKTIV = 1
STATUS_GELOESCHT = 2

# Zeiterfassung
WORKDAY_START_HOUR = 7
WORKDAY_END_HOUR = 18
BREAK_AFTER_HOURS = 6
MIN_BREAK_DURATION_MINUTES = 30
OVERTIME_THRESHOLD_HOURS = 8

# Sound-Dateien (relativ zu assets/sounds/)
SOUNDS = {
    'BEEP_SUCCESS': 'beep_success.wav',
    'BEEP_ERROR': 'beep_error.wav',
    'LOGIN': 'login.wav',
    'LOGOUT': 'logout.wav',
    'SCAN': 'scan.wav',
    'WARNING': 'warning.wav',
}

# Icons (relativ zu assets/images/)
ICONS = {
    'APP': 'icon.ico',
    'LOGIN': 'login.png',
    'LOGOUT': 'logout.png',
    'SCAN': 'scan.png',
    'USER': 'user.png',
    'PACKAGE': 'package.png',
    'SETTINGS': 'settings.png',
    'HELP': 'help.png',
    'ERROR': 'error.png',
    'SUCCESS': 'success.png',
    'WARNING': 'warning.png',
}

# Nachrichten
MESSAGES = {
    'WELCOME': "Willkommen im Wareneingang-System",
    'LOGIN_PROMPT': "Bitte halten Sie Ihre RFID-Karte an den Reader",
    'LOGIN_SUCCESS': "Erfolgreich angemeldet als {name}",
    'LOGIN_FAILED': "Anmeldung fehlgeschlagen. Karte nicht erkannt.",
    'LOGOUT_CONFIRM': "Möchten Sie sich wirklich abmelden?",
    'LOGOUT_SUCCESS': "Erfolgreich abgemeldet",
    'SCAN_PROMPT': "Halten Sie den QR-Code vor die Kamera",
    'SCAN_SUCCESS': "Paket erfolgreich gescannt",
    'SCAN_DUPLICATE': "Paket wurde bereits gescannt",
    'DB_ERROR': "Datenbankfehler aufgetreten",
    'CAMERA_ERROR': "Kamera konnte nicht geöffnet werden",
    'BREAK_REMINDER': "Sie arbeiten seit über 6 Stunden. Bitte machen Sie eine Pause!",
}

# Reguläre Ausdrücke
REGEX_PATTERNS = {
    'AUFTRAGS_NR': r'^[A-Z]{2}-\d+$',
    'PAKET_NR': r'^\d{10,}$',
    'RFID_TAG': r'^[0-9A-Fa-f]+$',
    'EMAIL': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
}

# Datei-Endungen
FILE_EXTENSIONS = {
    'LOG': '.log',
    'CSV': '.csv',
    'JSON': '.json',
    'BACKUP': '.bak',
    'IMAGE': ['.png', '.jpg', '.jpeg', '.bmp'],
}

# Limits
LIMITS = {
    'MAX_CONCURRENT_USERS': 10,
    'MAX_SCANS_PER_SESSION': 1000,
    'MAX_LOG_SIZE_MB': 100,
    'MAX_BACKUP_FILES': 10,
    'SESSION_TIMEOUT_MINUTES': 480,  # 8 Stunden
}

# API-Endpoints (falls zukünftig benötigt)
API_ENDPOINTS = {
    'BASE_URL': 'https://api.shirtful.com/v1',
    'AUTH': '/auth',
    'USERS': '/users',
    'SCANS': '/scans',
    'PACKAGES': '/packages',
}

# Debug-Einstellungen
DEBUG_OPTIONS = {
    'SHOW_FPS': False,
    'SHOW_QR_OVERLAY': True,
    'LOG_SQL_QUERIES': False,
    'SAVE_SCAN_IMAGES': False,
    'MOCK_RFID': False,
    'MOCK_CAMERA': False,
}

# Export-Formate
EXPORT_FORMATS = {
    'CSV': {
        'extension': '.csv',
        'delimiter': ';',
        'encoding': 'utf-8-sig',  # Mit BOM für Excel
    },
    'JSON': {
        'extension': '.json',
        'indent': 2,
        'ensure_ascii': False,
    },
    'EXCEL': {
        'extension': '.xlsx',
        'engine': 'openpyxl',
    },
}

# Tastenkombinationen
KEYBOARD_SHORTCUTS = {
    'FULLSCREEN': 'F11',
    'EXIT_FULLSCREEN': 'Escape',
    'QUIT': 'Ctrl+Q',
    'HELP': 'F1',
    'SCAN': 'Space',
    'LOGIN': 'Ctrl+L',
    'LOGOUT': 'Ctrl+O',
    'EXPORT': 'Ctrl+E',
    'SETTINGS': 'Ctrl+S',
}

# Sprachen (für zukünftige Mehrsprachigkeit)
LANGUAGES = {
    'de': 'Deutsch',
    'en': 'English',
    'tr': 'Türkçe',
    'pl': 'Polski',
}
DEFAULT_LANGUAGE = 'de'

# Datum/Zeit-Formate
DATE_FORMATS = {
    'DEFAULT': '%Y-%m-%d %H:%M:%S',
    'DATE_ONLY': '%Y-%m-%d',
    'TIME_ONLY': '%H:%M:%S',
    'FILENAME': '%Y%m%d_%H%M%S',
    'DISPLAY': '%d.%m.%Y %H:%M',
    'LOG': '%Y-%m-%d %H:%M:%S.%f',
}

# Performance-Einstellungen
PERFORMANCE = {
    'DB_CONNECTION_POOL_SIZE': 5,
    'CAMERA_BUFFER_SIZE': 1,
    'QR_DECODE_THREADS': 2,
    'LOG_ROTATION_CHECK_INTERVAL': 3600,  # Sekunden
    'CACHE_EXPIRY_SECONDS': 300,
}


# Utility-Funktionen
def get_color_rgb(color_name: str) -> tuple:
    """
    Konvertiert Hex-Farbe zu RGB-Tupel

    Args:
        color_name: Name der Farbe aus COLORS

    Returns:
        RGB-Tupel (r, g, b)
    """
    hex_color = COLORS.get(color_name, '#000000')
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def get_scan_typ_name(typ_id: int) -> str:
    """
    Gibt den Namen eines Scan-Typs zurück

    Args:
        typ_id: ID des Scan-Typs

    Returns:
        Name des Scan-Typs
    """
    scan_types = {
        SCAN_TYP_WARENEINGANG: "Wareneingang",
        SCAN_TYP_RAHMENSPANNEN: "Rahmenspannen",
        SCAN_TYP_STICKEN: "Sticken",
        SCAN_TYP_VERSAEUBERN: "Versäubern",
        SCAN_TYP_QUALITAETSKONTROLLE: "Qualitätskontrolle",
        SCAN_TYP_WARENAUSGANG: "Warenausgang",
    }
    return scan_types.get(typ_id, "Unbekannt")


# Test
if __name__ == "__main__":
    print(f"🏷️ {APP_NAME} v{APP_VERSION}")
    print("=" * 50)

    print("\n🎨 Farben:")
    for name, color in COLORS.items():
        rgb = get_color_rgb(name)
        print(f"  {name}: {color} -> RGB{rgb}")

    print("\n📋 Scan-Typen:")
    for i in range(1, 7):
        print(f"  {i}: {get_scan_typ_name(i)}")

    print("\n✅ Konstanten erfolgreich geladen")