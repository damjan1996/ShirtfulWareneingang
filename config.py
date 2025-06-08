#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale Konfiguration
Lädt Einstellungen aus .env
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

# Anwendungs-Konfiguration
APP_CONFIG = {
    'DEBUG': os.getenv('APP_DEBUG', 'False').lower() == 'true',
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'CAMERA_INDEX': int(os.getenv('CAMERA_INDEX', '0'))
}

# Pfade
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
CONFIG_DIR = os.path.join(BASE_DIR, 'config')

# Dateien
AUTHORIZED_TAGS_FILE = os.path.join(CONFIG_DIR, 'authorized_tags.json')

# Sicherstellen dass Verzeichnisse existieren
for directory in [LOG_DIR, CONFIG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)