#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR-Code Scanner mit OpenCV und pyzbar
Minimale Version für Webcam-Scanning
"""

import cv2
import threading
import time
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from PIL import Image, ImageTk
import tkinter as tk
from utils import get_logger, validate_qr_payload

logger = get_logger('QRScanner')


class QRScanner:
    def __init__(self, camera_index=0, callback=None, video_label=None):
        """
        Args:
            camera_index: Kamera-Index (0 = Standard)
            callback: Funktion die bei erkanntem QR-Code aufgerufen wird
            video_label: Tkinter Label für Video-Anzeige
        """
        self.camera_index = camera_index
        self.callback = callback
        self.video_label = video_label

        self.cap = None
        self.running = False
        self.thread = None
        self.last_scan_data = None
        self.last_scan_time = 0
        self.scan_cooldown = 2.0  # Sekunden zwischen gleichen Scans

    def start(self):
        """Scanner starten"""
        if self.running:
            return

        try:
            # Kamera öffnen
            self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap.isOpened():
                raise Exception("Kamera konnte nicht geöffnet werden")

            # Kamera-Einstellungen optimieren
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            self.running = True
            self.thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.thread.start()

            logger.info(f"QR-Scanner gestartet (Kamera {self.camera_index})")

        except Exception as e:
            logger.error(f"Fehler beim Starten des QR-Scanners: {e}")
            self.release()
            raise

    def stop(self):
        """Scanner stoppen"""
        self.running = False

        if self.thread:
            self.thread.join(timeout=2.0)

        self.release()
        logger.info("QR-Scanner gestoppt")

    def release(self):
        """Kamera freigeben"""
        if self.cap:
            self.cap.release()
            self.cap = None

    def _scan_loop(self):
        """Haupt-Scan-Schleife"""
        frame_count = 0

        while self.running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("Kein Frame erhalten")
                    time.sleep(0.1)
                    continue

                # Frame verarbeiten
                processed_frame = self._process_frame(frame)

                # QR-Codes suchen (nicht bei jedem Frame)
                if frame_count % 5 == 0:  # Jeden 5. Frame scannen
                    self._detect_qr_codes(frame)

                # Video anzeigen wenn Label vorhanden
                if self.video_label:
                    self._update_video_display(processed_frame)

                frame_count += 1

                # CPU schonen
                time.sleep(0.03)  # ~30 FPS

            except Exception as e:
                logger.error(f"Fehler in Scan-Schleife: {e}")
                time.sleep(0.1)

    def _process_frame(self, frame):
        """Frame vorverarbeiten"""
        # Größe anpassen für Anzeige
        display_frame = cv2.resize(frame, (640, 480))

        # Text overlay
        cv2.putText(
            display_frame,
            "QR-Code Scanner aktiv",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        # Fadenkreuz in der Mitte
        height, width = display_frame.shape[:2]
        center_x, center_y = width // 2, height // 2

        cv2.line(display_frame, (center_x - 50, center_y), (center_x + 50, center_y), (0, 255, 0), 2)
        cv2.line(display_frame, (center_x, center_y - 50), (center_x, center_y + 50), (0, 255, 0), 2)

        return display_frame

    def _detect_qr_codes(self, frame):
        """QR-Codes im Frame erkennen"""
        try:
            # Graubild für bessere Erkennung
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # QR-Codes dekodieren (nur QR-Codes, keine anderen Barcode-Typen)
            decoded_objects = pyzbar.decode(gray, symbols=[ZBarSymbol.QRCODE])

            for obj in decoded_objects:
                # Daten extrahieren
                qr_data = obj.data.decode('utf-8', errors='ignore')

                # Cooldown prüfen
                current_time = time.time()
                if (qr_data == self.last_scan_data and
                        current_time - self.last_scan_time < self.scan_cooldown):
                    continue

                # Validierung
                validated = validate_qr_payload(qr_data)
                if validated:
                    self.last_scan_data = qr_data
                    self.last_scan_time = current_time

                    logger.info(f"QR-Code erkannt: {qr_data[:100]}...")

                    # Callback aufrufen
                    if self.callback:
                        threading.Thread(
                            target=self.callback,
                            args=(qr_data,),
                            daemon=True
                        ).start()

        except Exception as e:
            logger.error(f"Fehler bei QR-Erkennung: {e}")

    def _update_video_display(self, frame):
        """Video im Tkinter Label anzeigen"""
        try:
            # BGR zu RGB konvertieren
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Zu PIL Image konvertieren
            image = Image.fromarray(rgb_frame)

            # Zu PhotoImage konvertieren
            photo = ImageTk.PhotoImage(image=image)

            # Label aktualisieren
            self.video_label.configure(image=photo)
            self.video_label.image = photo  # Referenz behalten

        except Exception as e:
            logger.error(f"Fehler bei Video-Anzeige: {e}")

    def validate_payload(self, payload):
        """Öffentliche Methode zur Payload-Validierung"""
        return validate_qr_payload(payload)


# Test-Funktion
def test_scanner():
    """Test-Funktion für QR-Scanner"""
    print("📸 QR-Scanner Test")
    print("Halten Sie QR-Codes vor die Kamera...")
    print("Drücken Sie 'q' zum Beenden\n")

    def on_qr_code(data):
        print(f"✅ QR-Code erkannt:")
        print(f"   Daten: {data}")
        print(f"   Zeit: {time.strftime('%H:%M:%S')}")
        validated = validate_qr_payload(data)
        print(f"   Typ: {validated['type']}")
        if validated['type'] != 'text':
            print(f"   Parsed: {validated['data']}")
        print("-" * 60)

    scanner = QRScanner(camera_index=0, callback=on_qr_code)

    try:
        scanner.start()

        # Einfaches OpenCV Fenster für Test
        print("OpenCV Fenster öffnet sich...")
        while scanner.running:
            if scanner.cap and scanner.cap.isOpened():
                ret, frame = scanner.cap.read()
                if ret:
                    cv2.imshow('QR Scanner Test', frame)

                    # 'q' zum Beenden
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

            time.sleep(0.03)

    except KeyboardInterrupt:
        print("\n⏹️  Test unterbrochen")
    finally:
        scanner.stop()
        cv2.destroyAllWindows()
        print("Test beendet")


if __name__ == "__main__":
    test_scanner()