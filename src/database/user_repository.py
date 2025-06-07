#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository für Benutzer-bezogene Datenbankoperationen
Implementiert das Repository-Pattern für Benutzerdaten
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager

from .connection import DatabaseConnection, ConnectionPool
from .queries import Queries, QueryHelper
from config.constants import StatusCodes

# Logger einrichten
logger = logging.getLogger(__name__)


# ==============================================================================
# UserRepository Klasse
# ==============================================================================

class UserRepository:
    """
    Repository für alle Benutzer-bezogenen Datenbankoperationen
    Verwaltet ScannBenutzer Einträge und Authentifizierung
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

        # Cache für häufig abgerufene Benutzer
        self._cache = {}
        self._cache_ttl = 300  # 5 Minuten

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
    # Benutzer-Authentifizierung
    # ==========================================================================

    def authenticate_by_rfid(self, rfid_tag: str) -> Optional[Dict[str, Any]]:
        """
        Authentifiziert einen Benutzer anhand seines RFID-Tags

        Args:
            rfid_tag: RFID-Tag als Hex-String

        Returns:
            Dict mit Benutzerdaten oder None bei fehlgeschlagener Authentifizierung
        """
        try:
            # RFID-Tag zu Decimal konvertieren
            epc_decimal = int(rfid_tag.upper(), 16)

            # Aus Cache holen falls vorhanden
            cache_key = f"epc_{epc_decimal}"
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.debug(f"Benutzer aus Cache geladen: EPC {rfid_tag}")
                return cached

            # Aus Datenbank laden
            user = self.get_user_by_epc(epc_decimal)

            if user:
                # Letzte Aktivität aktualisieren
                self.update_last_activity(user["id"])

                # In Cache speichern
                self._set_cache(cache_key, user)

                logger.info(f"Benutzer authentifiziert: {user['benutzer_name']} (EPC: {rfid_tag})")
                return user
            else:
                logger.warning(f"Authentifizierung fehlgeschlagen: Unbekannter RFID-Tag {rfid_tag}")
                return None

        except ValueError:
            logger.error(f"Ungültiger RFID-Tag: {rfid_tag}")
            return None
        except Exception as e:
            logger.error(f"Fehler bei RFID-Authentifizierung: {e}")
            return None

    # ==========================================================================
    # Benutzer-Abfragen
    # ==========================================================================

    def get_user_by_epc(self, epc: int) -> Optional[Dict[str, Any]]:
        """
        Holt einen Benutzer anhand seiner EPC (RFID-Tag als Decimal)

        Args:
            epc: EPC als Decimal-Wert

        Returns:
            Dict mit Benutzerdaten oder None
        """
        try:
            with self._get_connection() as conn:
                result = conn.execute_query(
                    Queries.Users.GET_BY_EPC,
                    (epc,)
                )

                if result and len(result) > 0:
                    row = result[0]
                    return self._row_to_user_dict(row)

                return None

        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Benutzers (EPC: {epc}): {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Holt einen Benutzer anhand seiner ID

        Args:
            user_id: Benutzer-ID

        Returns:
            Dict mit Benutzerdaten oder None
        """
        try:
            # Aus Cache holen falls vorhanden
            cache_key = f"id_{user_id}"
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

            with self._get_connection() as conn:
                result = conn.execute_query(
                    Queries.Users.GET_BY_ID,
                    (user_id,)
                )

                if result and len(result) > 0:
                    row = result[0]
                    user = self._row_to_user_dict(row)

                    # In Cache speichern
                    self._set_cache(cache_key, user)

                    return user

                return None

        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Benutzers (ID: {user_id}): {e}")
            return None

    def get_all_active_users(self) -> List[Dict[str, Any]]:
        """
        Holt alle aktiven Benutzer

        Returns:
            Liste von Benutzerdaten
        """
        try:
            with self._get_connection() as conn:
                results = conn.execute_query(Queries.Users.GET_ALL_ACTIVE)

                users = []
                for row in results:
                    users.append({
                        "id": row[0],
                        "vorname": row[1],
                        "nachname": row[2],
                        "benutzer_name": row[3],
                        "email": row[4],
                        "epc": row[5],
                        "epc_hex": format(row[5], 'X') if row[5] else None,
                        "registriert_am": row[6]
                    })

                return users

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der aktiven Benutzer: {e}")
            return []

    def check_rfid_exists(self, rfid_tag: str) -> bool:
        """
        Prüft ob ein RFID-Tag bereits registriert ist

        Args:
            rfid_tag: RFID-Tag als Hex-String

        Returns:
            bool: True wenn Tag existiert
        """
        try:
            # RFID-Tag zu Decimal konvertieren
            epc_decimal = int(rfid_tag.upper(), 16)

            with self._get_connection() as conn:
                count = conn.execute_scalar(
                    Queries.Users.CHECK_EPC_EXISTS,
                    (epc_decimal,)
                )

                return count > 0

        except ValueError:
            logger.error(f"Ungültiger RFID-Tag: {rfid_tag}")
            return False
        except Exception as e:
            logger.error(f"Fehler bei RFID-Prüfung: {e}")
            return False

    # ==========================================================================
    # Benutzer-Verwaltung
    # ==========================================================================

    def create_user(self, vorname: str, nachname: str, rfid_tag: str,
                    email: str = None, benutzer_name: str = None,
                    created_by: str = "System") -> Optional[int]:
        """
        Erstellt einen neuen Benutzer

        Args:
            vorname: Vorname
            nachname: Nachname
            rfid_tag: RFID-Tag als Hex-String
            email: E-Mail-Adresse (optional)
            benutzer_name: Anzeigename (optional, wird generiert wenn leer)
            created_by: Ersteller für Audit

        Returns:
            int: ID des erstellten Benutzers oder None bei Fehler
        """
        try:
            # RFID-Tag zu Decimal konvertieren
            epc_decimal = int(rfid_tag.upper(), 16)

            # Prüfen ob Tag bereits existiert
            if self.check_rfid_exists(rfid_tag):
                logger.error(f"RFID-Tag {rfid_tag} bereits registriert")
                return None

            # Benutzername generieren falls nicht angegeben
            if not benutzer_name:
                benutzer_name = f"{vorname} {nachname}".strip()

            # Benutzer-Login generieren
            benutzer = f"{vorname.lower()}_{nachname.lower()}".replace(" ", "_")

            # E-Mail generieren falls nicht angegeben
            if not email:
                email = f"{benutzer}@shirtful.com"

            # Daten vorbereiten
            now = datetime.now()
            params = (
                vorname,
                nachname,
                benutzer,
                benutzer_name,
                "rfid",  # Standard-Passwort
                email,
                epc_decimal,
                StatusCodes.ACTIVE,
                now,
                QueryHelper.format_datetime_int(now),
                created_by
            )

            with self._get_connection() as conn:
                # Benutzer erstellen
                conn.execute_query(Queries.Users.CREATE, params)

                # ID des erstellten Benutzers abrufen
                result = conn.execute_query(
                    "SELECT @@IDENTITY AS NewID"
                )

                if result and len(result) > 0:
                    new_id = result[0][0]
                    logger.info(
                        f"Benutzer erstellt: {benutzer_name} (ID: {new_id}, "
                        f"RFID: {rfid_tag})"
                    )

                    # Cache invalidieren
                    self._clear_cache()

                    return int(new_id)
                else:
                    logger.error("Keine ID nach INSERT erhalten")
                    return None

        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Benutzers: {e}")
            return None

    def update_user(self, user_id: int, vorname: str = None,
                    nachname: str = None, email: str = None,
                    updated_by: str = "System") -> bool:
        """
        Aktualisiert Benutzerdaten

        Args:
            user_id: Benutzer-ID
            vorname: Neuer Vorname (optional)
            nachname: Neuer Nachname (optional)
            email: Neue E-Mail (optional)
            updated_by: Bearbeiter für Audit

        Returns:
            bool: True bei Erfolg
        """
        try:
            # Aktuellen Benutzer laden
            current = self.get_user_by_id(user_id)
            if not current:
                logger.error(f"Benutzer {user_id} nicht gefunden")
                return False

            # Nur übergebene Werte aktualisieren
            vorname = vorname or current["vorname"]
            nachname = nachname or current["nachname"]
            email = email or current["email"]

            # Update-Parameter
            now = datetime.now()
            params = (
                vorname,
                nachname,
                email,
                QueryHelper.format_datetime_int(now),
                updated_by,
                user_id
            )

            with self._get_connection() as conn:
                affected = conn.execute_query(
                    Queries.Users.UPDATE,
                    params
                )

                if affected > 0:
                    logger.info(f"Benutzer {user_id} aktualisiert")

                    # Cache invalidieren
                    self._clear_cache()

                    return True
                else:
                    logger.warning(f"Keine Änderungen für Benutzer {user_id}")
                    return False

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Benutzers: {e}")
            return False

    def deactivate_user(self, user_id: int, deactivated_by: str = "System") -> bool:
        """
        Deaktiviert einen Benutzer (Soft Delete)

        Args:
            user_id: Benutzer-ID
            deactivated_by: Bearbeiter für Audit

        Returns:
            bool: True bei Erfolg
        """
        try:
            now = datetime.now()
            params = (
                QueryHelper.format_datetime_int(now),
                deactivated_by,
                user_id
            )

            with self._get_connection() as conn:
                affected = conn.execute_query(
                    Queries.Users.DEACTIVATE,
                    params
                )

                if affected > 0:
                    logger.info(f"Benutzer {user_id} deaktiviert")

                    # Cache invalidieren
                    self._clear_cache()

                    return True
                else:
                    logger.warning(f"Benutzer {user_id} nicht gefunden")
                    return False

        except Exception as e:
            logger.error(f"Fehler beim Deaktivieren des Benutzers: {e}")
            return False

    def update_last_activity(self, user_id: int) -> bool:
        """
        Aktualisiert die letzte Aktivität eines Benutzers

        Args:
            user_id: Benutzer-ID

        Returns:
            bool: True bei Erfolg
        """
        try:
            with self._get_connection() as conn:
                affected = conn.execute_query(
                    Queries.Users.UPDATE_LAST_ACTIVITY,
                    (user_id,)
                )

                return affected > 0

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der letzten Aktivität: {e}")
            return False

    # ==========================================================================
    # Zeiterfassung
    # ==========================================================================

    def clock_in(self, user_id: int, epc: int) -> bool:
        """
        Stempelt einen Benutzer ein

        Args:
            user_id: Benutzer-ID
            epc: EPC des Benutzers

        Returns:
            bool: True bei Erfolg
        """
        try:
            # Prüfen ob bereits eingestempelt
            with self._get_connection() as conn:
                count = conn.execute_scalar(
                    Queries.TimeTracking.CHECK_CLOCKED_IN,
                    (user_id,)
                )

                if count > 0:
                    logger.warning(f"Benutzer {user_id} bereits eingestempelt")
                    return True  # Bereits eingestempelt

                # Einstempeln
                affected = conn.execute_query(
                    Queries.TimeTracking.CLOCK_IN,
                    (user_id, epc)
                )

                if affected > 0:
                    logger.info(f"Benutzer {user_id} eingestempelt")
                    return True
                else:
                    return False

        except Exception as e:
            logger.error(f"Fehler beim Einstempeln: {e}")
            return False

    def clock_out(self, user_id: int) -> bool:
        """
        Stempelt einen Benutzer aus

        Args:
            user_id: Benutzer-ID

        Returns:
            bool: True bei Erfolg
        """
        try:
            with self._get_connection() as conn:
                affected = conn.execute_query(
                    Queries.TimeTracking.CLOCK_OUT,
                    (user_id,)
                )

                if affected > 0:
                    logger.info(f"Benutzer {user_id} ausgestempelt")
                    return True
                else:
                    logger.warning(f"Keine aktive Zeiterfassung für Benutzer {user_id}")
                    return False

        except Exception as e:
            logger.error(f"Fehler beim Ausstempeln: {e}")
            return False

    def get_today_worktime(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Holt die heutige Arbeitszeit eines Benutzers

        Args:
            user_id: Benutzer-ID

        Returns:
            Dict mit Arbeitszeitdaten oder None
        """
        try:
            with self._get_connection() as conn:
                result = conn.execute_query(
                    Queries.TimeTracking.GET_TODAY_WORKTIME,
                    (user_id,)
                )

                if result and len(result) > 0:
                    row = result[0]
                    return {
                        "ein_uhrzeit": row[0],
                        "aus_uhrzeit": row[1],
                        "minuten_gearbeitet": row[2],
                        "stunden_gearbeitet": round(row[2] / 60, 2) if row[2] else 0
                    }

                return None

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Arbeitszeit: {e}")
            return None

    # ==========================================================================
    # Cache-Verwaltung
    # ==========================================================================

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Holt einen Wert aus dem Cache"""
        if key in self._cache:
            entry = self._cache[key]
            # Prüfe ob noch gültig
            if datetime.now().timestamp() - entry["timestamp"] < self._cache_ttl:
                return entry["data"]
            else:
                # Abgelaufen, entfernen
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Dict[str, Any]):
        """Speichert einen Wert im Cache"""
        self._cache[key] = {
            "data": data,
            "timestamp": datetime.now().timestamp()
        }

        # Cache-Größe begrenzen
        if len(self._cache) > 100:
            # Älteste Einträge entfernen
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k]["timestamp"]
            )
            for old_key in sorted_keys[:20]:
                del self._cache[old_key]

    def _clear_cache(self):
        """Leert den Cache"""
        self._cache.clear()

    # ==========================================================================
    # Hilfsfunktionen
    # ==========================================================================

    def _row_to_user_dict(self, row: Tuple) -> Dict[str, Any]:
        """
        Konvertiert eine Datenbankzeile in ein Benutzer-Dictionary

        Args:
            row: Datenbankzeile aus GET_BY_EPC oder GET_BY_ID Query

        Returns:
            Dict mit Benutzerdaten
        """
        return {
            "id": row[0],
            "vorname": row[1],
            "nachname": row[2],
            "benutzer": row[3],
            "benutzer_name": row[4],
            "email": row[5],
            "epc": row[6],
            "epc_hex": format(row[6], 'X') if row[6] else None,
            "status": row[7],
            "aktiv": row[7] == StatusCodes.ACTIVE,
            "registriert_am": row[8]
        }

    # ==========================================================================
    # Statistik-Funktionen
    # ==========================================================================

    def get_user_statistics(self, user_id: int,
                            start_date: datetime = None,
                            end_date: datetime = None) -> Dict[str, Any]:
        """
        Holt Statistiken für einen Benutzer

        Args:
            user_id: Benutzer-ID
            start_date: Startdatum (None = vor 30 Tagen)
            end_date: Enddatum (None = heute)

        Returns:
            Dict mit Statistiken
        """
        if not start_date:
            start_date = datetime.now().replace(hour=0, minute=0, second=0) - \
                         datetime.timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return {}

            with self._get_connection() as conn:
                # Basis-Query für Statistiken
                stats_query = """
                              SELECT COUNT(DISTINCT sk.ID)                     as AnzahlSessions, \
                                     COUNT(sp.ID)                              as AnzahlScans, \
                                     COUNT(DISTINCT sk.TagesDatum)             as ArbeitsTage, \
                                     AVG(DATEDIFF(SECOND, sk.Datum, sp.Datum)) as AvgScanZeit
                              FROM dbo.ScannKopf sk
                                       LEFT JOIN dbo.ScannPosition sp ON sk.ID = sp.ScannKopf_ID
                              WHERE sk.EPC = ?
                                AND sk.Datum BETWEEN ? AND ? \
                              """

                result = conn.execute_query(
                    stats_query,
                    (user["epc"], start_date, end_date)
                )

                stats = {
                    "user_id": user_id,
                    "user_name": user["benutzer_name"],
                    "period": {
                        "start": start_date,
                        "end": end_date
                    },
                    "sessions": 0,
                    "scans": 0,
                    "work_days": 0,
                    "avg_scan_time_seconds": 0
                }

                if result and len(result) > 0:
                    row = result[0]
                    stats.update({
                        "sessions": row[0] or 0,
                        "scans": row[1] or 0,
                        "work_days": row[2] or 0,
                        "avg_scan_time_seconds": row[3] or 0
                    })

                return stats

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Benutzerstatistiken: {e}")
            return {}

    # ==========================================================================
    # Cleanup
    # ==========================================================================

    def close(self):
        """Schließt alle Verbindungen und leert den Cache"""
        self._clear_cache()
        if self._owns_connection and self.pool:
            self.pool.close_all()