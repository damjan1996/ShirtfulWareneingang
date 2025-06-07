#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HID Listener für RFID-Reader im Keyboard Wedge Modus
====================================================

Dieser Listener empfängt die Eingaben vom RFID-Reader, der im HID-Modus
als Tastatur agiert. Die Tag-IDs werden als Tastatureingaben empfangen.
"""

import threading
import time
import logging
from typing import Optional, Callable
from pynput import keyboard

logger = logging.getLogger(__name__)


class HIDListener:
    """
    Listener für RFID-Tags im HID-Modus (Keyboard Wedge)

    Der TSHRW380BZMP sendet die Tag-ID als Tastatureingabe,
    gefolgt von einem Enter-Zeichen.
    """

    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        """
        Initialisiert den HID-Listener

        Args:
            callback: Funktion, die bei erkanntem Tag aufgerufen wird
        """
        self.callback = callback
        self.hid_data = ""
        self.listener = None
        self.is_running = False
        self.last_tag_time = 0
        self.tag_cooldown = 2.0  # Sekunden zwischen gleichen Tags
        self.last_tag = ""
        self._lock = threading.Lock()

        logger.info("HID-Listener initialisiert")

    def on_key_press(self, key):
        """
        Verarbeitet Tastatureingaben vom RFID-Reader

        Args:
            key: Die gedrückte Taste

        Returns:
            bool: False stoppt den Listener
        """
        if not self.is_running:
            return False

        try:
            # Normale Zeichen sammeln
            if hasattr(key, 'char') and key.char:
                with self._lock:
                    self.hid_data += key.char

            # Enter-Taste signalisiert Ende der Tag-ID
            elif key == keyboard.Key.enter:
                with self._lock:
                    if self.hid_data.strip():
                        tag_id = self.hid_data.strip().upper()
                        self.hid_data = ""

                        # Cooldown-Prüfung für doppelte Scans
                        current_time = time.time()
                        if (tag_id != self.last_tag or
                                current_time - self.last_tag_time > self.tag_cooldown):

                            self.last_tag = tag_id
                            self.last_tag_time = current_time

                            logger.info(f"RFID-Tag erkannt: {tag_id}")

                            # Callback in separatem Thread ausführen
                            if self.callback:
                                threading.Thread(
                                    target=self._handle_callback,
                                    args=(tag_id,),
                                    daemon=True
                                ).start()
                        else:
                            logger.debug(f"Tag {tag_id} innerhalb Cooldown ignoriert")

                    # Buffer leeren
                    self.hid_data = ""

            # Escape-Taste zum Abbrechen
            elif key == keyboard.Key.esc:
                with self._lock:
                    self.hid_data = ""

        except Exception as e:
            logger.error(f"Fehler bei Tastatureingabe: {e}")

        return True

    def _handle_callback(self, tag_id: str):
        """
        Führt den Callback in einem separaten Thread aus

        Args:
            tag_id: Die erkannte Tag-ID
        """
        try:
            if self.callback:
                self.callback(tag_id)
        except Exception as e:
            logger.error(f"Fehler im Callback für Tag {tag_id}: {e}")

    def start(self):
        """Startet den HID-Listener"""
        if self.is_running:
            logger.warning("HID-Listener läuft bereits")
            return

        self.is_running = True
        self.hid_data = ""
        self.last_tag = ""
        self.last_tag_time = 0

        # Keyboard-Listener starten
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

        logger.info("HID-Listener gestartet - warte auf RFID-Tags...")

    def stop(self):
        """Stoppt den HID-Listener"""
        self.is_running = False

        if self.listener:
            self.listener.stop()
            self.listener = None

        logger.info("HID-Listener gestoppt")

    def is_active(self) -> bool:
        """
        Prüft, ob der Listener aktiv ist

        Returns:
            bool: True wenn aktiv
        """
        return self.is_running and self.listener is not None

    def set_callback(self, callback: Callable[[str], None]):
        """
        Setzt eine neue Callback-Funktion

        Args:
            callback: Die neue Callback-Funktion
        """
        self.callback = callback
        logger.debug("Neue Callback-Funktion gesetzt")

    def set_cooldown(self, seconds: float):
        """
        Setzt die Cooldown-Zeit zwischen gleichen Tags

        Args:
            seconds: Cooldown-Zeit in Sekunden
        """
        self.tag_cooldown = max(0.0, seconds)
        logger.debug(f"Tag-Cooldown auf {self.tag_cooldown}s gesetzt")

    def clear_buffer(self):
        """Leert den internen Eingabe-Buffer"""
        with self._lock:
            self.hid_data = ""
            logger.debug("Eingabe-Buffer geleert")

    def __enter__(self):
        """Context-Manager Unterstützung"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context-Manager Unterstützung"""
        self.stop()
        return False


# Beispiel-Verwendung
if __name__ == "__main__":
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


    def tag_detected(tag_id):
        print(f"✅ Tag erkannt: {tag_id}")


    # Listener mit Context-Manager verwenden
    print("🎯 RFID-Tag Scanner gestartet")
    print("📱 Halten Sie einen RFID-Tag an den Reader...")
    print("⏹️  Drücken Sie Ctrl+C zum Beenden")

    try:
        with HIDListener(callback=tag_detected) as listener:
            # Listener läuft im Hintergrund
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n👋 Scanner beendet")