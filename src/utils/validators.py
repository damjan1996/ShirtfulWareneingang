#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validierungs-Funktionen
=======================

Sammlung von Funktionen zur Eingabe-Validierung.
"""

import re
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


def validate_tag_id(tag_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validiert eine RFID-Tag-ID

    Args:
        tag_id: Die zu validierende Tag-ID

    Returns:
        Tuple (is_valid, error_message)
    """
    if not tag_id:
        return False, "Tag-ID darf nicht leer sein"

    # Whitespace entfernen
    tag_id = tag_id.strip()

    # Länge prüfen (typisch 8-12 Hex-Zeichen)
    if len(tag_id) < 8:
        return False, "Tag-ID ist zu kurz (min. 8 Zeichen)"

    if len(tag_id) > 20:
        return False, "Tag-ID ist zu lang (max. 20 Zeichen)"

    # Hex-Format prüfen
    if not re.match(r'^[0-9A-Fa-f]+$', tag_id):
        return False, "Tag-ID enthält ungültige Zeichen (nur 0-9, A-F erlaubt)"

    return True, None


def validate_qr_data(qr_data: Dict[str, Any]) -> Tuple[bool, list]:
    """
    Validiert gescannte QR-Code-Daten

    Args:
        qr_data: Die zu validierenden QR-Daten

    Returns:
        Tuple (is_valid, list_of_errors)
    """
    errors = []

    # Pflichtfelder prüfen
    if not qr_data.get('raw_data'):
        errors.append("Keine Rohdaten vorhanden")

    # Auftragsnummer validieren
    auftrags_nr = qr_data.get('auftrags_nr', '').strip()
    if auftrags_nr:
        # Format prüfen (z.B. XX-XXXXXXX)
        if not re.match(r'^[A-Z]{2}-\d{5,}$', auftrags_nr):
            errors.append(f"Ungültiges Auftragsnummer-Format: {auftrags_nr}")

    # Paketnummer validieren
    paket_nr = qr_data.get('paket_nr', '').strip()
    if paket_nr:
        # Nur Zahlen erlaubt, 10-20 Stellen
        if not re.match(r'^\d{10,20}$', paket_nr):
            errors.append(f"Ungültiges Paketnummer-Format: {paket_nr}")

    # Mindestens eine Nummer sollte vorhanden sein
    if not auftrags_nr and not paket_nr:
        errors.append("Weder Auftrags- noch Paketnummer gefunden")

    return len(errors) == 0, errors


