#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Package für die Wareneingang-Anwendung

Dieses Package stellt alle Datenbank-bezogenen Funktionalitäten zur Verfügung:
- Verbindungsverwaltung
- Repository-Pattern für Datenzugriff
- Query-Definitionen
- Connection-Pooling
"""

from typing import TYPE_CHECKING

# Versionsinformation
__version__ = "1.0.0"
__author__ = "Shirtful GmbH"

# Lazy imports für bessere Performance
if TYPE_CHECKING:
    from .connection import DatabaseConnection, ConnectionPool
    from .user_repository import UserRepository
    from .scan_repository import ScanRepository
    from .queries import Queries

# Package-Level Imports
__all__ = [
    # Connection Management
    "DatabaseConnection",
    "ConnectionPool",
    "get_connection",
    "close_all_connections",

    # Repositories
    "UserRepository",
    "ScanRepository",

    # Queries
    "Queries",
    "QueryBuilder",

    # Exceptions
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    "RepositoryError",

    # Utilities
    "test_connection",
    "migrate_database",
    "backup_database",
]


# ==============================================================================
# Exceptions
# ==============================================================================

class DatabaseError(Exception):
    """Basis-Exception für alle Datenbank-Fehler"""
    pass


class ConnectionError(DatabaseError):
    """Fehler bei der Datenbankverbindung"""
    pass


class QueryError(DatabaseError):
    """Fehler bei der Query-Ausführung"""
    pass


class RepositoryError(DatabaseError):
    """Fehler in den Repository-Klassen"""
    pass


# ==============================================================================
# Singleton Connection Pool
# ==============================================================================

_connection_pool = None


def get_connection_pool():
    """Gibt die globale Connection Pool Instanz zurück"""
    global _connection_pool
    if _connection_pool is None:
        from .connection import ConnectionPool
        _connection_pool = ConnectionPool()
    return _connection_pool


def get_connection():
    """
    Holt eine Datenbankverbindung aus dem Pool

    Returns:
        DatabaseConnection: Aktive Datenbankverbindung

    Raises:
        ConnectionError: Wenn keine Verbindung hergestellt werden kann
    """
    pool = get_connection_pool()
    return pool.get_connection()


def close_all_connections():
    """Schließt alle offenen Datenbankverbindungen"""
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.close_all()
        _connection_pool = None


# ==============================================================================
# Utility Functions
# ==============================================================================

def test_connection(config=None):
    """
    Testet die Datenbankverbindung

    Args:
        config: Optionale Datenbank-Konfiguration

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        from .connection import DatabaseConnection
        from config.database import DATABASE_CONFIG

        test_config = config or DATABASE_CONFIG
        conn = DatabaseConnection(test_config)

        if conn.connect():
            # Test-Query ausführen
            cursor = conn.execute_query("SELECT 1 AS test")
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == 1:
                return True, "Verbindung erfolgreich"
            else:
                return False, "Test-Query fehlgeschlagen"
        else:
            return False, "Verbindung konnte nicht hergestellt werden"

    except Exception as e:
        return False, f"Fehler: {str(e)}"


def migrate_database(version=None):
    """
    Führt Datenbank-Migrationen durch

    Args:
        version: Ziel-Version (None = neueste)

    Returns:
        bool: True bei Erfolg
    """
    # TODO: Implementierung von Migrations-System
    raise NotImplementedError("Datenbank-Migrationen noch nicht implementiert")


def backup_database(backup_path=None):
    """
    Erstellt ein Backup der Datenbank

    Args:
        backup_path: Pfad für Backup-Datei

    Returns:
        str: Pfad zur Backup-Datei
    """
    # TODO: Implementierung von Backup-Funktionalität
    raise NotImplementedError("Datenbank-Backup noch nicht implementiert")


# ==============================================================================
# Query Builder Helper
# ==============================================================================

class QueryBuilder:
    """Einfacher Query Builder für häufige Operationen"""

    @staticmethod
    def select(table, columns="*", where=None, order_by=None, limit=None):
        """Baut eine SELECT-Query"""
        query = f"SELECT {columns} FROM {table}"

        if where:
            conditions = " AND ".join([f"{k} = ?" for k in where.keys()])
            query += f" WHERE {conditions}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" TOP {limit}"

        return query

    @staticmethod
    def insert(table, data):
        """Baut eine INSERT-Query"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        return f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    @staticmethod
    def update(table, data, where):
        """Baut eine UPDATE-Query"""
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        where_clause = " AND ".join([f"{k} = ?" for k in where.keys()])
        return f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

    @staticmethod
    def delete(table, where):
        """Baut eine DELETE-Query"""
        where_clause = " AND ".join([f"{k} = ?" for k in where.keys()])
        return f"DELETE FROM {table} WHERE {where_clause}"


# ==============================================================================
# Initialisierung
# ==============================================================================

def initialize_database():
    """
    Initialisiert die Datenbank-Verbindung beim Import
    Wird nur aufgerufen wenn AUTO_CONNECT = True
    """
    import os
    from config.settings import DEBUG_SETTINGS

    if os.getenv("DATABASE_AUTO_CONNECT", "false").lower() == "true":
        try:
            pool = get_connection_pool()
            pool.initialize()

            if DEBUG_SETTINGS.get("enabled", False):
                success, message = test_connection()
                print(f"Datenbank-Verbindungstest: {message}")

        except Exception as e:
            if DEBUG_SETTINGS.get("enabled", False):
                print(f"Fehler bei Datenbank-Initialisierung: {e}")


# Cleanup bei Modul-Entladung
import atexit

atexit.register(close_all_connections)