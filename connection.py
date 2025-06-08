#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbank Connection Pool
Minimale Version mit pyodbc
"""

import pyodbc
import threading
from config import DB_CONFIG
from utils import get_logger

logger = get_logger('Database')

# Thread-Local Storage für Connections
_thread_local = threading.local()


def get_connection_string():
    """Erstellt den Connection String"""
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['user']};"
        f"PWD={DB_CONFIG['password']};"
    )

    if DB_CONFIG.get('trust_cert'):
        conn_str += "TrustServerCertificate=yes;"

    if DB_CONFIG.get('encrypt') is False:
        conn_str += "Encrypt=no;"

    return conn_str


def get_connection():
    """Gibt eine Datenbankverbindung zurück (Thread-Safe)"""
    if not hasattr(_thread_local, 'connection') or _thread_local.connection is None:
        try:
            _thread_local.connection = pyodbc.connect(get_connection_string())
            _thread_local.connection.autocommit = True
            logger.debug("Neue Datenbankverbindung erstellt")
        except pyodbc.Error as e:
            logger.error(f"Datenbankverbindung fehlgeschlagen: {e}")
            raise

    return _thread_local.connection


def close_connection():
    """Schließt die Thread-lokale Verbindung"""
    if hasattr(_thread_local, 'connection') and _thread_local.connection:
        try:
            _thread_local.connection.close()
            _thread_local.connection = None
            logger.debug("Datenbankverbindung geschlossen")
        except:
            pass


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Führt eine Query aus und gibt Ergebnisse zurück"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        else:
            # Für INSERT, UPDATE, DELETE
            return cursor.rowcount

    except pyodbc.Error as e:
        logger.error(f"Query-Fehler: {e}")
        logger.error(f"Query: {query}")
        raise
    finally:
        cursor.close()


def execute_scalar(query, params=None):
    """Führt eine Query aus und gibt einen einzelnen Wert zurück"""
    result = execute_query(query, params, fetch_one=True)
    return result[0] if result else None


def test_connection():
    """Testet die Datenbankverbindung"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        return result[0] == 1
    except Exception as e:
        logger.error(f"Verbindungstest fehlgeschlagen: {e}")
        return False