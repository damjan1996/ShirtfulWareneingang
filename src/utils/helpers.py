#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hilfsfunktionen und Utilities
==============================

Allgemeine Hilfsfunktionen für die Wareneingang-Anwendung.
"""

import os
import sys
import json
import hashlib
import platform
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union


def get_app_data_dir() -> str:
    """
    Gibt das Anwendungsdaten-Verzeichnis zurück

    Returns:
        Pfad zum App-Data-Verzeichnis
    """
    if platform.system() == "Windows":
        app_data = os.environ.get('APPDATA', '')
        if app_data:
            return os.path.join(app_data, 'Shirtful', 'Wareneingang')

    # Fallback: Relatives Verzeichnis
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')


def ensure_directory(path: str) -> bool:
    """
    Stellt sicher, dass ein Verzeichnis existiert

    Args:
        path: Verzeichnispfad

    Returns:
        True wenn erfolgreich
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Fehler beim Erstellen des Verzeichnisses {path}: {e}")
        return False


def get_timestamp(format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Gibt einen formatierten Zeitstempel zurück

    Args:
        format_string: Datumsformat

    Returns:
        Formatierter Zeitstempel
    """
    return datetime.now().strftime(format_string)


def get_date_int() -> int:
    """
    Gibt das aktuelle Datum als Integer zurück (Format: YYYYMMDDHHMMSS)

    Returns:
        Datum als Integer
    """
    return int(datetime.now().strftime("%Y%m%d%H%M%S"))


def format_file_size(size_bytes: int) -> str:
    """
    Formatiert eine Dateigröße in lesbarer Form

    Args:
        size_bytes: Größe in Bytes

    Returns:
        Formatierte Größe (z.B. "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """
    Erstellt einen Hash von einem String

    Args:
        text: Zu hashender Text
        algorithm: Hash-Algorithmus

    Returns:
        Hash als Hex-String
    """
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode('utf-8'))
    return hasher.hexdigest()


def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Lädt eine JSON-Datei

    Args:
        filepath: Pfad zur JSON-Datei

    Returns:
        Dict mit JSON-Daten oder None bei Fehler
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden von {filepath}: {e}")
        return None


def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """
    Speichert Daten als JSON-Datei

    Args:
        data: Zu speichernde Daten
        filepath: Zielpfad

    Returns:
        True wenn erfolgreich
    """
    try:
        ensure_directory(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Fehler beim Speichern von {filepath}: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """
    Bereinigt einen Dateinamen von ungültigen Zeichen

    Args:
        filename: Original-Dateiname

    Returns:
        Bereinigter Dateiname
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def parse_rfid_tag(tag: str) -> Optional[int]:
    """
    Konvertiert einen RFID-Tag von Hex zu Decimal

    Args:
        tag: RFID-Tag als Hex-String

    Returns:
        Tag als Decimal-Integer oder None bei Fehler
    """
    try:
        # Entferne Leerzeichen und konvertiere zu Großbuchstaben
        tag = tag.strip().upper()
        # Konvertiere von Hex zu Decimal
        return int(tag, 16)
    except (ValueError, TypeError):
        return None


def format_rfid_tag(tag_decimal: Union[int, str]) -> str:
    """
    Formatiert einen RFID-Tag von Decimal zu Hex

    Args:
        tag_decimal: Tag als Decimal-Wert

    Returns:
        Tag als Hex-String
    """
    try:
        if isinstance(tag_decimal, str):
            tag_decimal = int(tag_decimal)
        return format(tag_decimal, 'X')
    except (ValueError, TypeError):
        return ""


def is_valid_auftrags_nr(auftrags_nr: str) -> bool:
    """
    Prüft, ob eine Auftragsnummer gültig ist

    Args:
        auftrags_nr: Auftragsnummer

    Returns:
        True wenn gültig
    """
    if not auftrags_nr:
        return False

    # Muster: XX-XXXXXXX (z.B. NL-2581949)
    import re
    pattern = r'^[A-Z]{2}-\d+$'
    return bool(re.match(pattern, auftrags_nr))


def is_valid_paket_nr(paket_nr: str) -> bool:
    """
    Prüft, ob eine Paketnummer gültig ist

    Args:
        paket_nr: Paketnummer

    Returns:
        True wenn gültig
    """
    if not paket_nr:
        return False

    # Paketnummer sollte mindestens 10 Ziffern haben
    return paket_nr.isdigit() and len(paket_nr) >= 10


def calculate_time_difference(start: datetime, end: datetime) -> str:
    """
    Berechnet die Zeitdifferenz zwischen zwei Zeitpunkten

    Args:
        start: Startzeit
        end: Endzeit

    Returns:
        Formatierte Zeitdifferenz (z.B. "2h 15m")
    """
    diff = end - start
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def get_work_hours_today(clock_in: datetime, clock_out: Optional[datetime] = None) -> float:
    """
    Berechnet die Arbeitsstunden für heute

    Args:
        clock_in: Einschaltzeit
        clock_out: Ausschaltzeit (oder aktuelle Zeit)

    Returns:
        Arbeitsstunden als Float
    """
    if clock_out is None:
        clock_out = datetime.now()

    diff = clock_out - clock_in
    return diff.total_seconds() / 3600  # Stunden


def should_take_break(work_start: datetime) -> bool:
    """
    Prüft, ob eine Pause gemacht werden sollte

    Args:
        work_start: Arbeitsbeginn

    Returns:
        True wenn mehr als 6 Stunden gearbeitet
    """
    hours_worked = get_work_hours_today(work_start)
    return hours_worked >= 6.0


def get_greeting(name: str = "") -> str:
    """
    Gibt eine zeitabhängige Begrüßung zurück

    Args:
        name: Name der Person

    Returns:
        Begrüßungstext
    """
    hour = datetime.now().hour

    if hour < 12:
        greeting = "Guten Morgen"
    elif hour < 17:
        greeting = "Guten Tag"
    else:
        greeting = "Guten Abend"

    if name:
        return f"{greeting}, {name}!"
    return f"{greeting}!"


def get_system_info() -> Dict[str, str]:
    """
    Gibt System-Informationen zurück

    Returns:
        Dict mit System-Infos
    """
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node(),
    }


def create_backup_filename(base_name: str, extension: str = "bak") -> str:
    """
    Erstellt einen Backup-Dateinamen mit Zeitstempel

    Args:
        base_name: Basis-Dateiname
        extension: Dateierweiterung

    Returns:
        Backup-Dateiname
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"


def is_business_hours() -> bool:
    """
    Prüft, ob aktuelle Zeit innerhalb der Geschäftszeiten ist

    Returns:
        True wenn Geschäftszeiten
    """
    now = datetime.now()
    weekday = now.weekday()  # 0 = Montag, 6 = Sonntag
    hour = now.hour

    # Montag bis Freitag, 7:00 - 18:00 Uhr
    if weekday < 5 and 7 <= hour < 18:
        return True

    # Samstag, 8:00 - 13:00 Uhr
    if weekday == 5 and 8 <= hour < 13:
        return True

    return False


# Test-Funktionen
if __name__ == "__main__":
    print("🧪 Helpers Test")
    print("=" * 50)

    # App-Data-Verzeichnis
    print(f"App-Data-Dir: {get_app_data_dir()}")

    # Zeitstempel
    print(f"Timestamp: {get_timestamp()}")
    print(f"Date-Int: {get_date_int()}")

    # Dateigrößen
    print(f"1024 Bytes: {format_file_size(1024)}")
    print(f"1048576 Bytes: {format_file_size(1048576)}")

    # RFID-Tags
    test_tag = "53004ECD68"
    decimal = parse_rfid_tag(test_tag)
    print(f"RFID Hex->Dec: {test_tag} -> {decimal}")
    print(f"RFID Dec->Hex: {decimal} -> {format_rfid_tag(decimal)}")

    # Validierung
    print(f"Gültige Auftragsnr 'NL-123456': {is_valid_auftrags_nr('NL-123456')}")
    print(f"Ungültige Auftragsnr '123456': {is_valid_auftrags_nr('123456')}")

    # Begrüßung
    print(f"Begrüßung: {get_greeting('Test User')}")

    # System-Info
    print("\nSystem-Info:")
    for key, value in get_system_info().items():
        print(f"  {key}: {value}")

    print("\n✅ Helpers Test abgeschlossen")