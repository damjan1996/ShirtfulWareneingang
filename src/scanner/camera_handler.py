#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camera Handler für QR-Code Scanner
==================================

Verwaltet die Kamera-Hardware und stellt Frames für das
QR-Code-Scanning bereit.
"""

import cv2
import logging
import threading
import time
from typing import Optional, Tuple, List
import numpy as np

logger = logging.getLogger(__name__)


class CameraHandler:
    """
    Verwaltet die Kamera für QR-Code-Scanning

    Features:
    - Automatische Kamera-Erkennung
    - Thread-sichere Frame-Erfassung
    - Optimierte Einstellungen für QR-Codes
    """

    def __init__(self, camera_index: int = 0):
        """
        Initialisiert den Camera Handler

        Args:
            camera_index: Index der zu verwendenden Kamera
        """
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.frame_thread = None
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()

        logger.info(f"Camera Handler initialisiert (Index: {camera_index})")

    def start(self) -> bool:
        """
        Startet die Kamera

        Returns:
            bool: True wenn erfolgreich gestartet
        """
        if self.is_running:
            logger.warning("Kamera läuft bereits")
            return True

        try:
            # Kamera öffnen
            self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap.isOpened():
                logger.error(f"Kamera {self.camera_index} konnte nicht geöffnet werden")
                return False

            # Optimale Einstellungen für QR-Code-Scanning
            self._configure_camera()

            # Test-Frame lesen
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.error(f"Kamera {self.camera_index} liefert keine Frames")
                self.cap.release()
                return False

            # Frame-Thread starten
            self.is_running = True
            self.frame_thread = threading.Thread(target=self._frame_worker, daemon=True)
            self.frame_thread.start()

            logger.info(f"Kamera {self.camera_index} erfolgreich gestartet")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Starten der Kamera: {e}")
            if self.cap:
                self.cap.release()
            return False

    def stop(self):
        """Stoppt die Kamera"""
        if not self.is_running:
            return

        self.is_running = False

        # Auf Thread warten
        if self.frame_thread:
            self.frame_thread.join(timeout=2.0)

        # Kamera freigeben
        if self.cap:
            self.cap.release()
            self.cap = None

        logger.info("Kamera gestoppt")

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Gibt den aktuellen Frame zurück

        Returns:
            numpy array mit dem Frame oder None
        """
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None

    def get_frame_size(self) -> Tuple[int, int]:
        """
        Gibt die Frame-Größe zurück

        Returns:
            Tuple (Breite, Höhe) oder (0, 0)
        """
        if self.cap and self.cap.isOpened():
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return (width, height)
        return (0, 0)

    def get_fps(self) -> float:
        """
        Gibt die aktuelle FPS-Rate zurück

        Returns:
            FPS als float
        """
        return self.fps

    def _configure_camera(self):
        """Konfiguriert optimale Kamera-Einstellungen für QR-Codes"""
        if not self.cap:
            return

        try:
            # Auflösung setzen (HD für bessere QR-Code-Erkennung)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            # Autofokus aktivieren (falls unterstützt)
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)

            # Buffer-Größe reduzieren für geringere Latenz
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # FPS auf 30 setzen
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            logger.debug("Kamera-Einstellungen konfiguriert")

        except Exception as e:
            logger.warning(f"Einige Kamera-Einstellungen konnten nicht gesetzt werden: {e}")

    def _frame_worker(self):
        """Worker-Thread für kontinuierliche Frame-Erfassung"""
        logger.debug("Frame-Worker gestartet")

        while self.is_running:
            try:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()

                    if ret and frame is not None:
                        # Frame speichern
                        with self.frame_lock:
                            self.current_frame = frame

                        # FPS berechnen
                        self.frame_count += 1
                        current_time = time.time()
                        if current_time - self.last_fps_time >= 1.0:
                            self.fps = self.frame_count / (current_time - self.last_fps_time)
                            self.frame_count = 0
                            self.last_fps_time = current_time
                    else:
                        logger.warning("Kein Frame empfangen")
                        time.sleep(0.1)
                else:
                    logger.error("Kamera nicht mehr verfügbar")
                    break

            except Exception as e:
                logger.error(f"Fehler im Frame-Worker: {e}")
                time.sleep(0.1)

        logger.debug("Frame-Worker beendet")

    @staticmethod
    def get_available_cameras() -> List[int]:
        """
        Findet alle verfügbaren Kameras

        Returns:
            Liste mit verfügbaren Kamera-Indizes
        """
        available = []

        # Teste bis zu 10 Kameras
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Test-Frame lesen
                    ret, _ = cap.read()
                    if ret:
                        available.append(i)
                    cap.release()
            except:
                pass

        logger.info(f"Gefundene Kameras: {available}")
        return available

    def take_snapshot(self, filename: str) -> bool:
        """
        Speichert den aktuellen Frame als Bild

        Args:
            filename: Pfad zum Speichern

        Returns:
            bool: True wenn erfolgreich
        """
        frame = self.get_frame()
        if frame is not None:
            try:
                cv2.imwrite(filename, frame)
                logger.info(f"Snapshot gespeichert: {filename}")
                return True
            except Exception as e:
                logger.error(f"Fehler beim Speichern des Snapshots: {e}")
        return False

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

    print("📷 Camera Handler Test")
    print("-" * 40)

    # Verfügbare Kameras finden
    cameras = CameraHandler.get_available_cameras()
    print(f"Verfügbare Kameras: {cameras}")

    if not cameras:
        print("❌ Keine Kameras gefunden!")
        exit(1)

    # Erste verfügbare Kamera verwenden
    camera_index = cameras[0]
    print(f"\n🎥 Verwende Kamera {camera_index}")

    try:
        with CameraHandler(camera_index) as camera:
            print("✅ Kamera gestartet")
            print(f"📐 Auflösung: {camera.get_frame_size()}")

            # 5 Sekunden laufen lassen
            for i in range(5):
                time.sleep(1)
                print(f"⏱️ FPS: {camera.get_fps():.1f}")

                # Frame anzeigen (optional)
                frame = camera.get_frame()
                if frame is not None:
                    cv2.imshow("Camera Test", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

            # Snapshot speichern
            camera.take_snapshot("test_snapshot.jpg")

    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        cv2.destroyAllWindows()
        print("\n✅ Test beendet")