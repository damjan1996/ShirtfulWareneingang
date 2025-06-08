#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR-Code Scanner mit OpenCV und pyzbar
Optimierte finale Version für schnelleren Start und bessere Performance
"""

import cv2
import threading
import time
import os
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
        self.scan_cooldown = 0.5  # Reduziert auf 0.5 Sekunden für bessere Responsivität

        # Performance-Optimierungen
        self.frame_skip = 3  # Jeden 3. Frame für QR-Erkennung verwenden
        self.frame_count = 0
        self.detection_running = False

    def start(self):
        """Scanner starten (optimiert für schnelleren Start)"""
        if self.running:
            return

        try:
            # Bestimme Kamera-Backend
            from config import APP_CONFIG
            backend = APP_CONFIG.get('CAMERA_BACKEND', 'DSHOW').upper()

            logger.info(f"Starte QR-Scanner mit Backend: {backend}")

            # Kamera öffnen mit optimiertem Backend
            if backend == 'DSHOW' and os.name == 'nt':  # Windows DirectShow
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            elif backend == 'V4L2':  # Linux Video4Linux2
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            else:  # AUTO - OpenCV wählt automatisch
                self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap.isOpened():
                raise Exception("Kamera konnte nicht geöffnet werden")

            # Optimierte Kamera-Einstellungen für schnelleren Start
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduziert Latenz

            # Autofocus und Autoexposure deaktivieren für konstante Performance
            try:
                self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual mode
            except:
                pass  # Nicht alle Kameras unterstützen diese Einstellungen

            self.running = True
            self.thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.thread.start()

            logger.info(f"QR-Scanner erfolgreich gestartet (Kamera {self.camera_index}, Backend: {backend})")

        except Exception as e:
            logger.error(f"Fehler beim Starten des QR-Scanners: {e}")
            self.release()
            raise

    def stop(self):
        """Scanner stoppen"""
        logger.info("Stoppe QR-Scanner...")
        self.running = False
        self.detection_running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.0)

        self.release()
        logger.info("QR-Scanner gestoppt")

    def release(self):
        """Kamera freigeben"""
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None

    def _scan_loop(self):
        """Haupt-Scan-Schleife (optimiert)"""
        logger.debug("QR-Scanner Hauptschleife gestartet")

        while self.running:
            try:
                if not self.cap or not self.cap.isOpened():
                    logger.warning("Kamera nicht verfügbar")
                    time.sleep(0.1)
                    continue

                ret, frame = self.cap.read()
                if not ret or frame is None:
                    logger.warning("Kein Frame erhalten")
                    time.sleep(0.1)
                    continue

                # Frame verarbeiten für Anzeige
                display_frame = self._process_frame(frame.copy())

                # QR-Codes suchen (nur jeden N-ten Frame für Performance)
                self.frame_count += 1
                if self.frame_count % self.frame_skip == 0 and not self.detection_running:
                    self.detection_running = True
                    # QR-Erkennung in separatem Thread für bessere Performance
                    threading.Thread(
                        target=self._detect_qr_codes_async,
                        args=(frame.copy(),),
                        daemon=True
                    ).start()

                # Video anzeigen wenn Label vorhanden
                if self.video_label and self.running:
                    self._update_video_display(display_frame)

                # CPU schonen
                time.sleep(0.033)  # ~30 FPS

            except Exception as e:
                logger.error(f"Fehler in Scan-Schleife: {e}")
                time.sleep(0.1)

        logger.debug("QR-Scanner Hauptschleife beendet")

    def _detect_qr_codes_async(self, frame):
        """QR-Codes asynchron erkennen"""
        try:
            self._detect_qr_codes(frame)
        finally:
            self.detection_running = False

    def _process_frame(self, frame):
        """Frame für Anzeige verarbeiten"""
        try:
            # Größe anpassen für Anzeige
            display_frame = cv2.resize(frame, (640, 480))

            # Status-Text overlay
            status_text = "QR-Code Scanner aktiv"
            if self.last_scan_data:
                time_since_scan = time.time() - self.last_scan_time
                if time_since_scan < 2.0:  # 2 Sekunden nach letztem Scan
                    status_text = "QR-Code erkannt!"

            cv2.putText(
                display_frame,
                status_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            # Scan-Bereich markieren (Fadenkreuz in der Mitte)
            height, width = display_frame.shape[:2]
            center_x, center_y = width // 2, height // 2

            # Fadenkreuz
            cv2.line(display_frame, (center_x - 50, center_y), (center_x + 50, center_y), (0, 255, 0), 2)
            cv2.line(display_frame, (center_x, center_y - 50), (center_x, center_y + 50), (0, 255, 0), 2)

            # Scan-Rahmen
            cv2.rectangle(display_frame, (center_x - 100, center_y - 100), (center_x + 100, center_y + 100),
                          (0, 255, 0), 1)

            return display_frame

        except Exception as e:
            logger.error(f"Fehler bei Frame-Verarbeitung: {e}")
            return frame

    def _detect_qr_codes(self, frame):
        """QR-Codes im Frame erkennen"""
        try:
            # Graubild für bessere Erkennung
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Kontrast verbessern für bessere QR-Erkennung
            gray = cv2.equalizeHist(gray)

            # QR-Codes dekodieren (nur QR-Codes, keine anderen Barcode-Typen)
            decoded_objects = pyzbar.decode(gray, symbols=[ZBarSymbol.QRCODE])

            for obj in decoded_objects:
                # Daten extrahieren
                qr_data = obj.data.decode('utf-8', errors='ignore')

                # Cooldown prüfen (gegen zu häufige gleiche Scans)
                current_time = time.time()
                if (qr_data == self.last_scan_data and
                        current_time - self.last_scan_time < self.scan_cooldown):
                    logger.debug(f"QR-Code Cooldown aktiv für: {qr_data[:30]}...")
                    continue

                # Validierung
                validated = validate_qr_payload(qr_data)
                if validated and validated.get('valid', True):
                    self.last_scan_data = qr_data
                    self.last_scan_time = current_time

                    logger.info(f"QR-Code erkannt: {qr_data[:100]}...")
                    logger.debug(f"QR-Code Validierung: {validated.get('type', 'unknown')}")

                    # Callback aufrufen
                    if self.callback:
                        logger.debug("Rufe QR-Code Callback auf...")
                        try:
                            self.callback(qr_data)
                        except Exception as e:
                            logger.error(f"Fehler im QR-Code Callback: {e}")
                    else:
                        logger.warning("Kein Callback für QR-Code definiert")
                else:
                    logger.debug(f"QR-Code Validierung fehlgeschlagen: {qr_data[:50]}...")

        except Exception as e:
            logger.error(f"Fehler bei QR-Erkennung: {e}")
            import traceback
            logger.debug(f"QR-Erkennung Traceback: {traceback.format_exc()}")

    def _update_video_display(self, frame):
        """Video im Tkinter Label anzeigen"""
        try:
            if not self.video_label or not self.running:
                return

            # BGR zu RGB konvertieren
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Zu PIL Image konvertieren
            image = Image.fromarray(rgb_frame)

            # Zu PhotoImage konvertieren
            photo = ImageTk.PhotoImage(image=image)

            # Label aktualisieren (Thread-sicher)
            def update_label():
                try:
                    if self.video_label and self.running:
                        self.video_label.configure(image=photo)
                        self.video_label.image = photo  # Referenz behalten
                except:
                    pass

            # Update im Hauptthread ausführen
            if hasattr(self.video_label, 'after'):
                self.video_label.after(0, update_label)

        except Exception as e:
            logger.debug(f"Fehler bei Video-Anzeige: {e}")

    def validate_payload(self, payload):
        """Öffentliche Methode zur Payload-Validierung"""
        return validate_qr_payload(payload)

    def get_stats(self):
        """Gibt Scanner-Statistiken zurück"""
        return {
            'running': self.running,
            'camera_index': self.camera_index,
            'last_scan_time': self.last_scan_time,
            'scan_cooldown': self.scan_cooldown,
            'frame_count': self.frame_count,
            'frame_skip': self.frame_skip,
            'detection_running': self.detection_running
        }

    def set_scan_cooldown(self, cooldown):
        """Setzt das Scan-Cooldown"""
        old_cooldown = self.scan_cooldown
        self.scan_cooldown = max(0.1, min(5.0, cooldown))  # Zwischen 0.1 und 5 Sekunden
        logger.info(f"Scan-Cooldown geändert: {old_cooldown}s → {self.scan_cooldown}s")


# Test-Funktion
def test_scanner():
    """Test-Funktion für QR-Scanner"""
    print("📸 QR-Scanner Test (Optimierte Version)")
    print("Halten Sie QR-Codes vor die Kamera...")
    print("Drücken Sie 'q' zum Beenden\n")

    def on_qr_code(data):
        print(f"✅ QR-Code erkannt:")
        print(f"   Daten: {data}")
        print(f"   Zeit: {time.strftime('%H:%M:%S')}")
        validated = validate_qr_payload(data)
        if validated:
            print(f"   Typ: {validated.get('type', 'unknown')}")
            if validated.get('type') != 'text' and validated.get('data'):
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