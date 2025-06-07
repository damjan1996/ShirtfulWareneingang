#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbank-Verbindungsverwaltung für die Wareneingang-Anwendung
Implementiert Connection-Pooling und automatisches Retry
"""

import pyodbc
import threading
import queue
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager
from datetime import datetime, timedelta

from config.database import (
    DATABASE_CONFIG,
    ODBC_DRIVERS,
    get_connection_string,
    get_all_connection_strings,
    POOL_CONFIG,
    QUERY_CONFIG
)
from config.settings import LOGGING_SETTINGS, PERFORMANCE_SETTINGS

# Logger einrichten
logger = logging.getLogger(__name__)


# ==============================================================================
# DatabaseConnection Klasse
# ==============================================================================

class DatabaseConnection:
    """
    Wrapper für eine einzelne Datenbankverbindung
    Implementiert automatisches Retry und Query-Logging
    """

    def __init__(self, config: Dict[str, Any] = None, pool_id: int = None):
        """
        Initialisiert eine Datenbankverbindung

        Args:
            config: Datenbank-Konfiguration (Standard: DATABASE_CONFIG)
            pool_id: ID für Connection-Pool Management
        """
        self.config = config or DATABASE_CONFIG
        self.pool_id = pool_id
        self.connection = None
        self.cursor = None
        self._connected = False
        self._in_transaction = False
        self._last_used = time.time()
        self._query_count = 0
        self._lock = threading.Lock()

        # Performance Tracking
        self.slow_query_threshold = QUERY_CONFIG.get("slow_query_threshold", 5)
        self.enable_query_logging = QUERY_CONFIG.get("enable_query_logging", True)

    def connect(self) -> bool:
        """
        Stellt eine Verbindung zur Datenbank her
        Versucht alle verfügbaren ODBC-Driver

        Returns:
            bool: True bei erfolgreicher Verbindung
        """
        with self._lock:
            if self._connected and self.connection:
                return True

            connection_strings = get_all_connection_strings(self.config)

            for i, conn_str in enumerate(connection_strings):
                try:
                    logger.debug(f"Verbindungsversuch {i + 1}/{len(connection_strings)}")

                    self.connection = pyodbc.connect(
                        conn_str,
                        autocommit=False,
                        timeout=self.config.get("timeout", 30)
                    )

                    # Verbindung testen
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()

                    self._connected = True
                    self._last_used = time.time()

                    logger.info(f"Datenbankverbindung hergestellt (Pool-ID: {self.pool_id})")
                    return True

                except pyodbc.Error as e:
                    logger.warning(f"Verbindungsversuch {i + 1} fehlgeschlagen: {e}")
                    if self.connection:
                        try:
                            self.connection.close()
                        except:
                            pass
                        self.connection = None

            logger.error("Keine Datenbankverbindung möglich")
            return False

    def close(self):
        """Schließt die Datenbankverbindung"""
        with self._lock:
            if self.cursor:
                try:
                    self.cursor.close()
                except:
                    pass
                self.cursor = None

            if self.connection:
                try:
                    if self._in_transaction:
                        self.connection.rollback()
                    self.connection.close()
                except:
                    pass
                self.connection = None

            self._connected = False
            self._in_transaction = False
            logger.debug(f"Datenbankverbindung geschlossen (Pool-ID: {self.pool_id})")

    def is_alive(self) -> bool:
        """
        Prüft ob die Verbindung noch aktiv ist

        Returns:
            bool: True wenn Verbindung aktiv
        """
        if not self._connected or not self.connection:
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except:
            return False

    def execute_query(self, query: str, params: Tuple = None,
                      fetch_all: bool = True) -> Any:
        """
        Führt eine SQL-Query aus

        Args:
            query: SQL-Query
            params: Query-Parameter (optional)
            fetch_all: Alle Zeilen abrufen (True) oder Cursor zurückgeben (False)

        Returns:
            Query-Ergebnis oder Cursor

        Raises:
            Exception: Bei Query-Fehlern
        """
        if not self._connected:
            if not self.connect():
                raise Exception("Keine Datenbankverbindung")

        start_time = time.time()
        rows_affected = 0

        try:
            with self._lock:
                cursor = self.connection.cursor()

                # Parameter vorbereiten
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                self._query_count += 1
                self._last_used = time.time()

                # Ergebnis abrufen
                if fetch_all:
                    if query.strip().upper().startswith(("SELECT", "WITH")):
                        result = cursor.fetchall()
                        rows_affected = len(result) if result else 0
                        cursor.close()
                        return result
                    else:
                        rows_affected = cursor.rowcount
                        cursor.close()
                        return rows_affected
                else:
                    return cursor

        except Exception as e:
            logger.error(f"Query-Fehler: {e}\nQuery: {query}")
            if cursor:
                cursor.close()
            raise

        finally:
            # Query-Logging
            if self.enable_query_logging:
                execution_time = time.time() - start_time
                self._log_query(query, params, execution_time, rows_affected)

    def execute_scalar(self, query: str, params: Tuple = None) -> Any:
        """
        Führt eine Query aus und gibt den ersten Wert zurück

        Args:
            query: SQL-Query
            params: Query-Parameter

        Returns:
            Erster Wert des Ergebnisses oder None
        """
        cursor = self.execute_query(query, params, fetch_all=False)
        try:
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            cursor.close()

    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Führt eine Query mehrfach mit verschiedenen Parametern aus

        Args:
            query: SQL-Query
            params_list: Liste von Parameter-Tupeln

        Returns:
            int: Anzahl betroffener Zeilen
        """
        if not self._connected:
            if not self.connect():
                raise Exception("Keine Datenbankverbindung")

        start_time = time.time()
        total_rows = 0

        try:
            with self._lock:
                cursor = self.connection.cursor()

                for params in params_list:
                    cursor.execute(query, params)
                    total_rows += cursor.rowcount

                cursor.close()
                self._query_count += len(params_list)
                self._last_used = time.time()

                return total_rows

        except Exception as e:
            logger.error(f"Batch-Query-Fehler: {e}")
            raise

        finally:
            if self.enable_query_logging:
                execution_time = time.time() - start_time
                self._log_query(f"{query} (Batch: {len(params_list)})",
                                None, execution_time, total_rows)

    def begin_transaction(self):
        """Startet eine Transaktion"""
        if not self._connected:
            if not self.connect():
                raise Exception("Keine Datenbankverbindung")

        with self._lock:
            if not self._in_transaction:
                self._in_transaction = True
                logger.debug("Transaktion gestartet")

    def commit(self):
        """Committed die aktuelle Transaktion"""
        if self._connected and self.connection and self._in_transaction:
            with self._lock:
                try:
                    self.connection.commit()
                    self._in_transaction = False
                    logger.debug("Transaktion committed")
                except Exception as e:
                    logger.error(f"Commit-Fehler: {e}")
                    raise

    def rollback(self):
        """Rollt die aktuelle Transaktion zurück"""
        if self._connected and self.connection and self._in_transaction:
            with self._lock:
                try:
                    self.connection.rollback()
                    self._in_transaction = False
                    logger.debug("Transaktion zurückgerollt")
                except Exception as e:
                    logger.error(f"Rollback-Fehler: {e}")
                    raise

    @contextmanager
    def transaction(self):
        """
        Context Manager für Transaktionen

        Usage:
            with connection.transaction():
                connection.execute_query(...)
                connection.execute_query(...)
        """
        self.begin_transaction()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise

    def _log_query(self, query: str, params: Tuple, execution_time: float,
                   rows_affected: int):
        """Loggt Query-Informationen"""
        if execution_time > self.slow_query_threshold:
            logger.warning(
                f"Langsame Query ({execution_time:.2f}s): {query[:100]}... "
                f"({rows_affected} Zeilen)"
            )
        elif logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Query ({execution_time:.3f}s): {query[:100]}... "
                f"({rows_affected} Zeilen)"
            )

    @property
    def statistics(self) -> Dict[str, Any]:
        """Gibt Verbindungsstatistiken zurück"""
        return {
            "pool_id": self.pool_id,
            "connected": self._connected,
            "in_transaction": self._in_transaction,
            "query_count": self._query_count,
            "last_used": datetime.fromtimestamp(self._last_used),
            "age_seconds": time.time() - self._last_used
        }


