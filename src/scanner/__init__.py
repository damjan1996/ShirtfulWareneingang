#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR-Code Scanner Module für die Wareneingang-Anwendung
=====================================================

Dieses Modul stellt die Funktionalität für das Scannen und
Dekodieren von QR-Codes auf Versandetiketten bereit.

Hauptkomponenten:
- QRScanner: Hauptklasse für QR-Code-Scanning
- CameraHandler: Verwaltung der Kamera-Hardware
- QRDecoder: Dekodierung und Parsing der QR-Code-Daten
"""

from .qr_scanner import QRScanner
from .camera_handler import CameraHandler
from .decoder import QRDecoder

__all__ = ['QRScanner', 'CameraHandler', 'QRDecoder']

# Version des Scanner-Moduls
__version__ = '1.0.0'