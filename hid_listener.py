#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HID Keyboard Listener für RFID Reader
Verbesserte Version mit intelligenter Filterung
"""

from pynput import keyboard
import threading
import time
import re
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
        self.last_key_time = 0
        self.input_timeout = 0.5  # Max Zeit zwischen Zeichen eines Tags
        self.max_buffer_length = 15  # Maximale Buffer-Länge

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
        logger.info("HID Listener gestartet - intelligente Filterung aktiv")

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
            current_time = time.time()

            # Timeout-Check: Buffer leeren wenn zu lange keine Eingabe
            if self.buffer and (current_time - self.last_key_time) > self.input_timeout:
                if len(self.buffer) >= 8:  # Versuche Verarbeitung vor Timeout
                    logger.debug(f"Input-Timeout, versuche Verarbeitung: '{self.buffer}'")
                    self._process_buffer()
                else:
                    logger.debug(f"Input-Timeout, Buffer geleert: '{self.buffer}'")
                    self.buffer = ""

            self.last_key_time = current_time

            # Normale Zeichen (nur Hex-Zeichen und Zahlen akzeptieren)
            if hasattr(key, 'char') and key.char:
                char = key.char.upper()

                # Nur Hex-Zeichen akzeptieren (0-9, A-F)
                if re.match(r'[0-9A-F]', char):
                    self.buffer += char

                    # Buffer-Länge begrenzen
                    if len(self.buffer) > self.max_buffer_length:
                        self.buffer = self.buffer[-self.max_buffer_length:]
                        logger.debug(f"Buffer gekürzt auf {self.max_buffer_length} Zeichen")

                    logger.debug(f"Buffer: '{self.buffer}' (Länge: {len(self.buffer)})")

                else:
                    # Ungültiges Zeichen - prüfe ob Buffer verarbeitet werden soll
                    if len(self.buffer) >= 8:  # Mindestlänge für Tag
                        logger.debug(f"Ungültiges Zeichen '{char}' nach Buffer '{self.buffer}' - versuche Verarbeitung")
                        self._process_buffer()
                    else:
                        # Buffer leeren bei ungültigen Zeichen und kurzen Buffern
                        if self.buffer:
                            logger.debug(f"Buffer wegen ungültigem Zeichen geleert: '{self.buffer}' + '{char}'")
                        self.buffer = ""

            # Enter-Taste = Ende der Eingabe
            elif key == keyboard.Key.enter:
                logger.debug(f"Enter gedrückt, Buffer: '{self.buffer}'")
                self._process_buffer()

            # Bei anderen Sondertasten Buffer verarbeiten oder leeren
            elif key in [keyboard.Key.esc, keyboard.Key.tab, keyboard.Key.space]:
                if len(self.buffer) >= 8:  # Versuche Verarbeitung vor dem Leeren
                    logger.debug(f"Sondertaste {key} nach längerem Buffer - versuche Verarbeitung")
                    self._process_buffer()
                else:
                    if self.buffer:
                        logger.debug(f"Buffer wegen Sondertaste geleert: '{self.buffer}'")
                    self.buffer = ""

        except Exception as e:
            logger.error(f"Fehler bei Tastenverarbeitung: {e}")

    def _on_key_release(self, key):
        """Wird bei Taste loslassen aufgerufen (nicht verwendet)"""
        pass

    def _process_buffer(self):
        """Verarbeitet den Buffer"""
        if not self.buffer:
            return

        # Trimmen und in Großbuchstaben
        tag_id = self.buffer.strip().upper()
        original_buffer = self.buffer
        self.buffer = ""

        # Mindestlänge prüfen
        if len(tag_id) < 8:
            logger.debug(f"Tag zu kurz, ignoriert: '{tag_id}' (Länge: {len(tag_id)})")
            return

        # Maximallänge prüfen
        if len(tag_id) > 12:
            logger.debug(f"Tag zu lang, ignoriert: '{tag_id}' (Länge: {len(tag_id)})")
            return

        # Zeit-Check (Doppel-Scans vermeiden)
        current_time = time.time()
        if current_time - self.last_scan_time < self.min_scan_interval:
            logger.debug(f"Scan zu schnell, ignoriert: {tag_id}")
            return

        # Validierung
        if not validate_tag_id(tag_id):
            logger.warning(f"Ungültiges Tag-Format: '{tag_id}' (Original: '{original_buffer}')")
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

    def get_buffer_info(self):
        """Debug-Information über aktuellen Buffer"""
        return {
            'buffer': self.buffer,
            'buffer_length': len(self.buffer),
            'last_key_time': self.last_key_time,
            'running': self.running,
            'last_scan_time': self.last_scan_time
        }

    def clear_buffer(self):
        """Leert den Buffer manuell"""
        old_buffer = self.buffer
        self.buffer = ""
        if old_buffer:
            logger.debug(f"Buffer manuell geleert: '{old_buffer}'")

    def set_min_scan_interval(self, interval):
        """Setzt das minimale Interval zwischen Scans"""
        old_interval = self.min_scan_interval
        self.min_scan_interval = max(0.1, min(10.0, interval))  # Zwischen 0.1 und 10 Sekunden
        logger.info(f"Scan-Interval geändert: {old_interval}s → {self.min_scan_interval}s")


# Test-Funktion
def test_listener():
    """Test-Funktion für HID Listener"""
    print("🔍 HID Listener Test (Verbesserte Version)")
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
        # Debug-Output alle 5 Sekunden
        last_debug = 0
        while True:
            time.sleep(1)
            current_time = time.time()

            if current_time - last_debug > 5:
                info = listener.get_buffer_info()
                if info['buffer']:
                    print(f"Debug - Aktueller Buffer: '{info['buffer']}' (Länge: {info['buffer_length']})")
                last_debug = current_time

    except KeyboardInterrupt:
        print("\n⏹️  Test beendet")
    finally:
        listener.stop()


if __name__ == "__main__":
    test_listener()