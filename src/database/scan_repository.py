#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository für Scan-bezogene Datenbankoperationen
Implementiert das Repository-Pattern für Scan-Daten
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from contextlib import contextmanager

from .connection import DatabaseConnection, ConnectionPool
from .queries import Queries, QueryHelper
from config.constants import ScanTypes, StatusCodes

# Logger einrichten
logger = logging.getLogger(__name__)


# ==============================================================================
# ScanRepository Klasse
# ==============================================================================

class ScanRepository:
    """
    Repository für alle Scan-bezogenen Datenbankoperationen
    Verwaltet ScannKopf und ScannPosition Einträge
    """

    def __init__(self, connection: DatabaseConnection = None,
                 pool: ConnectionPool = None):
        """
        Initialisiert das Repository

        Args:
            connection: Optionale Datenbankverbindung
            pool: Optionaler Connection Pool
        """
        self.connection = connection
        self.pool = pool
        self._owns_connection = False

        # Wenn weder Connection noch Pool übergeben, eigenen Pool erstellen
        if not self.connection and not self.pool:
            self.pool = ConnectionPool()
            self.pool.initialize()

    @contextmanager
    def _get_connection(self):
        """
        Context Manager für Datenbankverbindung
        Holt Verbindung aus Pool oder nutzt bestehende
        """
        if self.connection:
            # Bestehende Verbindung nutzen
            yield self.connection
        else:
            # Verbindung aus Pool holen
            conn = self.pool.get_connection()
            try:
                yield conn
            finally:
                self.pool.release_connection(conn)

    # ==========================================================================
    # Scan-Kopf Operationen
    # ==========================================================================

    def create_scan_session(self, epc: int, scan_type_id: int,
                            arbeitsplatz: str = None,
                            benutzer: str = "System") -> Optional[int]:
        """
        Erstellt eine neue Scan-Session (ScannKopf)

        Args:
            epc: EPC (RFID-Tag) des Benutzers
            scan_type_id: ID des Scan-Typs (1-6)
            arbeitsplatz: Arbeitsplatz-Bezeichnung
            benutzer: Benutzername für Audit

        Returns:
            int: ID der erstellten Session oder None bei Fehler
        """
        try:
            with self._get_connection() as conn:
                # Prüfe ob bereits aktive Session existiert
                existing = self.get_active_session(epc)
                if existing:
                    logger.warning(
                        f"Aktive Session bereits vorhanden für EPC {epc}"
                    )
                    return existing["id"]

                # Daten vorbereiten
                now = datetime.now()
                today = now.date()

                params = (
                    today,  # TagesDatum
                    int(today.strftime("%Y%m%d")),  # TagesDatumINT
                    now,  # Datum
                    QueryHelper.format_datetime_int(now),  # DatumINT
                    epc,  # EPC
                    arbeitsplatz or "Station-01",  # Arbeitsplatz
                    scan_type_id,  # ScannTyp_ID
                    StatusCodes.ACTIVE,  # xStatus
                    now,  # xDatum
                    QueryHelper.format_datetime_int(now),  # xDatumINT
                    benutzer  # xBenutzer
                )

                # Session erstellen
                result = conn.execute_scalar(Queries.ScanHead.CREATE, params)

                if result:
                    logger.info(
                        f"Scan-Session {result} erstellt für EPC {epc}, "
                        f"Typ {scan_type_id}"
                    )
                    return result
                else:
                    logger.error("Keine ID von INSERT erhalten")
                    return None

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Scan-Session: {e}")
            return None

    def get_active_session(self, epc: int) -> Optional[Dict[str, Any]]:
        """
        Holt die aktive Scan-Session eines Benutzers

        Args:
            epc: EPC des Benutzers

        Returns:
            Dict mit Session-Daten oder None
        """
        try:
            with self._get_connection() as conn:
                result = conn.execute_query(
                    Queries.ScanHead.GET_ACTIVE_SESSION,
                    (epc,)
                )

                if result and len(result) > 0:
                    row = result[0]
                    return {
                        "id": row[0],
                        "datum": row[1],
                        "arbeitsplatz": row[2],
                        "scan_typ": row[3]
                    }

                return None

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der aktiven Session: {e}")
            return None

    def close_session(self, session_id: int) -> bool:
        """
        Beendet eine Scan-Session

        Args:
            session_id: ID der zu beendenden Session

        Returns:
            bool: True bei Erfolg
        """
        try:
            with self._get_connection() as conn:
                affected = conn.execute_query(
                    Queries.ScanHead.CLOSE_SESSION,
                    (session_id,)
                )

                if affected > 0:
                    logger.info(f"Session {session_id} beendet")
                    return True
                else:
                    logger.warning(f"Session {session_id} nicht gefunden")
                    return False

        except Exception as e:
            logger.error(f"Fehler beim Beenden der Session: {e}")
            return False

    def get_scan_sessions_by_date(self, scan_date: date = None) -> List[Dict[str, Any]]:
        """
        Holt alle Scan-Sessions eines Tages

        Args:
            scan_date: Datum (None = heute)

        Returns:
            Liste von Session-Daten
        """
        if scan_date is None:
            scan_date = date.today()

        try:
            with self._get_connection() as conn:
                results = conn.execute_query(
                    Queries.ScanHead.GET_BY_DATE,
                    (scan_date,)
                )

                sessions = []
                for row in results:
                    sessions.append({
                        "id": row[0],
                        "epc": row[1],
                        "benutzer_name": row[2],
                        "datum": row[3],
                        "arbeitsplatz": row[4],
                        "scan_typ": row[5],
                        "anzahl_scans": row[6]
                    })

                return sessions

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Sessions: {e}")
            return []

    # ==========================================================================
    # Scan-Position Operationen
    # ==========================================================================

    def add_scan_position(self, session_id: int, kunde: str = None,
                          auftragsnummer: str = None, paketnummer: str = None,
                          zusatzinfo: str = None,
                          benutzer: str = "System") -> Optional[int]:
        """
        Fügt eine neue Scan-Position hinzu

        Args:
            session_id: ID der Scan-Session (ScannKopf)
            kunde: Kundenname
            auftragsnummer: Auftragsnummer
            paketnummer: Paketnummer
            zusatzinfo: Zusätzliche Informationen
            benutzer: Benutzername für Audit

        Returns:
            int: ID der erstellten Position oder None bei Fehler
        """
        try:
            with self._get_connection() as conn:
                # Daten vorbereiten
                now = datetime.now()
                today = now.date()

                params = (
                    session_id,  # ScannKopf_ID
                    today,  # TagesDatum
                    int(today.strftime("%Y%m%d")),  # TagesDatumINT
                    now,  # Datum
                    QueryHelper.format_datetime_int(now),  # DatumINT
                    kunde,  # Kunde
                    auftragsnummer,  # Auftragsnummer
                    paketnummer,  # Paketnummer
                    zusatzinfo,  # Zusatzinformtion
                    StatusCodes.ACTIVE,  # xStatus
                    now,  # xDatum
                    QueryHelper.format_datetime_int(now),  # xDatumINT
                    benutzer  # xBenutzer
                )

                # Position erstellen
                result = conn.execute_scalar(
                    Queries.ScanPosition.CREATE,
                    params
                )

                if result:
                    logger.info(
                        f"Scan-Position {result} erstellt für Session {session_id}"
                    )
                    return result
                else:
                    logger.error("Keine ID von INSERT erhalten")
                    return None

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Scan-Position: {e}")
            return None

    def get_scan_positions(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Holt alle Scan-Positionen einer Session

        Args:
            session_id: ID der Scan-Session

        Returns:
            Liste von Scan-Positionen
        """
        try:
            with self._get_connection() as conn:
                results = conn.execute_query(
                    Queries.ScanPosition.GET_BY_SCAN_HEAD,
                    (session_id,)
                )

                positions = []
                for row in results:
                    positions.append({
                        "id": row[0],
                        "datum": row[1],
                        "kunde": row[2],
                        "auftragsnummer": row[3],
                        "paketnummer": row[4],
                        "zusatzinfo": row[5]
                    })

                return positions

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Scan-Positionen: {e}")
            return []

    def check_duplicate_scan(self, paketnummer: str,
                             scan_type_id: int) -> Optional[Dict[str, Any]]:
        """
        Prüft ob ein Paket heute bereits gescannt wurde

        Args:
            paketnummer: Paketnummer
            scan_type_id: Scan-Typ ID

        Returns:
            Dict mit vorherigem Scan oder None
        """
        try:
            with self._get_connection() as conn:
                result = conn.execute_query(
                    Queries.ScanPosition.CHECK_DUPLICATE,
                    (paketnummer, scan_type_id)
                )

                if result and len(result) > 0:
                    row = result[0]
                    return {
                        "id": row[0],
                        "datum": row[1],
                        "arbeitsplatz": row[2],
                        "benutzer": row[3]
                    }

                return None

        except Exception as e:
            logger.error(f"Fehler bei Duplikat-Prüfung: {e}")
            return None

    def delete_scan_position(self, position_id: int,
                             benutzer: str = "System") -> bool:
        """
        Löscht eine Scan-Position (Soft Delete)

        Args:
            position_id: ID der zu löschenden Position
            benutzer: Benutzername für Audit

        Returns:
            bool: True bei Erfolg
        """
        try:
            with self._get_connection() as conn:
                affected = conn.execute_query(
                    Queries.ScanPosition.DELETE,
                    (benutzer, position_id)
                )

                if affected > 0:
                    logger.info(f"Scan-Position {position_id} gelöscht")
                    return True
                else:
                    logger.warning(f"Scan-Position {position_id} nicht gefunden")
                    return False

        except Exception as e:
            logger.error(f"Fehler beim Löschen der Scan-Position: {e}")
            return False

    def get_user_scan_count_today(self, epc: int) -> int:
        """
        Holt die Anzahl der Scans eines Benutzers heute

        Args:
            epc: EPC des Benutzers

        Returns:
            int: Anzahl der Scans
        """
        try:
            with self._get_connection() as conn:
                count = conn.execute_scalar(
                    Queries.ScanPosition.COUNT_TODAY,
                    (epc,)
                )
                return count or 0

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Scan-Anzahl: {e}")
            return 0

    def get_recent_scans_by_user(self, epc: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Holt die letzten Scans eines Benutzers

        Args:
            epc: EPC des Benutzers
            limit: Maximale Anzahl (Standard: 10)

        Returns:
            Liste der letzten Scans
        """
        try:
            with self._get_connection() as conn:
                # Query anpassen für Limit
                query = Queries.ScanPosition.GET_RECENT_BY_USER.replace(
                    "TOP 10", f"TOP {limit}"
                )

                results = conn.execute_query(query, (epc,))

                scans = []
                for row in results:
                    scans.append({
                        "id": row[0],
                        "datum": row[1],
                        "kunde": row[2],
                        "auftragsnummer": row[3],
                        "paketnummer": row[4],
                        "scan_typ": row[5]
                    })

                return scans

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der letzten Scans: {e}")
            return []

    # ==========================================================================
    # Scan-Typ Operationen
    # ==========================================================================

    def get_scan_types(self) -> List[Dict[str, Any]]:
        """
        Holt alle aktiven Scan-Typen

        Returns:
            Liste der Scan-Typen
        """
        try:
            with self._get_connection() as conn:
                results = conn.execute_query(Queries.ScanType.GET_ALL_ACTIVE)

                scan_types = []
                for row in results:
                    scan_types.append({
                        "id": row[0],
                        "bezeichnung": row[1]
                    })

                return scan_types

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Scan-Typen: {e}")
            return []

    def get_scan_type_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Holt einen Scan-Typ nach Bezeichnung

        Args:
            name: Bezeichnung des Scan-Typs

        Returns:
            Dict mit Scan-Typ oder None
        """
        try:
            with self._get_connection() as conn:
                result = conn.execute_query(
                    Queries.ScanType.GET_BY_NAME,
                    (name,)
                )

                if result and len(result) > 0:
                    row = result[0]
                    return {
                        "id": row[0],
                        "bezeichnung": row[1]
                    }

                return None

        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Scan-Typs: {e}")
            return None

    # ==========================================================================
    # Statistik-Funktionen
    # ==========================================================================

    def get_daily_statistics(self, scan_date: date = None) -> Dict[str, Any]:
        """
        Holt Tagesstatistiken

        Args:
            scan_date: Datum (None = heute)

        Returns:
            Dict mit Statistiken
        """
        if scan_date is None:
            scan_date = date.today()

        try:
            with self._get_connection() as conn:
                # Übersicht
                overview = conn.execute_query(
                    Queries.Statistics.DAILY_OVERVIEW,
                    (scan_date,)
                )

                # Nach Scan-Typ
                by_type = conn.execute_query(
                    Queries.ScanHead.GET_DAILY_STATS,
                    (scan_date,)
                )

                # Stundenverteilung
                hourly = conn.execute_query(
                    Queries.Statistics.HOURLY_DISTRIBUTION,
                    (scan_date,)
                )

                stats = {
                    "datum": scan_date,
                    "übersicht": {},
                    "nach_typ": [],
                    "stundenverteilung": []
                }

                # Übersicht verarbeiten
                if overview and len(overview) > 0:
                    row = overview[0]
                    stats["übersicht"] = {
                        "anzahl_benutzer": row[0] or 0,
                        "anzahl_sessions": row[1] or 0,
                        "anzahl_scans": row[2] or 0,
                        "erster_scan": row[3],
                        "letzter_scan": row[4]
                    }

                # Nach Typ verarbeiten
                for row in by_type:
                    stats["nach_typ"].append({
                        "scan_typ": row[0],
                        "sessions": row[1],
                        "benutzer": row[2],
                        "scans": row[3]
                    })

                # Stundenverteilung verarbeiten
                for row in hourly:
                    stats["stundenverteilung"].append({
                        "stunde": row[0],
                        "anzahl": row[1]
                    })

                return stats

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
            return {
                "datum": scan_date,
                "übersicht": {},
                "nach_typ": [],
                "stundenverteilung": []
            }

    # ==========================================================================
    # Transaktions-Management
    # ==========================================================================

    @contextmanager
    def transaction(self):
        """
        Context Manager für Transaktionen

        Usage:
            with repo.transaction():
                repo.create_scan_session(...)
                repo.add_scan_position(...)
        """
        with self._get_connection() as conn:
            conn.begin_transaction()
            try:
                yield self
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    # ==========================================================================
    # Cleanup
    # ==========================================================================

    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """
        Bereinigt alte gelöschte Daten

        Args:
            days_to_keep: Anzahl Tage die behalten werden sollen

        Returns:
            int: Anzahl gelöschter Datensätze
        """
        try:
            with self._get_connection() as conn:
                deleted = conn.execute_query(
                    Queries.System.CLEANUP_OLD_DATA,
                    (-days_to_keep,)  # Negativ für DATEADD
                )

                logger.info(f"{deleted} alte Datensätze bereinigt")
                return deleted

        except Exception as e:
            logger.error(f"Fehler bei der Datenbereinigung: {e}")
            return 0

    def close(self):
        """Schließt alle Verbindungen"""
        if self._owns_connection and self.pool:
            self.pool.close_all()