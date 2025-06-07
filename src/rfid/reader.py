#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RFID Reader Hauptklasse
=======================

Verwaltet die RFID-Tag-Erkennung und koordiniert HID-Listener
und Tag-Validierung.
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from .hid_listener import HIDListener
from .tag_validator import TagValidator

logger = logging.getLogger(__name__)


class RFIDReader:
    """
    Hauptklasse für die RFID-Funktionalität

    Koordiniert den HID-Listener und die Tag-Validierung
    gegen die Datenbank.
    """

    def __init__(self, db_connection=None):
        """
        Initialisiert den RFID-Reader

        Args:
            db_connection: Datenbank-Verbindung für Tag-Validierung
        """
        self.db_connection = db_connection
        self.hid_listener = HIDListener(callback=self._process_tag)
        self.tag_validator = TagValidator(db_connection)

        # Callbacks für verschiedene Events
        self.on_valid_tag: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_invalid_tag: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

        # Status-Tracking
        self.is_active = False
        self.last_scan_time = None
        self.scan_count = 0
        self.active_sessions = {}  # Tag-ID -> User-Info

        # Thread-Safety
        self._lock = threading.Lock()

        logger.info("RFID-Reader initialisiert")

    def _process_tag(self, tag_id: str):
        """
        Verarbeitet einen erkannten RFID-Tag

        Args:
            tag_id: Die erkannte Tag-ID
        """
        try:
            logger.info(f"Verarbeite Tag: {tag_id}")

            # Tag validieren
            user_info = self.tag_validator.validate_tag(tag_id)

            if user_info:
                # Gültiger Tag
                with self._lock:
                    self.scan_count += 1
                    self.last_scan_time = datetime.now()

                    # Session tracken
                    if tag_id not in self.active_sessions:
                        self.active_sessions[tag_id] = {
                            'user': user_info,
                            'login_time': datetime.now(),
                            'scan_count': 1
                        }
                    else:
                        self.active_sessions[tag_id]['scan_count'] += 1

                logger.info(f"Gültiger Tag: {user_info.get('BenutzerName', 'Unbekannt')}")

                # Callback ausführen
                if self.on_valid_tag:
                    threading.Thread(
                        target=self._safe_callback,
                        args=(self.on_valid_tag, user_info),
                        daemon=True
                    ).start()
            else:
                # Ungültiger Tag
                logger.warning(f"Ungültiger Tag: {tag_id}")

                if self.on_invalid_tag:
                    threading.Thread(
                        target=self._safe_callback,
                        args=(self.on_invalid_tag, tag_id),
                        daemon=True
                    ).start()

        except Exception as e:
            logger.error(f"Fehler bei Tag-Verarbeitung: {e}")

            if self.on_error:
                threading.Thread(
                    target=self._safe_callback,
                    args=(self.on_error, e),
                    daemon=True
                ).start()

    def _safe_callback(self, callback: Callable, *args):
        """
        Führt einen Callback sicher aus

        Args:
            callback: Die auszuführende Funktion
            *args: Argumente für den Callback
        """
        try:
            callback(*args)
        except Exception as e:
            logger.error(f"Fehler im Callback: {e}")

    def start(self):
        """Startet den RFID-Reader"""
        if self.is_active:
            logger.warning("RFID-Reader läuft bereits")
            return

        # Datenbank-Verbindung prüfen
        if not self.tag_validator.test_connection():
            logger.error("Keine Datenbankverbindung - Reader kann nicht gestartet werden")
            raise ConnectionError("Datenbankverbindung fehlgeschlagen")

        # HID-Listener starten
        self.hid_listener.start()
        self.is_active = True

        logger.info("RFID-Reader gestartet")

    def stop(self):
        """Stoppt den RFID-Reader"""
        if not self.is_active:
            return

        # HID-Listener stoppen
        self.hid_listener.stop()
        self.is_active = False

        # Sessions clearen
        with self._lock:
            self.active_sessions.clear()

        logger.info("RFID-Reader gestoppt")

    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Gibt alle aktiven Sessions zurück

        Returns:
            Dict mit aktiven Sessions
        """
        with self._lock:
            return self.active_sessions.copy()

    def remove_session(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Entfernt eine aktive Session

        Args:
            tag_id: Die Tag-ID der zu entfernenden Session

        Returns:
            Die entfernte Session oder None
        """
        with self._lock:
            return self.active_sessions.pop(tag_id, None)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über den Reader zurück

        Returns:
            Dict mit Statistiken
        """
        with self._lock:
            return {
                'is_active': self.is_active,
                'scan_count': self.scan_count,
                'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
                'active_sessions': len(self.active_sessions),
                'database_connected': self.tag_validator.test_connection()
            }

    def set_database_connection(self, connection):
        """
        Aktualisiert die Datenbank-Verbindung

        Args:
            connection: Die neue Datenbank-Verbindung
        """
        self.db_connection = connection
        self.tag_validator.set_connection(connection)
        logger.info("Datenbank-Verbindung aktualisiert")

    def set_callbacks(self,
                      on_valid_tag: Optional[Callable[[Dict[str, Any]], None]] = None,
                      on_invalid_tag: Optional[Callable[[str], None]] = None,
                      on_error: Optional[Callable[[Exception], None]] = None):
        """
        Setzt die Callback-Funktionen

        Args:
            on_valid_tag: Callback für gültige Tags
            on_invalid_tag: Callback für ungültige Tags
            on_error: Callback für Fehler
        """
        if on_valid_tag:
            self.on_valid_tag = on_valid_tag
        if on_invalid_tag:
            self.on_invalid_tag = on_invalid_tag
        if on_error:
            self.on_error = on_error

        logger.debug("Callbacks aktualisiert")

    def __enter__(self):
        """Context-Manager Unterstützung"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context-Manager Unterstützung"""
        self.stop()
        return False


# Test-Funktionen
def _test_reader():
    """Test-Funktion für den RFID-Reader"""
    import pyodbc
    from src.database.connection import get_connection

    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Callbacks definieren
    def on_valid_tag(user_info):
        print(f"✅ Benutzer eingeloggt: {user_info.get('BenutzerName', 'Unbekannt')}")
        print(f"   ID: {user_info.get('ID')}")
        print(f"   Vorname: {user_info.get('Vorname', '')}")
        print(f"   Nachname: {user_info.get('Nachname', '')}")

    def on_invalid_tag(tag_id):
        print(f"❌ Ungültiger Tag: {tag_id}")

    def on_error(error):
        print(f"⚠️ Fehler: {error}")

    try:
        # Datenbank-Verbindung herstellen
        print("📡 Stelle Datenbankverbindung her...")
        connection = get_connection()

        # Reader mit Context-Manager verwenden
        print("🎯 RFID-Reader gestartet")
        print("📱 Halten Sie einen RFID-Tag an den Reader...")
        print("⏹️ Drücken Sie Ctrl+C zum Beenden")

        with RFIDReader(connection) as reader:
            reader.set_callbacks(
                on_valid_tag=on_valid_tag,
                on_invalid_tag=on_invalid_tag,
                on_error=on_error
            )

            # Reader läuft im Hintergrund
            while True:
                time.sleep(1)

                # Statistiken anzeigen
                stats = reader.get_statistics()
                if stats['scan_count'] > 0:
                    print(f"\n📊 Scans: {stats['scan_count']}, "
                          f"Aktive Sessions: {stats['active_sessions']}")

    except KeyboardInterrupt:
        print("\n👋 Reader beendet")
    except Exception as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    _test_reader()