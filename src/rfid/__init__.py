#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RFID Module für die Wareneingang-Anwendung
==========================================

Dieses Modul stellt die Funktionalität für die RFID-Tag-Erkennung bereit.
Es arbeitet mit dem TSHRW380BZMP Reader im HID-Modus.

Hauptkomponenten:
- RFIDReader: Hauptklasse für die RFID-Kommunikation
- HIDListener: Keyboard-Event-Listener für HID-Modus
- TagValidator: Validierung der Tags gegen die Datenbank
"""

from .reader import RFIDReader
from .hid_listener import HIDListener
from .tag_validator import TagValidator

__all__ = ['RFIDReader', 'HIDListener', 'TagValidator']

# Version des RFID-Moduls
__version__ = '1.0.0'