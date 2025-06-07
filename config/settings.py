#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Allgemeine Einstellungen für die Wareneingang-Anwendung
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# ==============================================================================
# Projekt-Pfade
# ==============================================================================

# Basis-Verzeichnis (Projektroot)
BASE_DIR = Path(__file__).resolve().parent.parent

# Unterverzeichnisse
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
SOUNDS_DIR = ASSETS_DIR / "sounds"
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"
CONFIG_DIR = BASE_DIR / "config"

# Stelle sicher, dass wichtige Verzeichnisse existieren
for directory in [LOGS_DIR, TEMP_DIR, ASSETS_DIR, IMAGES_DIR, SOUNDS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# Anwendungs-Metadaten
# ==============================================================================

APP_NAME = "Wareneingang Scanner"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Shirtful GmbH"
APP_DESCRIPTION = "RFID-basierte Wareneingangs-Verwaltung mit QR-Code Scanner"

# ==============================================================================
# Hardware-Einstellungen
# ==============================================================================

# RFID Reader Einstellungen
RFID_SETTINGS = {
    "mode": "HID",  # HID (Keyboard Wedge) Modus
    "encoding": "utf-8",
    "enter_key_suffix": True,  # Reader sendet Enter nach Tag
    "read_timeout": 10,  # Sekunden
    "buffer_clear_time": 0.5,  # Sekunden
    "min_tag_length": 8,
    "max_tag_length": 12,
    "allowed_characters": "0123456789ABCDEFabcdef",
    "case_sensitive": False,  # Tags in Großbuchstaben konvertieren
}

# Kamera-Einstellungen für QR-Scanner
CAMERA_SETTINGS = {
    "default_index": 0,
    "resolution": (640, 480),
    "fps": 30,
    "buffer_size": 1,
    "auto_exposure": True,
    "brightness": 0,  # -64 bis 64
    "contrast": 32,  # 0 bis 64
    "scan_interval": 100,  # Millisekunden zwischen Scans
    "detection_cooldown": 1000,  # Millisekunden nach erfolgreicher Erkennung
}

# ==============================================================================
# GUI-Einstellungen
# ==============================================================================

GUI_SETTINGS = {
    # Fenster
    "window": {
        "title": f"{APP_NAME} v{APP_VERSION}",
        "min_width": 1024,
        "min_height": 768,
        "default_width": 1280,
        "default_height": 800,
        "resizable": True,
        "fullscreen_available": True,
        "always_on_top": False,
        "icon": str(IMAGES_DIR / "app_icon.ico"),
    },

    # Theme
    "theme": {
        "mode": "light",  # "light" oder "dark"
        "primary_color": "#2196F3",
        "secondary_color": "#FF9800",
        "font_family": "Segoe UI",
        "font_size_base": 12,
        "border_radius": 4,
        "padding_base": 10,
    },

    # Animationen
    "animations": {
        "enabled": True,
        "duration": 200,  # Millisekunden
        "easing": "ease-in-out",
    },

    # Touch-Optimierung
    "touch": {
        "enabled": True,
        "min_button_height": 60,
        "min_button_width": 120,
        "tap_delay": 300,  # Millisekunden
    }
}

# ==============================================================================
# Benutzer-Einstellungen
# ==============================================================================

USER_SETTINGS = {
    "session": {
        "timeout_minutes": 480,  # 8 Stunden
        "idle_timeout_minutes": 30,
        "warning_before_timeout": 5,  # Minuten
        "auto_logout_enabled": True,
    },

    "multi_user": {
        "enabled": True,
        "max_concurrent_users": 10,
        "show_user_tabs": True,
        "allow_user_switching": True,
    },

    "time_tracking": {
        "enabled": True,
        "auto_clock_in": True,
        "auto_clock_out": True,
        "break_reminder": True,
        "break_after_hours": 6,
        "break_duration_minutes": 30,
    }
}

# ==============================================================================
# Scanner-Einstellungen
# ==============================================================================

SCANNER_SETTINGS = {
    "qr_code": {
        "formats": ["QR_CODE", "CODE128", "CODE39", "EAN13", "EAN8"],
        "error_correction": "L",  # L, M, Q, H
        "min_confidence": 0.7,
        "duplicate_timeout": 2000,  # Millisekunden
        "beep_on_scan": True,
        "vibrate_on_scan": False,  # Für mobile Geräte
    },

    "data_parsing": {
        "delimiter": "^",  # Für delimited Format
        "encoding": "utf-8",
        "strip_whitespace": True,
        "validate_checksum": True,
    },

    "validation": {
        "order_number_pattern": r"^[A-Z]{2}-\d+$",
        "package_number_pattern": r"^\d{10,18}$",
        "require_all_fields": False,
    }
}

# ==============================================================================
# Audio-Einstellungen
# ==============================================================================

AUDIO_SETTINGS = {
    "enabled": True,
    "volume": 0.7,  # 0.0 - 1.0
    "sounds": {
        "login_success": "login_success.wav",
        "login_error": "login_error.wav",
        "scan_success": "scan_success.wav",
        "scan_error": "scan_error.wav",
        "warning": "warning.wav",
        "logout": "logout.wav",
    },
    "voice_feedback": {
        "enabled": False,
        "language": "de-DE",
        "rate": 1.0,
        "pitch": 1.0,
    }
}

# ==============================================================================
# Logging-Einstellungen
# ==============================================================================

LOGGING_SETTINGS = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "file": {
        "enabled": True,
        "filename": "wareneingang.log",
        "max_size": 10 * 1024 * 1024,  # 10 MB
        "backup_count": 5,
        "encoding": "utf-8",
    },
    "console": {
        "enabled": True,
        "colorized": True,
    },
    "database": {
        "enabled": False,  # Log in Datenbank schreiben
        "table": "SystemLogs",
        "batch_size": 100,
        "flush_interval": 60,  # Sekunden
    }
}