# ==============================================================================
# ConnectionPool Klasse
# ==============================================================================

class ConnectionPool:
    """
    Verwaltet einen Pool von Datenbankverbindungen
    Implementiert Connection-Reuse und automatisches Cleanup
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialisiert den Connection Pool

        Args:
            config: Pool-Konfiguration (Standard: POOL_CONFIG)
        """
        self.config = config or POOL_CONFIG
        self.db_config = DATABASE_CONFIG

        # Pool-Parameter
        self.min_size = self.config.get("min_size", 1)
        self.max_size = self.config.get("max_size", 5)
        self.timeout = self.config.get("timeout", 30)
        self.idle_time = self.config.get("idle_time", 300)
        self.retry_count = self.config.get("retry_count", 3)
        self.retry_delay = self.config.get("retry_delay", 1)

        # Pool-Verwaltung
        self._pool = queue.Queue(maxsize=self.max_size)
        self._all_connections = []
        self._lock = threading.Lock()
        self._shutdown = False
        self._initialized = False

        # Cleanup-Thread
        self._cleanup_thread = None
        self._cleanup_interval = 60  # Sekunden

        # Statistiken
        self._stats = {
            "created": 0,
            "active": 0,
            "idle": 0,
            "closed": 0,
            "errors": 0,
            "wait_time_total": 0,
            "wait_count": 0
        }

    def initialize(self):
        """Initialisiert den Connection Pool"""
        with self._lock:
            if self._initialized:
                return

            logger.info(f"Initialisiere Connection Pool (min={self.min_size}, max={self.max_size})")

            # Minimale Anzahl Verbindungen erstellen
            for i in range(self.min_size):
                try:
                    conn = self._create_connection()
                    if conn:
                        self._pool.put(conn)
                except Exception as e:
                    logger.error(f"Fehler beim Erstellen der Verbindung {i + 1}: {e}")

            # Cleanup-Thread starten
            self._start_cleanup_thread()

            self._initialized = True
            logger.info("Connection Pool initialisiert")

    def get_connection(self, timeout: float = None) -> DatabaseConnection:
        """
        Holt eine Verbindung aus dem Pool

        Args:
            timeout: Maximale Wartezeit (Standard: self.timeout)

        Returns:
            DatabaseConnection: Aktive Datenbankverbindung

        Raises:
            Exception: Wenn keine Verbindung verfügbar
        """
        if self._shutdown:
            raise Exception("Connection Pool ist heruntergefahren")

        if not self._initialized:
            self.initialize()

        timeout = timeout or self.timeout
        start_time = time.time()

        # Versuche Verbindung aus Pool zu holen
        for attempt in range(self.retry_count):
            try:
                # Warte auf verfügbare Verbindung
                wait_timeout = timeout - (time.time() - start_time)
                if wait_timeout <= 0:
                    break

                conn = self._pool.get(timeout=wait_timeout)

                # Prüfe ob Verbindung noch aktiv
                if conn.is_alive():
                    with self._lock:
                        self._stats["active"] += 1
                        self._stats["idle"] -= 1
                        self._stats["wait_time_total"] += time.time() - start_time
                        self._stats["wait_count"] += 1
                    return conn
                else:
                    # Verbindung ist tot, schließen und neue erstellen
                    logger.warning(f"Tote Verbindung gefunden (Pool-ID: {conn.pool_id})")
                    self._close_connection(conn)

            except queue.Empty:
                # Pool ist leer, versuche neue Verbindung zu erstellen
                if self._can_create_connection():
                    conn = self._create_connection()
                    if conn:
                        with self._lock:
                            self._stats["active"] += 1
                        return conn

            # Kurz warten vor nächstem Versuch
            if attempt < self.retry_count - 1:
                time.sleep(self.retry_delay)

        # Timeout erreicht
        raise Exception(
            f"Keine Datenbankverbindung verfügbar (Timeout: {timeout}s, "
            f"Active: {self._stats['active']}, Pool: {self._pool.qsize()})"
        )

    def release_connection(self, conn: DatabaseConnection):
        """
        Gibt eine Verbindung zurück in den Pool

        Args:
            conn: Die zurückzugebende Verbindung
        """
        if self._shutdown:
            self._close_connection(conn)
            return

        if not conn:
            return

        try:
            # Transaktion beenden falls aktiv
            if conn._in_transaction:
                try:
                    conn.rollback()
                except:
                    pass

            # Verbindung prüfen
            if conn.is_alive():
                # Zurück in den Pool
                self._pool.put(conn)
                with self._lock:
                    self._stats["active"] -= 1
                    self._stats["idle"] += 1
            else:
                # Verbindung ist tot
                self._close_connection(conn)

        except queue.Full:
            # Pool ist voll, Verbindung schließen
            self._close_connection(conn)

    @contextmanager
    def get_connection_context(self, timeout: float = None):
        """
        Context Manager für automatisches Connection Management

        Usage:
            with pool.get_connection_context() as conn:
                conn.execute_query(...)
        """
        conn = self.get_connection(timeout)
        try:
            yield conn
        finally:
            self.release_connection(conn)

    def close_all(self):
        """Schließt alle Verbindungen und fährt den Pool herunter"""
        logger.info("Fahre Connection Pool herunter...")

        with self._lock:
            self._shutdown = True

        # Cleanup-Thread stoppen
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)

        # Alle Verbindungen aus Pool holen und schließen
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                self._close_connection(conn)
            except queue.Empty:
                break

        # Alle registrierten Verbindungen schließen
        with self._lock:
            for conn in self._all_connections:
                try:
                    if conn.connection:
                        conn.close()
                except:
                    pass
            self._all_connections.clear()

        logger.info(f"Connection Pool heruntergefahren. Statistiken: {self._stats}")

    def _create_connection(self) -> Optional[DatabaseConnection]:
        """Erstellt eine neue Datenbankverbindung"""
        try:
            pool_id = len(self._all_connections) + 1
            conn = DatabaseConnection(self.db_config, pool_id)

            if conn.connect():
                with self._lock:
                    self._all_connections.append(conn)
                    self._stats["created"] += 1
                    self._stats["idle"] += 1

                logger.debug(f"Neue Verbindung erstellt (Pool-ID: {pool_id})")
                return conn
            else:
                logger.error("Konnte keine neue Verbindung erstellen")
                with self._lock:
                    self._stats["errors"] += 1
                return None

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Verbindung: {e}")
            with self._lock:
                self._stats["errors"] += 1
            return None

    def _close_connection(self, conn: DatabaseConnection):
        """Schließt eine Verbindung und entfernt sie aus dem Pool"""
        try:
            conn.close()
        except:
            pass

        with self._lock:
            if conn in self._all_connections:
                self._all_connections.remove(conn)
            self._stats["closed"] += 1
            if self._stats["idle"] > 0:
                self._stats["idle"] -= 1

    def _can_create_connection(self) -> bool:
        """Prüft ob eine neue Verbindung erstellt werden kann"""
        with self._lock:
            total_connections = len(self._all_connections)
            return total_connections < self.max_size

    def _cleanup_idle_connections(self):
        """Entfernt inaktive Verbindungen"""
        current_time = time.time()
        connections_to_close = []

        # Temporäre Liste für aktive Verbindungen
        temp_connections = []

        # Alle Verbindungen aus Pool prüfen
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()

                # Prüfe ob Verbindung zu alt oder tot
                if (current_time - conn._last_used > self.idle_time or
                        not conn.is_alive()):
                    connections_to_close.append(conn)
                else:
                    temp_connections.append(conn)

            except queue.Empty:
                break

        # Aktive Verbindungen zurück in Pool
        for conn in temp_connections:
            try:
                self._pool.put_nowait(conn)
            except queue.Full:
                connections_to_close.append(conn)

        # Alte Verbindungen schließen
        for conn in connections_to_close:
            logger.debug(f"Schließe inaktive Verbindung (Pool-ID: {conn.pool_id})")
            self._close_connection(conn)

        # Sicherstellen dass minimale Anzahl verfügbar
        with self._lock:
            current_size = len(self._all_connections)
            if current_size < self.min_size:
                for _ in range(self.min_size - current_size):
                    conn = self._create_connection()
                    if conn:
                        try:
                            self._pool.put_nowait(conn)
                        except queue.Full:
                            pass

    def _cleanup_thread_func(self):
        """Thread-Funktion für regelmäßiges Cleanup"""
        logger.debug("Cleanup-Thread gestartet")

        while not self._shutdown:
            try:
                # Warte bis zum nächsten Cleanup
                for _ in range(self._cleanup_interval):
                    if self._shutdown:
                        break
                    time.sleep(1)

                if not self._shutdown:
                    self._cleanup_idle_connections()

                    # Log Statistiken
                    if logger.isEnabledFor(logging.DEBUG):
                        with self._lock:
                            logger.debug(
                                f"Pool-Status: Active={self._stats['active']}, "
                                f"Idle={self._stats['idle']}, "
                                f"Total={len(self._all_connections)}"
                            )

            except Exception as e:
                logger.error(f"Fehler im Cleanup-Thread: {e}")

        logger.debug("Cleanup-Thread beendet")

    def _start_cleanup_thread(self):
        """Startet den Cleanup-Thread"""
        if not self._cleanup_thread or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_thread_func,
                name="ConnectionPool-Cleanup",
                daemon=True
            )
            self._cleanup_thread.start()

    @property
    def statistics(self) -> Dict[str, Any]:
        """Gibt detaillierte Pool-Statistiken zurück"""
        with self._lock:
            stats = self._stats.copy()
            stats["pool_size"] = self._pool.qsize()
            stats["total_connections"] = len(self._all_connections)
            stats["avg_wait_time"] = (
                stats["wait_time_total"] / stats["wait_count"]
                if stats["wait_count"] > 0 else 0
            )

            # Verbindungsdetails
            connection_details = []
            for conn in self._all_connections:
                connection_details.append(conn.statistics)
            stats["connections"] = connection_details

            return stats