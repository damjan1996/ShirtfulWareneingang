#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbank-Konfiguration für die Wareneingang-Anwendung
"""

import os
from typing import Dict, Any

# ==============================================================================
# Datenbank-Verbindungsparameter
# ==============================================================================

# Haupt-Datenbankverbindung
DATABASE_CONFIG = {
    "server": "116.202.224.248",
    "database": "RdScanner",
    "username": "sa",
    "password": "YJ5C19QZ7ZUW!",
    "port": 1433,
    "timeout": 30,  # Connection timeout in seconds
    "login_timeout": 10,  # Login timeout in seconds
}

# Backup-Server (falls vorhanden)
DATABASE_BACKUP_CONFIG = {
    "server": "",  # Backup-Server Adresse
    "database": "RdScanner",
    "username": "sa",
    "password": "",
    "port": 1433,
    "timeout": 30,
    "login_timeout": 10,
}

# ==============================================================================
# Connection String Templates
# ==============================================================================

# ODBC Driver Prioritäten (neueste zuerst)
ODBC_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "SQL Server"
]

# Connection String Template für verschiedene Driver
CONNECTION_STRING_TEMPLATES = {
    "ODBC Driver 18 for SQL Server": (
        "DRIVER={{{driver}}};"
        "SERVER={server},{port};"
        "DATABASE={database};"
        "UID={username};"
        "PWD={password};"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
        "Connection Timeout={timeout};"
        "LoginTimeout={login_timeout};"
    ),
    "ODBC Driver 17 for SQL Server": (
        "DRIVER={{{driver}}};"
        "SERVER={server},{port};"
        "DATABASE={database};"
        "UID={username};"
        "PWD={password};"
        "TrustServerCertificate=yes;"
        "Connection Timeout={timeout};"
        "LoginTimeout={login_timeout};"
    ),
    "SQL Server": (
        "DRIVER={{{driver}}};"
        "SERVER={server},{port};"
        "DATABASE={database};"
        "UID={username};"
        "PWD={password};"
        "Connection Timeout={timeout};"
        "LoginTimeout={login_timeout};"
    )
}

# ==============================================================================
# Connection Pool Settings
# ==============================================================================

POOL_CONFIG = {
    "min_size": 1,
    "max_size": 5,
    "timeout": 30,
    "idle_time": 300,  # 5 Minuten
    "retry_count": 3,
    "retry_delay": 1,  # Sekunden
}

# ==============================================================================
# Query Settings
# ==============================================================================

QUERY_CONFIG = {
    "command_timeout": 30,  # Sekunden
    "fetch_size": 1000,  # Anzahl Zeilen pro Fetch
    "enable_query_logging": True,
    "log_slow_queries": True,
    "slow_query_threshold": 5,  # Sekunden
}

# ==============================================================================
# Tabellen-Definitionen
# ==============================================================================

TABLE_DEFINITIONS = {
    "ScannBenutzer": {
        "schema": "dbo",
        "primary_key": "ID",
        "identity_column": "ID",
        "required_fields": ["BenutzerName", "EPC"],
        "indexes": ["EPC", "BenutzerName"],
    },
    "ScannKopf": {
        "schema": "dbo",
        "primary_key": "ID",
        "identity_column": "ID",
        "required_fields": ["EPC", "ScannTyp_ID"],
        "foreign_keys": {
            "ScannTyp_ID": "ScannTyp.ID"
        },
        "indexes": ["EPC", "TagesDatum", "ScannTyp_ID"],
    },
    "ScannPosition": {
        "schema": "dbo",
        "primary_key": "ID",
        "identity_column": "ID",
        "required_fields": ["ScannKopf_ID"],
        "foreign_keys": {
            "ScannKopf_ID": "ScannKopf.ID"
        },
        "indexes": ["ScannKopf_ID", "Auftragsnummer", "Paketnummer"],
    },
    "ScannTyp": {
        "schema": "dbo",
        "primary_key": "ID",
        "identity_column": "ID",
        "required_fields": ["Bezeichnung"],
        "indexes": ["Bezeichnung"],
    }
}

# ==============================================================================
# Stored Procedures und Functions
# ==============================================================================

STORED_PROCEDURES = {
    "sp_GetUserByEPC": {
        "parameters": ["@EPC"],
        "returns": "TABLE"
    },
    "sp_CreateScanSession": {
        "parameters": ["@EPC", "@ScannTyp_ID", "@Arbeitsplatz"],
        "returns": "INT"  # Returns ScannKopf.ID
    },
    "sp_AddScanPosition": {
        "parameters": ["@ScannKopf_ID", "@Kunde", "@Auftragsnummer", "@Paketnummer", "@Zusatzinfo"],
        "returns": "INT"  # Returns ScannPosition.ID
    }
}

# ==============================================================================
# Views
# ==============================================================================

VIEW_DEFINITIONS = {
    "vw_ActiveUsers": """
                      SELECT ID,
                             BenutzerName,
                             Vorname,
                             Nachname,
                             EPC,
                             Email
                      FROM dbo.ScannBenutzer
                      WHERE xStatus = 0
                      """,
    "vw_TodayScans": """
                     SELECT sk.ID,
                            sk.EPC,
                            sb.BenutzerName,
                            st.Bezeichnung as ScannTyp,
                            sk.Datum,
                            COUNT(sp.ID)   as AnzahlPositionen
                     FROM dbo.ScannKopf sk
                              INNER JOIN dbo.ScannBenutzer sb ON sk.EPC = sb.EPC
                              INNER JOIN dbo.ScannTyp st ON sk.ScannTyp_ID = st.ID
                              LEFT JOIN dbo.ScannPosition sp ON sk.ID = sp.ScannKopf_ID
                     WHERE sk.TagesDatum = CAST(GETDATE() AS DATE)
                     GROUP BY sk.ID, sk.EPC, sb.BenutzerName, st.Bezeichnung, sk.Datum
                     """
}


# ==============================================================================
# Datenbank-Funktionen
# ==============================================================================

def get_connection_string(driver: str = None, config: Dict[str, Any] = None) -> str:
    """
    Erstellt einen Connection String basierend auf dem angegebenen Driver

    Args:
        driver: ODBC Driver Name (optional)
        config: Datenbank-Konfiguration (optional, Standard: DATABASE_CONFIG)

    Returns:
        Connection String
    """
    if config is None:
        config = DATABASE_CONFIG

    if driver is None:
        # Verwende den ersten verfügbaren Driver
        driver = ODBC_DRIVERS[0]

    if driver not in CONNECTION_STRING_TEMPLATES:
        raise ValueError(f"Unbekannter Driver: {driver}")

    template = CONNECTION_STRING_TEMPLATES[driver]

    # Füge Driver zum Config hinzu
    config_with_driver = config.copy()
    config_with_driver["driver"] = driver

    return template.format(**config_with_driver)


def get_all_connection_strings(config: Dict[str, Any] = None) -> list:
    """
    Erstellt Connection Strings für alle verfügbaren Driver

    Args:
        config: Datenbank-Konfiguration (optional)

    Returns:
        Liste von Connection Strings
    """
    if config is None:
        config = DATABASE_CONFIG

    connection_strings = []

    for driver in ODBC_DRIVERS:
        try:
            conn_str = get_connection_string(driver, config)
            connection_strings.append(conn_str)
        except ValueError:
            continue

    return connection_strings


# ==============================================================================
# Umgebungsvariablen (falls vorhanden)
# ==============================================================================

# Überschreibe Konfiguration mit Umgebungsvariablen falls gesetzt
if os.getenv("DB_SERVER"):
    DATABASE_CONFIG["server"] = os.getenv("DB_SERVER")

if os.getenv("DB_DATABASE"):
    DATABASE_CONFIG["database"] = os.getenv("DB_DATABASE")

if os.getenv("DB_USERNAME"):
    DATABASE_CONFIG["username"] = os.getenv("DB_USERNAME")

if os.getenv("DB_PASSWORD"):
    DATABASE_CONFIG["password"] = os.getenv("DB_PASSWORD")

if os.getenv("DB_PORT"):
    DATABASE_CONFIG["port"] = int(os.getenv("DB_PORT"))

# ==============================================================================
# Test-Konfiguration
# ==============================================================================

TEST_DATABASE_CONFIG = {
    "server": "localhost",
    "database": "RdScanner_Test",
    "username": "sa",
    "password": "test_password",
    "port": 1433,
    "timeout": 10,
    "login_timeout": 5,
}

# Verwende Test-Datenbank im Test-Modus
if os.getenv("TESTING", "").lower() == "true":
    DATABASE_CONFIG = TEST_DATABASE_CONFIG