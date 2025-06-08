#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR-Code Scanner mit OpenCV und pyzbar - Multi-Scanner Version
Optimiert für paralleles Scannen mit mehreren Kameras
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


class MultiQRScanner:
    """Multi-Scanner Manager für parallele QR-Code Erkennung"""

    def __init__(self, camera_indices, shared_callback=None, primary_video_label=None):
        """
        Args:
            camera_indices: Liste der Kamera-Indizes [0, 1, 2, ...]
            shared_callback: Gemeinsame Callback-Funktion für alle Scanner
            primary_video_label: Video-Label für primäre Kamera
        """
        self.camera_indices = camera_indices
        self.shared_callback = shared_callback
        self.primary_video_label = primary_video_label

        self.scanners = []
        self.running = False

        # Multi-Scanner Statistiken
        self.total_scans = 0
        self.scanner_stats = {}

        # Last scan tracking für Cross-Scanner Duplikat-Verhinderung
        self.last_scans = {}  # {payload: {'time': timestamp, 'scanner_id': id}}
        self.cross_scanner_cooldown = 2.0  # Sekunden zwischen gleichen Codes von verschiedenen Scannern

        logger.info(f"MultiQRScanner initialisiert für Kameras: {camera_indices}")

    def start_all(self):
        """Startet alle Scanner"""
        if self.running:
            return

        self.running = True
        logger.info("Starte alle QR-Scanner...")

        for i, camera_index in enumerate(self.camera_indices):
            try:
                # Video-Label nur für primäre Kamera
                video_label = self.primary_video_label if i == 0 else None

                scanner = QRScanner(
                    camera_index=camera_index,
                    callback=lambda payload, scanner_id=camera_index: self._on_scan_detected(payload, scanner_id),
                    video_label=video_label,
                    scanner_id=f"Scanner_{camera_index}"
                )

                scanner.start()
                self.scanners.append(scanner)

                # Statistiken initialisieren
                self.scanner_stats[camera_index] = {
                    'scans': 0,
                    'last_scan': None,
                    'status': 'active',
                    'start_time': time.time()
                }

                logger.info(f"Scanner {camera_index} erfolgreich gestartet")

            except Exception as e:
                logger.error(f"Fehler beim Starten von Scanner {camera_index}: {e}")
                self.scanner_stats[camera_index] = {
                    'scans': 0,
                    'last_scan': None,
                    'status': 'error',
                    'error': str(e)
                }

        if self.scanners:
            logger.info(f"{len(self.scanners)} von {len(self.camera_indices)} Scannern gestartet")
        else:
            logger.error("Keine Scanner konnten gestartet werden")
            self.running = False

    def stop_all(self):
        """Stoppt alle Scanner"""
        self.running = False
        logger.info("Stoppe alle QR-Scanner...")

        for scanner in self.scanners:
            try:
                scanner.stop()
            except Exception as e:
                logger.warning(f"Fehler beim Stoppen eines Scanners: {e}")

        self.scanners.clear()
        logger.info("Alle Scanner gestoppt")

    def _on_scan_detected(self, payload, scanner_id):
        """Callback wenn QR-Code von einem Scanner erkannt wurde"""
        current_time = time.time()

        # Cross-Scanner Duplikat-Check
        if payload in self.last_scans:
            last_scan_time = self.last_scans[payload]['time']
            if current_time - last_scan_time < self.cross_scanner_cooldown:
                logger.debug(f"Cross-Scanner Duplikat ignoriert: {payload[:30]}... von Scanner {scanner_id}")
                return

        # Scan registrieren
        self.last_scans[payload] = {
            'time': current_time,
            'scanner_id': scanner_id
        }

        # Statistiken aktualisieren
        if scanner_id in self.scanner_stats:
            self.scanner_stats[scanner_id]['scans'] += 1
            self.scanner_stats[scanner_id]['last_scan'] = current_time

        self.total_scans += 1

        # An gemeinsamen Callback weiterleiten
        if self.shared_callback:
            try:
                # Zusätzliche Scanner-Info mitgeben
                enhanced_payload = {
                    'payload': payload,
                    'scanner_id': scanner_id,
                    'timestamp': current_time,
                    'scan_number': self.total_scans
                }

                # Für Rückwärtskompatibilität: Wenn Callback nur payload erwartet
                import inspect
                callback_params = inspect.signature(self.shared_callback).parameters
                if len(callback_params) == 1:
                    self.shared_callback(payload)
                else:
                    self.shared_callback(enhanced_payload)

            except Exception as e:
                logger.error(f"Fehler im Multi-Scanner Callback: {e}")
                # Fallback: Versuche nur mit payload
                try:
                    self.shared_callback(payload)
                except:
                    pass

    def get_stats(self):
        """Gibt Multi-Scanner Statistiken zurück"""
        return {
            'total_scanners': len(self.camera_indices),
            'active_scanners': len(self.scanners),
            'total_scans': self.total_scans,
            'scanner_stats': self.scanner_stats,
            'running': self.running
        }

    def get_scanner_info(self):
        """Gibt detaillierte Scanner-Informationen zurück"""
        info = []
        for camera_index in self.camera_indices:
            stats = self.scanner_stats.get(camera_index, {})

            scanner_info = {
                'camera_index': camera_index,
                'status': stats.get('status', 'unknown'),
                'scans': stats.get('scans', 0),
                'last_scan': stats.get('last_scan'),
                'active': any(s.camera_index == camera_index for s in self.scanners if hasattr(s, 'camera_index'))
            }

            if stats.get('error'):
                scanner_info['error'] = stats['error']

            info.append(scanner_info)

        return info