# ==============================================================================
# Sicherheits-Einstellungen
# ==============================================================================

SECURITY_SETTINGS = {
    "rfid": {
        "validate_checksum": True,
        "anti_collision": True,
        "encryption": False,  # Für verschlüsselte Tags
        "blacklist_check": True,
        "blacklist_file": str(CONFIG_DIR / "blacklist.txt"),
    },

    "database": {
        "encrypt_connection": True,
        "validate_ssl": False,  # Für selbst-signierte Zertifikate
        "connection_pool": True,
        "max_connections": 5,
    },

    "api": {
        "rate_limiting": True,
        "max_requests_per_minute": 60,
        "require_authentication": True,
    }
}

# ==============================================================================
# Performance-Einstellungen
# ==============================================================================

PERFORMANCE_SETTINGS = {
    "caching": {
        "enabled": True,
        "user_cache_size": 100,
        "scan_cache_size": 1000,
        "cache_ttl": 3600,  # Sekunden
    },

    "threading": {
        "worker_threads": 4,
        "queue_size": 1000,
        "thread_timeout": 30,  # Sekunden
    },

    "database": {
        "batch_insert": True,
        "batch_size": 100,
        "async_queries": True,
        "query_timeout": 30,  # Sekunden
    }
}

# ==============================================================================
# Lokalisierung
# ==============================================================================

LOCALIZATION_SETTINGS = {
    "default_language": "de",
    "available_languages": ["de", "en", "tr", "pl"],
    "auto_detect": False,
    "fallback_language": "en",
    "date_format": {
        "de": "%d.%m.%Y",
        "en": "%Y-%m-%d",
        "tr": "%d.%m.%Y",
        "pl": "%d.%m.%Y",
    },
    "time_format": {
        "de": "%H:%M:%S",
        "en": "%I:%M:%S %p",
        "tr": "%H:%M:%S",
        "pl": "%H:%M:%S",
    }
}

# ==============================================================================
# Update-Einstellungen
# ==============================================================================

UPDATE_SETTINGS = {
    "check_for_updates": True,
    "auto_update": False,
    "update_channel": "stable",  # "stable", "beta", "dev"
    "update_server": "https://updates.shirtful.com/wareneingang",
    "check_interval": 86400,  # 24 Stunden
}

# ==============================================================================
# Debug-Einstellungen
# ==============================================================================

