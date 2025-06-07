#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR-Code Scanner Hauptklasse
===========================

Koordiniert Kamera und Decoder für kontinuierliches
QR-Code-Scanning.
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import cv2
import numpy as np

from .camera_handler import CameraHandler
from .decoder import QRDecoder

logger = logging.getLogger(__name__)


class QRScanner:
    """
    Hauptklasse für QR-Code-Scanning

    Features:
    - Kontinuierliches Scanning
    - Duplikat-Erkennung
    - Callback-System für erkannte Codes
    - Statistik-Tracking
    """

    def __init__(self, camera_index: int = 0):
        """
        Initialisiert den QR-Scanner

        Args:
            camera_index: Index der zu verwendenden Kamera
        """
        self.camera_handler = CameraHandler(camera_index)
        self.decoder = QRDecoder()

        # Callbacks
        self.on_code_detected: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

        # Status
        self.is_scanning = False
        self.scan_thread = None
        self.scan_count = 0
        self.last_scan_time = None

        # Duplikat-Verwaltung
        self.recent_codes = {}  # raw_data -> timestamp
        self.duplicate_timeout = 5.0  # Sekunden

        # Thread-Safety
        self._lock = threading.Lock()

        # Performance-Tracking
        self.fps = 0
        self.last_fps_time = time.time()
        self.frame_count = 0

        logger.info("QR-Scanner initialisiert")

    def start(self) -> bool:
        """
        Startet den QR-Scanner

        Returns:
            bool: True wenn erfolgreich gestartet
        """
        if self.is_scanning:
            logger.warning("Scanner läuft bereits")
            return True

        # Kamera starten
        if not self.camera_handler.start():
            logger.error("Kamera konnte nicht gestartet werden")
            return False

        # Scan-Thread starten
        self.is_scanning = True
        self.scan_thread = threading.Thread(target=self._scan_worker, daemon=True)
        self.scan_thread.start()

        logger.info("QR-Scanner gestartet")
        return True

    def stop(self):
        """Stoppt den QR-Scanner"""
        if not self.is_scanning:
            return

        # Scanning stoppen
        self.is_scanning = False

        # Auf Thread warten
        if self.scan_thread:
            self.scan_thread.join(timeout=2.0)

        # Kamera stoppen
        self.camera_handler.stop()

        logger.info("QR-Scanner gestoppt")

    def _scan_worker(self):
        """Worker-Thread für kontinuierliches Scanning"""
        logger.debug("Scan-Worker gestartet")

        while self.is_scanning:
            try:
                # Frame abrufen
                frame = self.camera_handler.get_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue

                # QR-Codes dekodieren
                detected_codes = self.decoder.decode_frame(frame)

                # Jeden erkannten Code verarbeiten
                for code_data in detected_codes:
                    self._process_detected_code(code_data)

                # FPS tracken
                self._update_fps()

                # CPU-Last reduzieren
                time.sleep(0.01)

            except Exception as e:
                logger.error(f"Fehler im Scan-Worker: {e}")
                if self.on_error:
                    self._safe_callback(self.on_error, e)
                time.sleep(0.1)

        logger.debug("Scan-Worker beendet")

    def _process_detected_code(self, code_data: Dict[str, Any]):
        """
        Verarbeitet einen erkannten QR-Code

        Args:
            code_data: Die dekodierten Daten
        """
        raw_data = code_data.get('raw_data', '')

        # Duplikat-Check
        if self._is_duplicate(raw_data):
            logger.debug(f"Duplikat ignoriert: {raw_data[:50]}...")
            return

        # Als verarbeitet markieren
        with self._lock:
            self.recent_codes[raw_data] = time.time()
            self.scan_count += 1
            self.last_scan_time = datetime.now()

        logger.info(f"QR-Code erkannt: {code_data.get('auftrags_nr', 'N/A')} / "
                    f"{code_data.get('paket_nr', 'N/A')}")

        # Callback ausführen
        if self.on_code_detected:
            self._safe_callback(self.on_code_detected, code_data)

        # Alte Einträge aufräumen
        self._cleanup_recent_codes()

    def _is_duplicate(self, raw_data: str) -> bool:
        """
        Prüft, ob ein Code kürzlich bereits erkannt wurde

        Args:
            raw_data: Die Rohdaten des QR-Codes

        Returns:
            bool: True wenn Duplikat
        """
        with self._lock:
            if raw_data in self.recent_codes:
                last_time = self.recent_codes[raw_data]
                if time.time() - last_time < self.duplicate_timeout:
                    return True
        return False

    def _cleanup_recent_codes(self):
        """Entfernt alte Einträge aus der Duplikat-Liste"""
        current_time = time.time()
        with self._lock:
            self.recent_codes = {
                code: timestamp
                for code, timestamp in self.recent_codes.items()
                if current_time - timestamp < self.duplicate_timeout
            }

    def _update_fps(self):
        """Aktualisiert die FPS-Berechnung"""
        self.frame_count += 1
        current_time = time.time()

        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time

    def _safe_callback(self, callback: Callable, *args):
        """
        Führt einen Callback sicher aus

        Args:
            callback: Die auszuführende Funktion
            *args: Argumente für den Callback
        """
        try:
            threading.Thread(
                target=callback,
                args=args,
                daemon=True
            ).start()
        except Exception as e:
            logger.error(f"Fehler im Callback: {e}")

    def get_frame_with_overlay(self) -> Optional[np.ndarray]:
        """
        Gibt den aktuellen Frame mit QR-Code-Markierungen zurück

        Returns:
            Frame mit Overlay oder None
        """
        frame = self.camera_handler.get_frame()
        if frame is None:
            return None

        # QR-Code-Positionen einzeichnen
        for position in self.decoder.get_last_positions():
            cv2.polylines(frame, [position], True, (0, 255, 0), 2)

        # Statistiken einblenden
        self._draw_statistics(frame)

        return frame

    def _draw_statistics(self, frame: np.ndarray):
        """Zeichnet Statistiken auf den Frame"""
        height, width = frame.shape[:2]

        # Text-Eigenschaften
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.6
        thickness = 1
        color = (0, 255, 0)

        # FPS anzeigen
        fps_text = f"FPS: {self.fps:.1f}"
        cv2.putText(frame, fps_text, (10, 25), font, scale, color, thickness)

        # Scan-Zähler
        scan_text = f"Scans: {self.scan_count}"
        cv2.putText(frame, scan_text, (10, 50), font, scale, color, thickness)

        # Kamera-Info
        cam_size = self.camera_handler.get_frame_size()
        size_text = f"Size: {cam_size[0]}x{cam_size[1]}"
        cv2.putText(frame, size_text, (10, 75), font, scale, color, thickness)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Scanner-Statistiken zurück

        Returns:
            Dict mit Statistiken
        """
        with self._lock:
            return {
                'is_scanning': self.is_scanning,
                'scan_count': self.scan_count,
                'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
                'fps': self.fps,
                'camera_fps': self.camera_handler.get_fps(),
                'camera_size': self.camera_handler.get_frame_size(),
                'recent_codes': len(self.recent_codes),
                'history_size': len(self.decoder.decode_history)
            }

    def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Gibt die Scan-Historie zurück

        Args:
            limit: Maximale Anzahl Einträge

        Returns:
            Liste mit historischen Scans
        """
        return self.decoder.get_history(limit)

    def set_callbacks(self,
                      on_code_detected: Optional[Callable[[Dict[str, Any]], None]] = None,
                      on_error: Optional[Callable[[Exception], None]] = None):
        """
        Setzt die Callback-Funktionen

        Args:
            on_code_detected: Callback für erkannte QR-Codes
            on_error: Callback für Fehler
        """
        if on_code_detected:
            self.on_code_detected = on_code_detected
        if on_error:
            self.on_error = on_error

        logger.debug("Callbacks aktualisiert")

    def set_duplicate_timeout(self, seconds: float):
        """
        Setzt das Timeout für Duplikat-Erkennung

        Args:
            seconds: Timeout in Sekunden
        """
        self.duplicate_timeout = max(0.0, seconds)
        logger.debug(f"Duplikat-Timeout auf {self.duplicate_timeout}s gesetzt")

    def scan_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Scannt ein einzelnes Bild nach QR-Codes

        Args:
            image_path: Pfad zum Bild

        Returns:
            Liste mit gefundenen QR-Codes
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Bild konnte nicht geladen werden: {image_path}")
                return []

            return self.decoder.decode_frame(image)

        except Exception as e:
            logger.error(f"Fehler beim Scannen des Bildes: {e}")
            return []

    def __enter__(self):
        """Context-Manager Support"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context-Manager Support"""
        self.stop()
        return False


