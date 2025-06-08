#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HID Keyboard Listener für RFID Reader
Liest RFID-Tags die als Keyboard-Input kommen
"""

from pynput import keyboard
import threading
import time
from utils import get_logger, validate_tag_id

logger = get_logger('HIDListener')


class HIDListener:
    def __init__(self, callback=None):
        """
        Args:
            callback: Funktion die bei erkanntem Tag aufgerufen wird
        """
        self.callback = callback
        self.buffer = ""
        self.listener = None
        self.running = False
        self.last_scan_time = 0
        self.min_scan_interval = 1.0  # Mindestabstand zwischen Scans in Sekunden

    def start(self):
        """Startet den Keyboard Listener"""
        if self.running:
            return

        self.running = True
        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.listener.start()
        logger.info("HID Listener gestartet")

    def stop(self):
        """Stoppt den Keyboard Listener"""
        self.running = False
        if self.listener:
            self.listener.stop()
            self.listener = None
        logger.info("HID Listener gestoppt")

    def _on_key_press(self, key):
        """Verarbeitet Tastenanschläge"""
        if not self.running:
            return False

        try:
            # Normale Zeichen
            if hasattr(key, 'char') and key.char:
                self.buffer += key.char

            # Enter-Taste = Ende der Eingabe
            elif key == keyboard.Key.enter:
                self._process_buffer()

            # Bei anderen Sondertasten Buffer leeren
            elif key in [keyboard.Key.esc, keyboard.Key.tab]:
                self.buffer = ""

        except Exception as e:
            logger.error(f"Fehler bei Tastenverarbeitung: {e}")

    def _on_key_release(self, key):
        """Wird bei Taste loslassen aufgerufen (nicht verwendet)"""
        pass

    def _process_buffer(self):
        """Verarbeitet den Buffer wenn Enter gedrückt wurde"""
        if not self.buffer:
            return

        # Trimmen und in Großbuchstaben
        tag_id = self.buffer.strip().upper()
        self.buffer = ""

        # Zeit-Check (Doppel-Scans vermeiden)
        current_time = time.time()
        if current_time - self.last_scan_time < self.min_scan_interval:
            logger.debug(f"Scan zu schnell, ignoriert: {tag_id}")
            return

        # Validierung
        if not validate_tag_id(tag_id):
            logger.warning(f"Ungültiges Tag-Format: {tag_id}")
            return

        # Callback aufrufen
        self.last_scan_time = current_time
        logger.info(f"RFID Tag erkannt: {tag_id}")

        if self.callback:
            # In separatem Thread ausführen um Listener nicht zu blockieren
            threading.Thread(
                target=self.callback,
                args=(tag_id,),
                daemon=True
            ).start()


# Test-Funktion
def test_listener():
    """Test-Funktion für HID Listener"""
    print("🔍 HID Listener Test")
    print("Halten Sie RFID-Tags an den Reader...")
    print("Drücken Sie Ctrl+C zum Beenden\n")

    def on_tag(tag_id):
        print(f"✅ Tag erkannt: {tag_id}")
        print(f"   Decimal: {int(tag_id, 16)}")
        print(f"   Zeit: {time.strftime('%H:%M:%S')}")
        print("-" * 40)

    listener = HIDListener(callback=on_tag)
    listener.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test beendet")
    finally:
        listener.stop()


if __name__ == "__main__":
    test_listener()