DEBUG_SETTINGS = {
    "enabled": os.getenv("DEBUG", "False").lower() == "true",
    "show_fps": False,
    "show_memory_usage": False,
    "log_sql_queries": False,
    "mock_hardware": False,  # Für Tests ohne RFID/Kamera
    "test_mode": os.getenv("TESTING", "False").lower() == "true",
}

# ==============================================================================
# Umgebungsspezifische Überschreibungen
# ==============================================================================

# Lade lokale Einstellungen falls vorhanden
LOCAL_SETTINGS_FILE = CONFIG_DIR / "local_settings.py"
if LOCAL_SETTINGS_FILE.exists():
    import importlib.util

    spec = importlib.util.spec_from_file_location("local_settings", LOCAL_SETTINGS_FILE)
    local_settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(local_settings)

    # Überschreibe Einstellungen mit lokalen Werten
    for attr in dir(local_settings):
        if not attr.startswith("_"):
            globals()[attr] = getattr(local_settings, attr)


# ==============================================================================
# Hilfsfunktionen
# ==============================================================================

def get_setting(path: str, default: Any = None) -> Any:
    """
    Holt eine Einstellung über einen Punkt-separierten Pfad

    Args:
        path: Pfad zur Einstellung (z.B. "GUI_SETTINGS.window.title")
        default: Standardwert falls Einstellung nicht gefunden

    Returns:
        Wert der Einstellung oder default
    """
    parts = path.split(".")
    value = globals()

    try:
        for part in parts:
            if isinstance(value, dict):
                value = value[part]
            else:
                value = getattr(value, part)
        return value
    except (KeyError, AttributeError):
        return default


def update_setting(path: str, value: Any) -> bool:
    """
    Aktualisiert eine Einstellung zur Laufzeit

    Args:
        path: Pfad zur Einstellung
        value: Neuer Wert

    Returns:
        True bei Erfolg, False bei Fehler
    """
    parts = path.split(".")
    target = globals()

    try:
        for part in parts[:-1]:
            if isinstance(target, dict):
                target = target[part]
            else:
                target = getattr(target, part)

        if isinstance(target, dict):
            target[parts[-1]] = value
        else:
            setattr(target, parts[-1], value)
        return True
    except (KeyError, AttributeError):
        return False


# ==============================================================================
# Validierung
# ==============================================================================

def validate_settings() -> Dict[str, Any]:
    """
    Validiert alle Einstellungen und gibt Warnungen/Fehler zurück

    Returns:
        Dictionary mit "errors" und "warnings" Listen
    """
    errors = []
    warnings = []

    # Prüfe wichtige Verzeichnisse
    for dir_name, dir_path in [
        ("Logs", LOGS_DIR),
        ("Assets", ASSETS_DIR),
        ("Config", CONFIG_DIR),
    ]:
        if not dir_path.exists():
            errors.append(f"{dir_name} Verzeichnis existiert nicht: {dir_path}")

    # Prüfe Audio-Dateien wenn Audio aktiviert
    if AUDIO_SETTINGS["enabled"]:
        for sound_name, sound_file in AUDIO_SETTINGS["sounds"].items():
            sound_path = SOUNDS_DIR / sound_file
            if not sound_path.exists():
                warnings.append(f"Sound-Datei fehlt: {sound_path}")

    # Prüfe Kamera-Index
    if CAMERA_SETTINGS["default_index"] < 0:
        errors.append("Kamera-Index muss >= 0 sein")

    # Prüfe Performance-Einstellungen
    if PERFORMANCE_SETTINGS["threading"]["worker_threads"] < 1:
        errors.append("Mindestens 1 Worker-Thread erforderlich")

    return {
        "errors": errors,
        "warnings": warnings,
        "valid": len(errors) == 0
    }


# Führe Validierung beim Import aus
validation_result = validate_settings()
if not validation_result["valid"]:
    import logging

    logger = logging.getLogger(__name__)
    for error in validation_result["errors"]:
        logger.error(f"Einstellungs-Fehler: {error}")
    for warning in validation_result["warnings"]:
        logger.warning(f"Einstellungs-Warnung: {warning}")