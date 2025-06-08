#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils Package für RFID & QR Scanner
Kombiniert alle Hilfsfunktionen - finale optimierte Version
"""

# Import aus Untermodulen
try:
    from .logger import setup_logger, get_logger
    from .validators import validate_tag_id, format_duration
except ImportError:
    # Fallback falls Module nicht existieren
    pass

# Zusätzliche Hilfsfunktionen direkt hier
import os
import json
import logging
from datetime import datetime


def setup_logger(name='RFIDScanner', log_level='INFO'):
    """Setup für Logger mit Console und File Output"""
    logger = logging.getLogger(name)

    # Verhindere doppelte Handler
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level.upper()))

    # Console Handler
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File Handler (optional)
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warnung: Konnte Log-Datei nicht erstellen: {e}")

    return logger


def get_logger(name='RFIDScanner'):
    """Logger abrufen oder erstellen"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


def validate_tag_id(tag_id):
    """Validiert RFID Tag ID (Hex String) - verbesserte Version"""
    if not tag_id:
        return False

    # Entferne Whitespace und mache uppercase
    tag_id = tag_id.strip().upper()

    # Prüfe Länge (typisch 8-12 Zeichen für RFID Tags)
    if len(tag_id) < 8 or len(tag_id) > 12:
        return False

    # Prüfe ob gültiger Hex-String
    try:
        # Alle Zeichen müssen Hex sein
        for char in tag_id:
            if char not in '0123456789ABCDEF':
                return False

        # Prüfe ob konvertierbar zu Integer
        decimal_value = int(tag_id, 16)

        # Prüfe sinnvolle Grenzen (nicht 0, nicht zu groß)
        if decimal_value == 0 or decimal_value > 0xFFFFFFFFFFFF:
            return False

        return True

    except ValueError:
        return False


def validate_qr_payload(payload):
    """Validiert und parsed QR-Code Payload (sehr tolerante Version)"""
    if not payload or not isinstance(payload, str):
        return {'type': 'invalid', 'data': None, 'valid': False}

    payload = payload.strip()

    if not payload:
        return {'type': 'invalid', 'data': None, 'valid': False}

    # Alle QR-Codes mit mehr als 1 Zeichen sind erst mal gültig (sehr tolerant)
    if len(payload) < 1:
        return {'type': 'invalid', 'data': payload, 'valid': False}

    # 1. Versuche JSON zu parsen
    try:
        data = json.loads(payload)
        return {
            'type': 'json',
            'data': data,
            'valid': True,
            'formatted': json.dumps(data, indent=2, ensure_ascii=False)
        }
    except json.JSONDecodeError:
        pass

    # 2. Prüfe auf Key-Value Format oder delimited Format
    if '^' in payload:
        try:
            parts = payload.split('^')

            # Wenn es : enthält, dann Key:Value Format
            if ':' in payload:
                data = {}
                for part in parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        data[key.strip()] = value.strip()

                if data:
                    formatted = '\n'.join([f"{k}: {v}" for k, v in data.items()])
                    return {
                        'type': 'keyvalue',
                        'data': data,
                        'valid': True,
                        'formatted': formatted
                    }
            else:
                # Einfaches Format mit ^ als Trenner (wie "1^126644896^25000580^...")
                data = {f'field_{i + 1}': part.strip() for i, part in enumerate(parts) if part.strip()}
                formatted = ' | '.join([part.strip() for part in parts if part.strip()])
                return {
                    'type': 'delimited',
                    'data': data,
                    'valid': True,
                    'formatted': formatted
                }
        except Exception:
            pass

    # 3. Alle anderen Texte sind auch gültig (sehr tolerant für Wareneingang)
    if len(payload) <= 5000:  # Maximallänge großzügig
        return {
            'type': 'text',
            'data': payload,
            'valid': True,
            'formatted': payload
        }

    # 4. Nur bei extrem langen Payloads als ungültig markieren
    return {'type': 'toolong', 'data': payload, 'valid': False}


def format_duration(seconds):
    """Formatiert Dauer in lesbares Format (HH:MM:SS oder MM:SS)"""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "00:00"

    seconds = int(seconds)

    if seconds < 3600:  # Unter einer Stunde
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    else:  # Über einer Stunde
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_duration_verbose(seconds):
    """Formatiert Dauer in ausführliches deutsches Format"""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "0 Sekunden"

    seconds = int(seconds)

    if seconds < 60:
        return f"{seconds} Sekunde{'n' if seconds != 1 else ''}"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        if secs == 0:
            return f"{minutes} Minute{'n' if minutes != 1 else ''}"
        else:
            return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes == 0:
            return f"{hours} Stunde{'n' if hours != 1 else ''}"
        else:
            return f"{hours}h {minutes}m"


def hex_to_decimal(hex_string):
    """Konvertiert Hex-String zu Decimal"""
    try:
        if isinstance(hex_string, str):
            hex_string = hex_string.strip().upper()
            return int(hex_string, 16)
        return int(hex_string)
    except (ValueError, TypeError):
        return None


def decimal_to_hex(decimal_value):
    """Konvertiert Decimal zu Hex-String"""
    try:
        return f"{int(decimal_value):X}"
    except (ValueError, TypeError):
        return None


def safe_execute(func, *args, **kwargs):
    """Sichere Ausführung einer Funktion mit Logging"""
    logger = get_logger()
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Fehler bei {func.__name__}: {e}")
        return None


def create_directories():
    """Erstellt notwendige Verzeichnisse"""
    directories = ['logs', 'config', 'temp']
    created = []

    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                created.append(directory)
            except Exception as e:
                print(f"❌ Fehler beim Erstellen von {directory}: {e}")

    if created:
        logger = get_logger()
        logger.info(f"Verzeichnisse erstellt: {', '.join(created)}")

    return created


def get_system_info():
    """Gibt System-Informationen zurück"""
    import platform
    import sys

    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'python_version': sys.version,
        'python_executable': sys.executable,
        'working_directory': os.getcwd()
    }


def format_file_size(size_bytes):
    """Formatiert Dateigröße in lesbares Format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def cleanup_old_logs(log_dir='logs', days_to_keep=30):
    """Löscht alte Log-Dateien"""
    if not os.path.exists(log_dir):
        return 0

    import time
    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
    deleted_count = 0

    try:
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(log_dir, filename)
                if os.path.getmtime(filepath) < cutoff_time:
                    os.remove(filepath)
                    deleted_count += 1
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Fehler beim Log-Cleanup: {e}")

    return deleted_count


# Alle exportierten Funktionen
__all__ = [
    'setup_logger',
    'get_logger',
    'validate_tag_id',
    'validate_qr_payload',
    'format_duration',
    'format_duration_verbose',
    'hex_to_decimal',
    'decimal_to_hex',
    'safe_execute',
    'create_directories',
    'get_system_info',
    'format_file_size',
    'cleanup_old_logs'
]

# Setup beim Import
_main_logger = setup_logger('MainApp', 'INFO')
_main_logger.debug("Utils Package initialisiert")

# Erstelle notwendige Verzeichnisse beim Import
create_directories()