class QRScanner:
    """Einzelner QR-Scanner - erweiterte Version für Multi-Scanner System"""

    def __init__(self, camera_index=0, callback=None, video_label=None, scanner_id=None):
        """
        Args:
            camera_index: Kamera-Index (0 = Standard)
            callback: Funktion die bei erkanntem QR-Code aufgerufen wird
            video_label: Tkinter Label für Video-Anzeige (optional)
            scanner_id: Eindeutige Scanner-ID für Logging
        """
        self.camera_index = camera_index
        self.callback = callback
        self.video_label = video_label
        self.scanner_id = scanner_id or f"QRScanner_{camera_index}"

        self.cap = None
        self.running = False
        self.thread = None
        self.last_scan_data = None
        self.last_scan_time = 0

        # Lade Konfiguration
        from config import SCANNER_CONFIG, APP_CONFIG
        self.scan_cooldown = SCANNER_CONFIG.get('SCAN_COOLDOWN', 0.5)
        self.frame_skip = SCANNER_CONFIG.get('FRAME_SKIP', 3)
        self.frame_count = 0
        self.detection_running = False

        # Scanner-spezifische Einstellungen
        self.frame_width = SCANNER_CONFIG.get('FRAME_WIDTH', 640)
        self.frame_height = SCANNER_CONFIG.get('FRAME_HEIGHT', 480)
        self.fps = SCANNER_CONFIG.get('FPS', 30)
        self.buffer_size = SCANNER_CONFIG.get('BUFFER_SIZE', 1)
        self.camera_backend = APP_CONFIG.get('CAMERA_BACKEND', 'DSHOW')
        self.enable_autofocus = SCANNER_CONFIG.get('ENABLE_AUTOFOCUS', False)

        # Performance-Tracking
        self.performance_stats = {
            'frames_processed': 0,
            'qr_codes_detected': 0,
            'avg_processing_time': 0,
            'last_frame_time': 0
        }

    def start(self):
        """Scanner starten (optimiert für Multi-Scanner)"""
        if self.running:
            return

        try:
            logger.info(f"{self.scanner_id}: Starte Scanner mit Backend: {self.camera_backend}")

            # Kamera öffnen mit konfiguriertem Backend
            if self.camera_backend == 'DSHOW' and os.name == 'nt':
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            elif self.camera_backend == 'V4L2':
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            else:
                self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap.isOpened():
                raise Exception(f"Kamera {self.camera_index} konnte nicht geöffnet werden")

            # Optimierte Kamera-Einstellungen
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)

            # Autofocus und Exposure Einstellungen
            try:
                if not self.enable_autofocus:
                    self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual mode
            except:
                pass  # Nicht alle Kameras unterstützen diese Einstellungen

            self.running = True
            self.thread = threading.Thread(target=self._scan_loop, daemon=True, name=f"{self.scanner_id}_Thread")
            self.thread.start()

            logger.info(
                f"{self.scanner_id}: Erfolgreich gestartet (Kamera {self.camera_index}, Backend: {self.camera_backend})")

        except Exception as e:
            logger.error(f"{self.scanner_id}: Fehler beim Starten: {e}")
            self.release()
            raise

    def stop(self):
        """Scanner stoppen"""
        logger.info(f"{self.scanner_id}: Stoppe Scanner...")
        self.running = False
        self.detection_running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.0)

        self.release()
        logger.info(f"{self.scanner_id}: Scanner gestoppt")

    def release(self):
        """Kamera freigeben"""
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None

    def _scan_loop(self):
        """Haupt-Scan-Schleife (Multi-Scanner optimiert)"""
        logger.debug(f"{self.scanner_id}: Scan-Schleife gestartet")

        while self.running:
            try:
                if not self.cap or not self.cap.isOpened():
                    logger.warning(f"{self.scanner_id}: Kamera nicht verfügbar")
                    time.sleep(0.1)
                    continue

                frame_start_time = time.time()
                ret, frame = self.cap.read()

                if not ret or frame is None:
                    logger.debug(f"{self.scanner_id}: Kein Frame erhalten")
                    time.sleep(0.05)
                    continue

                # Performance-Statistiken
                self.performance_stats['frames_processed'] += 1
                self.performance_stats['last_frame_time'] = frame_start_time

                # Frame verarbeiten für Anzeige (nur wenn Video-Label vorhanden)
                if self.video_label and self.running:
                    display_frame = self._process_frame_for_display(frame.copy())
                    self._update_video_display(display_frame)

                # QR-Codes suchen (mit Frame-Skip für Performance)
                self.frame_count += 1
                if self.frame_count % self.frame_skip == 0 and not self.detection_running:
                    self.detection_running = True
                    # QR-Erkennung in separatem Thread für bessere Performance
                    threading.Thread(
                        target=self._detect_qr_codes_async,
                        args=(frame.copy(),),
                        daemon=True,
                        name=f"{self.scanner_id}_Detection"
                    ).start()

                # Processing-Zeit berechnen
                processing_time = time.time() - frame_start_time
                self._update_performance_stats(processing_time)

                # CPU schonen - adaptives Timing basierend auf Performance
                if processing_time < 0.02:  # Wenn sehr schnell
                    time.sleep(0.03)  # ~30 FPS
                elif processing_time < 0.04:  # Wenn normal
                    time.sleep(0.02)  # ~25 FPS
                else:  # Wenn langsam
                    time.sleep(0.01)  # ~20 FPS

            except Exception as e:
                logger.error(f"{self.scanner_id}: Fehler in Scan-Schleife: {e}")
                time.sleep(0.1)

        logger.debug(f"{self.scanner_id}: Scan-Schleife beendet")

    def _detect_qr_codes_async(self, frame):
        """QR-Codes asynchron erkennen"""
        try:
            self._detect_qr_codes(frame)
        finally:
            self.detection_running = False

    def _process_frame_for_display(self, frame):
        """Frame für Anzeige verarbeiten"""
        try:
            # Größe anpassen für Anzeige
            display_frame = cv2.resize(frame, (640, 480))

            # Scanner-ID und Status overlay
            status_text = f"{self.scanner_id}: Aktiv"
            if self.last_scan_data:
                time_since_scan = time.time() - self.last_scan_time
                if time_since_scan < 2.0:
                    status_text = f"{self.scanner_id}: QR erkannt!"

            cv2.putText(
                display_frame,
                status_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            # Performance-Info (optional)
            perf_text = f"FPS: {self.performance_stats['frames_processed'] // max(1, int(time.time() - self.performance_stats.get('start_time', time.time())))}"
            cv2.putText(
                display_frame,
                perf_text,
                (10, 460),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )

            # Scan-Bereich markieren
            height, width = display_frame.shape[:2]
            center_x, center_y = width // 2, height // 2

            # Fadenkreuz
            cv2.line(display_frame, (center_x - 30, center_y), (center_x + 30, center_y), (0, 255, 0), 2)
            cv2.line(display_frame, (center_x, center_y - 30), (center_x, center_y + 30), (0, 255, 0), 2)

            # Scan-Rahmen
            cv2.rectangle(display_frame, (center_x - 80, center_y - 80), (center_x + 80, center_y + 80), (0, 255, 0), 1)

            return display_frame

        except Exception as e:
            logger.error(f"{self.scanner_id}: Fehler bei Frame-Verarbeitung: {e}")
            return frame

    def _detect_qr_codes(self, frame):
        """QR-Codes im Frame erkennen (Multi-Scanner optimiert)"""
        try:
            detection_start = time.time()

            # Graubild für bessere Erkennung
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Kontrast verbessern
            gray = cv2.equalizeHist(gray)

            # QR-Codes dekodieren (nur QR-Codes für bessere Performance)
            decoded_objects = pyzbar.decode(gray, symbols=[ZBarSymbol.QRCODE])

            for obj in decoded_objects:
                # Daten extrahieren
                qr_data = obj.data.decode('utf-8', errors='ignore')

                # Cooldown prüfen (gegen zu häufige gleiche Scans)
                current_time = time.time()
                if (qr_data == self.last_scan_data and
                        current_time - self.last_scan_time < self.scan_cooldown):
                    logger.debug(f"{self.scanner_id}: QR-Code Cooldown aktiv für: {qr_data[:30]}...")
                    continue

                # Validierung
                validated = validate_qr_payload(qr_data)
                if validated and validated.get('valid', True):
                    self.last_scan_data = qr_data
                    self.last_scan_time = current_time
                    self.performance_stats['qr_codes_detected'] += 1

                    logger.info(f"{self.scanner_id}: QR-Code erkannt: {qr_data[:50]}...")

                    # Callback aufrufen
                    if self.callback:
                        try:
                            self.callback(qr_data)
                        except Exception as e:
                            logger.error(f"{self.scanner_id}: Fehler im Callback: {e}")
                else:
                    logger.debug(f"{self.scanner_id}: QR-Code Validierung fehlgeschlagen: {qr_data[:30]}...")

            # Performance-Tracking
            detection_time = time.time() - detection_start
            if detection_time > 0.1:  # Warnung bei langsamer Erkennung
                logger.debug(f"{self.scanner_id}: Langsame QR-Erkennung: {detection_time:.3f}s")

        except Exception as e:
            logger.error(f"{self.scanner_id}: Fehler bei QR-Erkennung: {e}")

    def _update_video_display(self, frame):
        """Video im Tkinter Label anzeigen (Thread-sicher)"""
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
            logger.debug(f"{self.scanner_id}: Fehler bei Video-Anzeige: {e}")

    def _update_performance_stats(self, processing_time):
        """Aktualisiert Performance-Statistiken"""
        # Gleitender Durchschnitt für Processing-Zeit
        if self.performance_stats['avg_processing_time'] == 0:
            self.performance_stats['avg_processing_time'] = processing_time
        else:
            alpha = 0.1  # Glättungsfaktor
            self.performance_stats['avg_processing_time'] = (
                    alpha * processing_time +
                    (1 - alpha) * self.performance_stats['avg_processing_time']
            )

    def get_performance_stats(self):
        """Gibt Performance-Statistiken zurück"""
        stats = self.performance_stats.copy()
        stats['scanner_id'] = self.scanner_id
        stats['camera_index'] = self.camera_index
        stats['running'] = self.running
        stats['scan_cooldown'] = self.scan_cooldown
        stats['frame_skip'] = self.frame_skip
        return stats

    def set_scan_cooldown(self, cooldown):
        """Setzt das Scan-Cooldown"""
        old_cooldown = self.scan_cooldown
        self.scan_cooldown = max(0.1, min(5.0, cooldown))
        logger.info(f"{self.scanner_id}: Scan-Cooldown geändert: {old_cooldown}s → {self.scan_cooldown}s")


# Test-Funktionen
def test_single_scanner():
    """Test-Funktion für einzelnen Scanner"""
    print("📸 Einzelner QR-Scanner Test")

    def on_qr_code(data):
        print(f"✅ QR-Code: {data}")

    scanner = QRScanner(camera_index=0, callback=on_qr_code)

    try:
        scanner.start()
        print("Scanner läuft... Drücken Sie Ctrl+C zum Beenden")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest beendet")
    finally:
        scanner.stop()


def test_multi_scanner():
    """Test-Funktion für Multi-Scanner"""
    print("📸 Multi-QR-Scanner Test")

    def on_qr_code(enhanced_payload):
        if isinstance(enhanced_payload, dict):
            payload = enhanced_payload['payload']
            scanner_id = enhanced_payload['scanner_id']
            print(f"✅ QR-Code von {scanner_id}: {payload}")
        else:
            print(f"✅ QR-Code: {enhanced_payload}")

    multi_scanner = MultiQRScanner([0, 1], shared_callback=on_qr_code)

    try:
        multi_scanner.start_all()
        print("Multi-Scanner läuft... Drücken Sie Ctrl+C zum Beenden")

        while True:
            time.sleep(5)
            stats = multi_scanner.get_stats()
            print(f"📊 Statistiken: {stats['total_scans']} Scans von {stats['active_scanners']} Scannern")

    except KeyboardInterrupt:
        print("\nTest beendet")
    finally:
        multi_scanner.stop_all()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'multi':
        test_multi_scanner()
    else:
        test_single_scanner()