#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validierungsfunktionen
"""

import json
import re


def validate_tag_id(tag_id):
    """Validiert RFID Tag ID (Hex String)"""
    if not tag_id:
        return False

    # Entferne Whitespace
    tag_id = tag_id.strip()

    # Prüfe ob gültiger Hex-String (typisch 10 Zeichen)
    if not re.match(r'^[0-9A-Fa-f]{8,12}$', tag_id):
        return False

    try:
        # Prüfe ob konvertierbar zu Integer
        int(tag_id, 16)
        return True
    except ValueError:
        return False


def validate_qr_payload(payload):
    """Validiert QR-Code Payload"""
    if not payload or not isinstance(payload, str):
        return None

    payload = payload.strip()

    # Versuche JSON zu parsen
    try:
        data = json.loads(payload)
        return {'type': 'json', 'data': data}
    except json.JSONDecodeError:
        pass

    # Prüfe auf Key-Value Format (z.B. "Kunde:ABC^Auftrag:123")
    if '^' in payload and ':' in payload:
        try:
            pairs = payload.split('^')
            data = {}
            for pair in pairs:
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    data[key.strip()] = value.strip()
            if data:
                return {'type': 'keyvalue', 'data': data}
        except:
            pass

    # Fallback: Roh-Text
    return {'type': 'text', 'data': payload}


def format_duration(seconds):
    """Formatiert Dauer in lesbares Format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"