# Test-Funktion
if __name__ == "__main__":
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


    def on_code_detected(code_data):
        print(f"\n✅ QR-Code erkannt!")
        print(f"   Format: {code_data.get('format', 'unknown')}")
        print(f"   Auftrag: {code_data.get('auftrags_nr', '-')}")
        print(f"   Paket: {code_data.get('paket_nr', '-')}")
        print(f"   Kunde: {code_data.get('kunden_name', '-')}")
        if code_data.get('zusatz_info'):
            print(f"   Zusatz: {code_data.get('zusatz_info')}")


    def on_error(error):
        print(f"⚠️ Fehler: {error}")


    print("📷 QR-Code Scanner Test")
    print("=" * 50)

    # Verfügbare Kameras anzeigen
    cameras = CameraHandler.get_available_cameras()
    print(f"Verfügbare Kameras: {cameras}")

    if not cameras:
        print("❌ Keine Kameras gefunden!")
        exit(1)

    camera_index = cameras[0]
    print(f"Verwende Kamera {camera_index}")
    print("\n🎯 Scanner gestartet - halten Sie QR-Codes vor die Kamera")
    print("⏹️ Drücken Sie 'q' zum Beenden")

    try:
        with QRScanner(camera_index) as scanner:
            scanner.set_callbacks(
                on_code_detected=on_code_detected,
                on_error=on_error
            )

            # Live-Anzeige
            while True:
                frame = scanner.get_frame_with_overlay()
                if frame is not None:
                    cv2.imshow("QR-Scanner", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    # Statistiken anzeigen
                    stats = scanner.get_statistics()
                    print(f"\n📊 Statistiken:")
                    for k, v in stats.items():
                        print(f"   {k}: {v}")

    except KeyboardInterrupt:
        print("\n⏹️ Scanner gestoppt")
    finally:
        cv2.destroyAllWindows()