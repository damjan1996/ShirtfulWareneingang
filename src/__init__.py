#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wareneingang Scanner Anwendung - Hauptpaket

Dieses Paket enthält alle Module für die Wareneingang-Anwendung:
- GUI: Benutzeroberfläche mit Tkinter
- RFID: RFID-Reader Integration (HID-Modus)
- Scanner: QR-Code Scanner Funktionalität
- Database: Datenbankanbindung an MSSQL
- Models: Datenmodelle
- Utils: Hilfsfunktionen

Autor: Shirtful GmbH
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Shirtful GmbH"
__email__ = "it@shirtful.com"

# Paket-Imports für einfacheren Zugriff
from src.database.connection import DatabaseConnection
from src.rfid.reader import RFIDReader
from src.scanner.qr_scanner import QRScanner

# Logging-Konfiguration
import logging
import os

# Log-Verzeichnis erstellen
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Standard-Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'wareneingang.log')),
        logging.StreamHandler()
    ]
)

# Logger für dieses Modul
logger = logging.getLogger(__name__)
logger.info(f"Wareneingang Scanner v{__version__} initialisiert")