#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tag Validator für RFID-Tags
===========================

Validiert RFID-Tags gegen die Datenbank und lädt Benutzerinformationen.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TagValidator:
    """
    Validiert RFID-Tags gegen die ScannBenutzer-Tabelle
    """

    def __init__(self, db_connection=None):
        """
        Initialisiert den Tag-Validator

        Args:
            db_connection: Datenbank-Verbindung
        """
        self.connection = db_connection
        self._cache = {}  # Tag-ID -> User-Info Cache
        self._cache_timeout = 300  # 5 Minuten Cache

        logger.info("Tag-Validator initialisiert")

    def set_connection(self, connection):
        """
        Setzt eine neue Datenbank-Verbindung

        Args:
            connection: Die neue Datenbank-Verbindung
        """
        self.connection = connection
        self._cache.clear()  # Cache leeren bei neuer Verbindung
        logger.info("Datenbank-Verbindung aktualisiert")

    def test_connection(self) -> bool:
        """
        Testet die Datenbank-Verbindung

        Returns:
            bool: True wenn Verbindung aktiv
        """
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Datenbankverbindung fehlgeschlagen: {e}")
            return False

    def validate_tag(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Validiert einen RFID-Tag und lädt Benutzerinformationen

        Args:
            tag_id: Die zu validierende Tag-ID (Hex-Format)

        Returns:
            Dict mit Benutzerinformationen oder None wenn ungültig
        """
        if not self.connection:
            logger.error("Keine Datenbankverbindung")
            return None

        try:
            # Cache prüfen
            cached = self._get_from_cache(tag_id)
            if cached is not None:
                logger.debug(f"Tag {tag_id} aus Cache geladen")
                return cached

            # Tag-ID von Hex zu Decimal konvertieren
            try:
                epc_decimal = int(tag_id, 16)
            except ValueError:
                logger.error(f"Ungültige Tag-ID (kein Hex): {tag_id}")
                return None

            # Benutzer aus Datenbank laden
            cursor = self.connection.cursor()
            query = """
                    SELECT ID, \
                           Vorname, \
                           Nachname, \
                           Benutzer, \
                           BenutzerName, \
                           Email, \
                           xStatus, \
                           CAST(EPC AS BIGINT) as EPC
                    FROM dbo.ScannBenutzer
                    WHERE EPC = ? \
                      AND xStatus = 0 \
                    """

            cursor.execute(query, (epc_decimal,))
            row = cursor.fetchone()
            cursor.close()

            if row:
                user_info = {
                    'ID': row[0],
                    'Vorname': row[1] or '',
                    'Nachname': row[2] or '',
                    'Benutzer': row[3] or '',
                    'BenutzerName': row[4] or '',
                    'Email': row[5] or '',
                    'xStatus': row[6],
                    'EPC': row[7],
                    'TagID': tag_id,
                    'ValidatedAt': datetime.now()
                }

                # In Cache speichern
                self._add_to_cache(tag_id, user_info)

                logger.info(f"Tag {tag_id} validiert: {user_info['BenutzerName']}")
                return user_info
            else:
                logger.warning(f"Tag {tag_id} nicht gefunden oder inaktiv")
                # Negativen Cache-Eintrag
                self._add_to_cache(tag_id, None)
                return None

        except Exception as e:
            logger.error(f"Fehler bei Tag-Validierung: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Lädt Benutzerinformationen anhand der Benutzer-ID

        Args:
            user_id: Die Benutzer-ID

        Returns:
            Dict mit Benutzerinformationen oder None
        """
        if not self.connection:
            logger.error("Keine Datenbankverbindung")
            return None

        try:
            cursor = self.connection.cursor()
            query = """
                    SELECT ID, \
                           Vorname, \
                           Nachname, \
                           Benutzer, \
                           BenutzerName, \
                           Email, \
                           xStatus, \
                           CAST(EPC AS BIGINT) as EPC
                    FROM dbo.ScannBenutzer
                    WHERE ID = ? \
                    """

            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            cursor.close()

            if row:
                user_info = {
                    'ID': row[0],
                    'Vorname': row[1] or '',
                    'Nachname': row[2] or '',
                    'Benutzer': row[3] or '',
                    'BenutzerName': row[4] or '',
                    'Email': row[5] or '',
                    'xStatus': row[6],
                    'EPC': row[7],
                    'TagID': format(int(row[7]), 'X') if row[7] else None
                }

                logger.debug(f"Benutzer {user_id} geladen")
                return user_info
            else:
                logger.warning(f"Benutzer {user_id} nicht gefunden")
                return None

        except Exception as e:
            logger.error(f"Fehler beim Laden des Benutzers: {e}")
            return None

    def check_tag_exists(self, tag_id: str) -> bool:
        """
        Prüft, ob ein Tag in der Datenbank existiert

        Args:
            tag_id: Die zu prüfende Tag-ID (Hex-Format)

        Returns:
            bool: True wenn Tag existiert
        """
        return self.validate_tag(tag_id) is not None

    def _get_from_cache(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Holt einen Eintrag aus dem Cache

        Args:
            tag_id: Die Tag-ID

        Returns:
            Gecachte Daten oder None
        """
        if tag_id not in self._cache:
            return None

        entry = self._cache[tag_id]
        # Cache-Timeout prüfen
        if (datetime.now() - entry['cached_at']).total_seconds() > self._cache_timeout:
            del self._cache[tag_id]
            return None

        return entry['data']

    def _add_to_cache(self, tag_id: str, data: Optional[Dict[str, Any]]):
        """
        Fügt einen Eintrag zum Cache hinzu

        Args:
            tag_id: Die Tag-ID
            data: Die zu cachenden Daten
        """
        self._cache[tag_id] = {
            'data': data.copy() if data else None,
            'cached_at': datetime.now()
        }

        # Cache-Größe begrenzen (max 100 Einträge)
        if len(self._cache) > 100:
            # Älteste Einträge entfernen
            sorted_cache = sorted(
                self._cache.items(),
                key=lambda x: x[1]['cached_at']
            )
            for key, _ in sorted_cache[:20]:  # 20 älteste entfernen
                del self._cache[key]

    def clear_cache(self):
        """Leert den Cache"""
        self._cache.clear()
        logger.debug("Tag-Cache geleert")

    def get_all_active_users(self) -> list:
        """
        Lädt alle aktiven Benutzer mit RFID-Tags

        Returns:
            Liste mit Benutzerinformationen
        """
        if not self.connection:
            logger.error("Keine Datenbankverbindung")
            return []

        try:
            cursor = self.connection.cursor()
            query = """
                    SELECT ID, \
                           Vorname, \
                           Nachname, \
                           Benutzer, \
                           BenutzerName, \
                           Email, \
                           CAST(EPC AS BIGINT) as EPC
                    FROM dbo.ScannBenutzer
                    WHERE xStatus = 0 \
                      AND EPC IS NOT NULL
                    ORDER BY BenutzerName \
                    """

            cursor.execute(query)
            users = []

            for row in cursor.fetchall():
                user_info = {
                    'ID': row[0],
                    'Vorname': row[1] or '',
                    'Nachname': row[2] or '',
                    'Benutzer': row[3] or '',
                    'BenutzerName': row[4] or '',
                    'Email': row[5] or '',
                    'EPC': row[6],
                    'TagID': format(int(row[6]), 'X') if row[6] else None
                }
                users.append(user_info)

            cursor.close()
            logger.info(f"{len(users)} aktive Benutzer geladen")
            return users

        except Exception as e:
            logger.error(f"Fehler beim Laden der Benutzer: {e}")
            return []


# Test-Funktion
if __name__ == "__main__":
    import sys

    sys.path.append("../..")

    from src.database.connection import get_connection

    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Datenbank-Verbindung
        connection = get_connection()
        validator = TagValidator(connection)

        # Test: Verbindung prüfen
        print(f"Datenbankverbindung: {'✅ OK' if validator.test_connection() else '❌ Fehler'}")

        # Test: Alle aktiven Benutzer anzeigen
        print("\n📋 Aktive Benutzer mit RFID-Tags:")
        users = validator.get_all_active_users()
        for user in users:
            print(f"  - {user['BenutzerName']} (Tag: {user['TagID']})")

        # Test: Spezifischen Tag validieren
        test_tag = "53004ECD68"  # Beispiel-Tag
        print(f"\n🔍 Validiere Tag {test_tag}...")
        user_info = validator.validate_tag(test_tag)

        if user_info:
            print(f"✅ Gültiger Tag!")
            print(f"   Benutzer: {user_info['BenutzerName']}")
            print(f"   ID: {user_info['ID']}")
        else:
            print(f"❌ Ungültiger Tag")

    except Exception as e:
        print(f"❌ Fehler: {e}")