def validate_user_input(
        input_value: str,
        input_type: str = 'text',
        min_length: int = 0,
        max_length: int = 255,
        required: bool = False,
        pattern: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validiert Benutzereingaben

    Args:
        input_value: Der zu validierende Wert
        input_type: Typ der Eingabe (text, number, email, etc.)
        min_length: Minimale Länge
        max_length: Maximale Länge
        required: Pflichtfeld
        pattern: Regex-Pattern für Validierung

    Returns:
        Tuple (is_valid, error_message)
    """
    # Whitespace entfernen
    value = input_value.strip() if input_value else ''

    # Pflichtfeld prüfen
    if required and not value:
        return False, "Dies ist ein Pflichtfeld"

    # Wenn nicht required und leer, ist es valid
    if not required and not value:
        return True, None

    # Länge prüfen
    if len(value) < min_length:
        return False, f"Mindestens {min_length} Zeichen erforderlich"

    if len(value) > max_length:
        return False, f"Maximal {max_length} Zeichen erlaubt"

    # Typ-spezifische Validierung
    if input_type == 'number':
        if not value.isdigit():
            return False, "Nur Zahlen erlaubt"

    elif input_type == 'email':
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            return False, "Ungültige E-Mail-Adresse"

    elif input_type == 'username':
        # Nur Buchstaben, Zahlen, Unterstrich, Bindestrich
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            return False, "Nur Buchstaben, Zahlen, _ und - erlaubt"

    elif input_type == 'name':
        # Buchstaben, Leerzeichen, Bindestriche, Apostrophe
        if not re.match(r"^[a-zA-ZäöüÄÖÜß\s'-]+$", value):
            return False, "Ungültige Zeichen im Namen"

    # Custom Pattern prüfen
    if pattern:
        if not re.match(pattern, value):
            return False, "Eingabe entspricht nicht dem erforderlichen Format"

    return True, None


def validate_database_connection(connection) -> Tuple[bool, Optional[str]]:
    """
    Validiert eine Datenbank-Verbindung

    Args:
        connection: Die zu validierende Verbindung

    Returns:
        Tuple (is_valid, error_message)
    """
    if connection is None:
        return False, "Keine Verbindung vorhanden"

    try:
        # Verbindung testen
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return True, None
    except Exception as e:
        return False, f"Verbindungsfehler: {str(e)}"


def validate_date_range(
        start_date,
        end_date,
        max_days: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validiert einen Datumsbereich

    Args:
        start_date: Startdatum
        end_date: Enddatum
        max_days: Maximale Anzahl Tage

    Returns:
        Tuple (is_valid, error_message)
    """
    if not start_date or not end_date:
        return False, "Start- und Enddatum erforderlich"

    if start_date > end_date:
        return False, "Startdatum muss vor Enddatum liegen"

    if max_days:
        delta = (end_date - start_date).days
        if delta > max_days:
            return False, f"Maximaler Zeitraum: {max_days} Tage"

    return True, None


def sanitize_input(input_value: str, allow_html: bool = False) -> str:
    """
    Bereinigt Benutzereingaben von potenziell gefährlichen Inhalten

    Args:
        input_value: Der zu bereinigende Wert
        allow_html: HTML-Tags erlauben

    Returns:
        Bereinigter String
    """
    if not input_value:
        return ''

    # Whitespace normalisieren
    value = ' '.join(input_value.split())

    if not allow_html:
        # HTML-Tags entfernen
        value = re.sub(r'<[^>]+>', '', value)

        # HTML-Entities ersetzen
        replacements = {
            '&lt;': '<',
            '&gt;': '>',
            '&amp;': '&',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }

        for entity, char in replacements.items():
            value = value.replace(entity, char)

    # SQL-Injection-Zeichen escapen (Basic)
    # Hinweis: Verwenden Sie immer parametrisierte Queries!
    value = value.replace("'", "''")

    return value


def validate_file_upload(
        filename: str,
        allowed_extensions: list = None,
        max_size_mb: float = 10.0
) -> Tuple[bool, Optional[str]]:
    """
    Validiert einen Datei-Upload

    Args:
        filename: Dateiname
        allowed_extensions: Erlaubte Dateierweiterungen
        max_size_mb: Maximale Dateigröße in MB

    Returns:
        Tuple (is_valid, error_message)
    """
    if not filename:
        return False, "Kein Dateiname angegeben"

    # Dateierweiterung prüfen
    if allowed_extensions:
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        if ext not in allowed_extensions:
            return False, f"Dateityp nicht erlaubt. Erlaubt: {', '.join(allowed_extensions)}"

    # Gefährliche Dateitypen blockieren
    dangerous_extensions = ['exe', 'bat', 'cmd', 'com', 'scr', 'vbs', 'js']
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    if ext in dangerous_extensions:
        return False, "Dieser Dateityp ist aus Sicherheitsgründen nicht erlaubt"

    return True, None


# Test-Funktion
if __name__ == "__main__":
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("✅ Validator Test")
    print("=" * 50)

    # Tag-ID Validierung
    print("\n🏷️ Tag-ID Validierung:")
    test_tags = [
        "53004ECD68",  # Valid
        "ABC",  # Zu kurz
        "GHIJKLMNOP",  # Ungültige Zeichen
        "12345678901234567890123456"  # Zu lang
    ]

    for tag in test_tags:
        valid, error = validate_tag_id(tag)
        print(f"  '{tag}': {'✓' if valid else '✗'} {error or 'OK'}")

    # QR-Daten Validierung
    print("\n📊 QR-Daten Validierung:")
    test_qr_data = [
        {
            'raw_data': 'test',
            'auftrags_nr': 'NL-123456',
            'paket_nr': '1234567890'
        },
        {
            'raw_data': 'test',
            'auftrags_nr': 'INVALID',
            'paket_nr': '123'
        },
        {
            'raw_data': 'test'
        }
    ]

    for i, data in enumerate(test_qr_data, 1):
        valid, errors = validate_qr_data(data)
        print(f"  Test {i}: {'✓' if valid else '✗'}")
        if errors:
            for error in errors:
                print(f"    - {error}")

    # Benutzereingabe Validierung
    print("\n👤 Benutzereingabe Validierung:")
    test_inputs = [
        ("test@example.com", "email", True),
        ("invalid.email", "email", False),
        ("user_123", "username", True),
        ("user@123", "username", False),
        ("123456", "number", True),
        ("abc123", "number", False),
    ]

    for value, input_type, expected in test_inputs:
        valid, error = validate_user_input(value, input_type, required=True)
        status = '✓' if valid == expected else '✗'
        print(f"  {input_type} '{value}': {status} {error or 'OK'}")

    # Sanitization
    print("\n🧹 Input Sanitization:")
    test_sanitize = [
        "<script>alert('XSS')</script>",
        "Normal text with   spaces",
        "SQL ' injection ' test"
    ]

    for input_str in test_sanitize:
        sanitized = sanitize_input(input_str)
        print(f"  Original: '{input_str}'")
        print(f"  Sanitized: '{sanitized}'")

    print("\n✅ Validator Test abgeschlossen")