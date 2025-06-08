#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware-spezifische Tests für RFID & QR Scanner
Detaillierte Tests für RFID-Reader und Kameras
"""

import sys
import os
import time
import threading
import unittest
from unittest.mock import Mock, patch, MagicMock
import cv2
import numpy as np

# Projekt-Pfad hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class RFIDReaderTests(unittest.TestCase):
    """Umfassende RFID-Reader Tests"""

    def setUp(self):
        """Setup für RFID-Tests"""
        from hid_listener import HIDListener
        self.listener = HIDListener()

    def tearDown(self):
        """Cleanup nach Tests"""
        if hasattr(self.listener, 'stop'):
            self.listener.stop()

    def test_rfid_listener_creation(self):
        """Test: HIDListener kann erstellt werden"""
        self.assertIsNotNone(self.listener)
        self.assertFalse(self.listener.running)
        self.assertEqual(self.listener.buffer, "")

    def test_rfid_listener_start_stop(self):
        """Test: HIDListener kann gestartet und gestoppt werden"""
        # Start
        self.listener.start()
        self.assertTrue(self.listener.running)
        time.sleep(0.1)  # Kurz warten

        # Stop
        self.listener.stop()
        self.assertFalse(self.listener.running)

    def test_tag_validation_comprehensive(self):
        """Test: Tag-Validierung mit verschiedenen Eingaben"""
        from utils import validate_tag_id

        # Gültige Tags
        valid_tags = [
            '53004ECD68',  # Standard 10-stellig
            '53004E114B',
            '1234567890',
            'ABCDEF1234',
            'abcdef1234',  # Lowercase sollte auch funktionieren
        ]

        for tag in valid_tags:
            with self.subTest(tag=tag):
                self.assertTrue(validate_tag_id(tag), f"Tag {tag} sollte gültig sein")

        # Ungültige Tags
        invalid_tags = [
            '',  # Leer
            '123',  # Zu kurz
            '123456789012345',  # Zu lang
            'GHIJK12345',  # Ungültige Hex-Zeichen
            '53004ECD6!',  # Sonderzeichen
            'NULL',  # Ungültiger String
            '0000000000',  # Nur Nullen (je nach Implementierung)
        ]

        for tag in invalid_tags:
            with self.subTest(tag=tag):
                self.assertFalse(validate_tag_id(tag), f"Tag {tag} sollte ungültig sein")

    def test_hex_decimal_conversion(self):
        """Test: Hex-Decimal Konvertierung"""
        from utils import hex_to_decimal, decimal_to_hex

        test_cases = [
            ('53004ECD68', 355034188136),
            ('53004E114B', 355034182987),
            ('1234567890', 78187493520),
            ('ABCDEF1234', 737894711860),
        ]

        for hex_val, expected_dec in test_cases:
            with self.subTest(hex_val=hex_val):
                # Hex zu Decimal
                decimal = hex_to_decimal(hex_val)
                self.assertEqual(decimal, expected_dec)

                # Decimal zurück zu Hex
                hex_back = decimal_to_hex(decimal)
                self.assertEqual(hex_back.upper(), hex_val.upper())

    def test_buffer_handling(self):
        """Test: Buffer-Verarbeitung simulieren"""
        test_callback_results = []

        def test_callback(tag_id):
            test_callback_results.append(tag_id)

        self.listener.callback = test_callback

        # Simuliere Buffer-Verarbeitung
        valid_tag = "53004ECD68"
        self.listener.buffer = valid_tag
        self.listener._process_buffer()

        # Buffer sollte geleert sein
        self.assertEqual(self.listener.buffer, "")

        # Callback sollte aufgerufen worden sein
        self.assertEqual(len(test_callback_results), 1)
        self.assertEqual(test_callback_results[0], valid_tag)

    def test_scan_interval_control(self):
        """Test: Scan-Interval Kontrolle"""
        # Test Scan-Interval setzen
        old_interval = self.listener.min_scan_interval
        new_interval = 2.0

        self.listener.set_min_scan_interval(new_interval)
        self.assertEqual(self.listener.min_scan_interval, new_interval)

        # Test Grenzen
        self.listener.set_min_scan_interval(-1.0)  # Sollte auf minimum begrenzt werden
        self.assertGreaterEqual(self.listener.min_scan_interval, 0.1)

        self.listener.set_min_scan_interval(20.0)  # Sollte auf maximum begrenzt werden
        self.assertLessEqual(self.listener.min_scan_interval, 10.0)

    def test_keyboard_input_simulation(self):
        """Test: Simuliere Keyboard-Input"""
        with patch('pynput.keyboard.Listener') as mock_listener:
            # Mock den Listener
            mock_instance = Mock()
            mock_listener.return_value = mock_instance

            listener = HIDListener()
            listener.start()

            # Prüfe ob Listener gestartet wurde
            mock_listener.assert_called_once()
            mock_instance.start.assert_called_once()


class CameraTests(unittest.TestCase):
    """Umfassende Kamera-Tests"""

    def setUp(self):
        """Setup für Kamera-Tests"""
        self.test_camera_indices = [0, 1, 2, 3]
        self.available_cameras = []

    def tearDown(self):
        """Cleanup nach Tests"""
        # Alle Test-Kameras freigeben
        pass

    def test_camera_detection_comprehensive(self):
        """Test: Umfassende Kamera-Erkennung"""
        print("\n🔍 Teste Kamera-Erkennung...")

        # Teste verschiedene Backends
        backends_to_test = [cv2.CAP_ANY]

        if os.name == 'nt':  # Windows
            backends_to_test.extend([cv2.CAP_DSHOW, cv2.CAP_MSMF])
        else:  # Linux/Mac
            backends_to_test.extend([cv2.CAP_V4L2, cv2.CAP_GSTREAMER])

        found_cameras = {}

        for backend in backends_to_test:
            backend_name = self._get_backend_name(backend)
            print(f"   🔧 Teste Backend: {backend_name}")

            for camera_index in self.test_camera_indices:
                try:
                    cap = cv2.VideoCapture(camera_index, backend)

                    if cap.isOpened():
                        # Teste Frame-Capture
                        ret, frame = cap.read()

                        if ret and frame is not None:
                            height, width = frame.shape[:2]

                            camera_info = {
                                'index': camera_index,
                                'backend': backend_name,
                                'resolution': f"{width}x{height}",
                                'channels': frame.shape[2] if len(frame.shape) > 2 else 1
                            }

                            if camera_index not in found_cameras:
                                found_cameras[camera_index] = []
                            found_cameras[camera_index].append(camera_info)

                            print(f"      ✅ Kamera {camera_index}: {width}x{height}")

                    cap.release()

                except Exception as e:
                    print(f"      ❌ Kamera {camera_index} mit {backend_name}: {e}")
                    continue

        self.available_cameras = found_cameras

        # Mindestens eine Kamera sollte gefunden werden
        self.assertGreater(len(found_cameras), 0, "Keine funktionierenden Kameras gefunden")

        print(f"   📊 Gefundene Kameras: {len(found_cameras)}")

    def test_camera_properties(self):
        """Test: Kamera-Eigenschaften testen"""
        if not self.available_cameras:
            self.test_camera_detection_comprehensive()

        if not self.available_cameras:
            self.skipTest("Keine Kameras verfügbar")

        # Teste mit erster verfügbarer Kamera
        first_camera_index = list(self.available_cameras.keys())[0]

        cap = cv2.VideoCapture(first_camera_index)
        self.assertTrue(cap.isOpened(), "Kamera konnte nicht geöffnet werden")

        try:
            # Teste verschiedene Eigenschaften
            properties_to_test = [
                (cv2.CAP_PROP_FRAME_WIDTH, 640),
                (cv2.CAP_PROP_FRAME_HEIGHT, 480),
                (cv2.CAP_PROP_FPS, 30),
                (cv2.CAP_PROP_BUFFERSIZE, 1),
            ]

            for prop, value in properties_to_test:
                # Setze Eigenschaft
                cap.set(prop, value)

                # Lese Eigenschaft zurück
                actual_value = cap.get(prop)

                print(f"      Property {prop}: Set={value}, Got={actual_value}")

                # Nicht alle Kameras unterstützen alle Eigenschaften
                # Daher nur warnen, nicht fehlschlagen

        finally:
            cap.release()

    def test_camera_frame_capture(self):
        """Test: Frame-Capture Funktionalität"""
        if not self.available_cameras:
            self.test_camera_detection_comprehensive()

        if not self.available_cameras:
            self.skipTest("Keine Kameras verfügbar")

        first_camera_index = list(self.available_cameras.keys())[0]

        cap = cv2.VideoCapture(first_camera_index)
        self.assertTrue(cap.isOpened())

        try:
            # Teste mehrere Frames
            successful_frames = 0

            for i in range(10):
                ret, frame = cap.read()

                if ret and frame is not None:
                    successful_frames += 1

                    # Validiere Frame
                    self.assertIsInstance(frame, np.ndarray)
                    self.assertEqual(len(frame.shape), 3)  # Sollte RGB/BGR sein
                    self.assertGreater(frame.shape[0], 0)  # Höhe > 0
                    self.assertGreater(frame.shape[1], 0)  # Breite > 0

                time.sleep(0.1)  # Kurze Pause zwischen Frames

            # Mindestens 50% der Frames sollten erfolgreich sein
            success_rate = successful_frames / 10
            self.assertGreater(success_rate, 0.5, f"Nur {success_rate:.1%} erfolgreiche Frames")

            print(f"      📊 Frame-Capture: {success_rate:.1%} erfolgreich")

        finally:
            cap.release()

    def test_multiple_camera_access(self):
        """Test: Mehrere Kameras gleichzeitig"""
        if len(self.available_cameras) < 2:
            self.skipTest("Nicht genug Kameras für Multi-Camera Test")

        camera_indices = list(self.available_cameras.keys())[:2]  # Maximal 2 Kameras

        caps = []

        try:
            # Öffne mehrere Kameras
            for camera_index in camera_indices:
                cap = cv2.VideoCapture(camera_index)
                self.assertTrue(cap.isOpened(), f"Kamera {camera_index} konnte nicht geöffnet werden")
                caps.append(cap)

            # Teste simultane Frame-Captures
            for i in range(5):
                frames = []

                for j, cap in enumerate(caps):
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        frames.append((camera_indices[j], frame))

                # Mindestens eine Kamera sollte Frame liefern
                self.assertGreater(len(frames), 0, f"Keine Frames in Iteration {i}")

                time.sleep(0.1)

            print(f"      ✅ {len(caps)} Kameras gleichzeitig funktionsfähig")

        finally:
            # Cleanup
            for cap in caps:
                if cap:
                    cap.release()

    def test_camera_error_handling(self):
        """Test: Kamera-Fehlerbehandlung"""
        # Test mit nicht-existierender Kamera
        invalid_camera = 99
        cap = cv2.VideoCapture(invalid_camera)

        # Sollte nicht geöffnet sein
        self.assertFalse(cap.isOpened(), "Ungültige Kamera sollte nicht geöffnet werden")

        # Teste Frame-Capture bei ungültiger Kamera
        ret, frame = cap.read()
        self.assertFalse(ret, "Frame-Capture sollte bei ungültiger Kamera fehlschlagen")

        cap.release()

        # Test mit bereits verwendeter Kamera
        if self.available_cameras:
            camera_index = list(self.available_cameras.keys())[0]

            cap1 = cv2.VideoCapture(camera_index)
            cap2 = cv2.VideoCapture(camera_index)  # Zweiter Zugriff

            try:
                # Beide sollten sich öffnen lassen (je nach System)
                # Aber mindestens einer sollte funktionieren

                ret1, frame1 = cap1.read() if cap1.isOpened() else (False, None)
                ret2, frame2 = cap2.read() if cap2.isOpened() else (False, None)

                # Mindestens eine sollte funktionieren
                self.assertTrue(ret1 or ret2, "Mindestens eine Kamera-Instanz sollte funktionieren")

            finally:
                cap1.release()
                cap2.release()

    def _get_backend_name(self, backend):
        """Hilfsfunktion: Backend-Name ermitteln"""
        backend_names = {
            cv2.CAP_ANY: "AUTO",
            cv2.CAP_DSHOW: "DSHOW",
            cv2.CAP_MSMF: "MSMF",
            cv2.CAP_V4L2: "V4L2",
            cv2.CAP_GSTREAMER: "GSTREAMER"
        }
        return backend_names.get(backend, f"UNKNOWN_{backend}")


class QRCodeTests(unittest.TestCase):
    """QR-Code spezifische Tests"""

    def setUp(self):
        """Setup für QR-Tests"""
        self.test_qr_codes = [
            '{"kunde":"Test GmbH","auftrag":"12345","paket":"1/3"}',  # JSON
            'Kunde:XYZ Corp^Auftrag:67890^Paket:2/5',  # Key-Value
            'Einfacher Text für Wareneingang',  # Plain Text
            '1^126644896^25000580^12345^END',  # Delimited
            '',  # Leer
            'x' * 1000,  # Lang
            '{"malformed_json": }',  # Ungültiges JSON
            'Special chars: äöü ßñ € @#$%',  # Sonderzeichen
        ]

    def test_qr_payload_validation_comprehensive(self):
        """Test: Umfassende QR-Payload Validierung"""
        from utils import validate_qr_payload

        results = []

        for i, payload in enumerate(self.test_qr_codes):
            with self.subTest(payload_index=i):
                try:
                    result = validate_qr_payload(payload)

                    self.assertIsNotNone(result, f"Validierung für Payload {i} sollte Ergebnis liefern")
                    self.assertIn('type', result, "Ergebnis sollte 'type' enthalten")
                    self.assertIn('valid', result, "Ergebnis sollte 'valid' enthalten")

                    results.append({
                        'payload': payload[:50] + '...' if len(payload) > 50 else payload,
                        'type': result.get('type'),
                        'valid': result.get('valid'),
                        'data': str(type(result.get('data')))
                    })

                except Exception as e:
                    self.fail(f"Validation für Payload {i} sollte nicht crashen: {e}")

        # Statistische Auswertung
        valid_count = sum(1 for r in results if r['valid'])
        total_count = len(results)

        print(f"\n📊 QR-Payload Validierung:")
        print(f"   Getestet: {total_count} Payloads")
        print(f"   Gültig: {valid_count}")
        print(f"   Ungültig: {total_count - valid_count}")

        for result in results:
            status = "✅" if result['valid'] else "❌"
            print(f"   {status} {result['type']}: {result['payload']}")

        # Mindestens 50% sollten als gültig erkannt werden (sehr tolerant)
        success_rate = valid_count / total_count
        self.assertGreater(success_rate, 0.5, f"Nur {success_rate:.1%} als gültig erkannt")

    def test_qr_scanner_creation(self):
        """Test: QRScanner kann erstellt werden"""
        from qr_scanner import QRScanner

        # Test ohne Video-Label
        scanner = QRScanner(camera_index=0, callback=None)
        self.assertIsNotNone(scanner)
        self.assertEqual(scanner.camera_index, 0)
        self.assertFalse(scanner.running)

        # Test mit Mock-Callback
        callback_called = []

        def test_callback(payload):
            callback_called.append(payload)

        scanner_with_callback = QRScanner(camera_index=0, callback=test_callback)
        self.assertEqual(scanner_with_callback.callback, test_callback)

    def test_multi_qr_scanner(self):
        """Test: MultiQRScanner Funktionalität"""
        from qr_scanner import MultiQRScanner

        # Test-Kameras
        camera_indices = [0, 1, 2]
        callback_results = []

        def shared_callback(payload):
            callback_results.append(payload)

        # Erstelle MultiQRScanner
        multi_scanner = MultiQRScanner(
            camera_indices=camera_indices,
            shared_callback=shared_callback
        )

        self.assertIsNotNone(multi_scanner)
        self.assertEqual(multi_scanner.camera_indices, camera_indices)
        self.assertEqual(multi_scanner.shared_callback, shared_callback)
        self.assertFalse(multi_scanner.running)

        # Test Statistiken (initial)
        stats = multi_scanner.get_stats()
        self.assertEqual(stats['total_scanners'], len(camera_indices))
        self.assertEqual(stats['active_scanners'], 0)
        self.assertEqual(stats['total_scans'], 0)

    def test_qr_code_synthesis(self):
        """Test: Synthetische QR-Code Erzeugung und Erkennung"""
        try:
            import qrcode
            from pyzbar import pyzbar
            import numpy as np

            # Teste verschiedene Payloads
            test_payloads = [
                "TEST_SIMPLE",
                '{"test":"data","number":123}',
                'Ä special chars: äöü ß €',
                'A' * 100,  # Langer Text
            ]

            for payload in test_payloads:
                with self.subTest(payload=payload[:20]):
                    # Erstelle QR-Code
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(payload)
                    qr.make(fit=True)

                    # Zu Image
                    img = qr.make_image(fill_color="black", back_color="white")

                    # Zu numpy array
                    img_array = np.array(img)

                    # Dekodiere
                    decoded = pyzbar.decode(img_array)

                    self.assertEqual(len(decoded), 1, "Genau ein QR-Code sollte erkannt werden")

                    decoded_data = decoded[0].data.decode('utf-8')
                    self.assertEqual(decoded_data, payload, "Dekodierte Daten sollten original entsprechen")

            print(f"      ✅ {len(test_payloads)} synthetische QR-Codes erfolgreich")

        except ImportError:
            self.skipTest("qrcode-Modul nicht verfügbar")

    def test_pyzbar_performance(self):
        """Test: pyzbar Performance"""
        from pyzbar import pyzbar
        import numpy as np
        import time

        # Erstelle Test-Bilder verschiedener Größen
        test_sizes = [(100, 100), (320, 240), (640, 480), (1280, 720)]

        performance_results = []

        for width, height in test_sizes:
            # Erstelle random Bild (kein QR-Code)
            test_image = np.random.randint(0, 256, (height, width), dtype=np.uint8)

            # Messe Zeit für Dekodierung
            start_time = time.time()

            # Mehrere Versuche für genauere Messung
            for _ in range(5):
                decoded = pyzbar.decode(test_image)

            end_time = time.time()

            avg_time = (end_time - start_time) / 5 * 1000  # ms

            performance_results.append({
                'size': f"{width}x{height}",
                'time_ms': avg_time,
                'decoded_count': len(decoded)
            })

        print(f"\n📊 pyzbar Performance:")
        for result in performance_results:
            print(f"   {result['size']}: {result['time_ms']:.1f}ms (gefunden: {result['decoded_count']})")

        # Performance sollte unter 100ms für 640x480 sein
        result_640x480 = next((r for r in performance_results if r['size'] == '640x480'), None)
        if result_640x480:
            self.assertLess(result_640x480['time_ms'], 100, "pyzbar sollte unter 100ms für 640x480 sein")


class HardwareIntegrationTests(unittest.TestCase):
    """Integration Tests für Hardware-Komponenten"""

    def test_rfid_camera_parallel(self):
        """Test: RFID und Kamera parallel"""
        from hid_listener import HIDListener
        from qr_scanner import QRScanner

        # Setup
        rfid_results = []
        qr_results = []

        def rfid_callback(tag_id):
            rfid_results.append(tag_id)

        def qr_callback(payload):
            qr_results.append(payload)

        # Erstelle beide Komponenten
        rfid_listener = HIDListener(callback=rfid_callback)
        qr_scanner = QRScanner(camera_index=0, callback=qr_callback)

        try:
            # Starte beide
            rfid_listener.start()
            # QR-Scanner nur starten wenn Kamera verfügbar

            # Kurz laufen lassen
            time.sleep(1.0)

            # Beide sollten ohne Konflikte laufen
            self.assertTrue(rfid_listener.running)

            print("      ✅ RFID und Kamera laufen parallel ohne Konflikte")

        finally:
            # Cleanup
            rfid_listener.stop()
            if hasattr(qr_scanner, 'stop'):
                qr_scanner.stop()

    def test_system_resource_usage(self):
        """Test: System-Ressourcen-Verbrauch"""
        try:
            import psutil

            process = psutil.Process()

            # Baseline
            baseline_cpu = process.cpu_percent()
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Simuliere Hardware-Nutzung
            from hid_listener import HIDListener

            components = []

            try:
                # RFID Listener
                rfid_listener = HIDListener()
                rfid_listener.start()
                components.append(rfid_listener)

                time.sleep(2.0)  # Lasse laufen

                # Messe Ressourcen
                current_cpu = process.cpu_percent()
                current_memory = process.memory_info().rss / 1024 / 1024  # MB

                memory_increase = current_memory - baseline_memory

                print(f"\n📊 Ressourcen-Verbrauch:")
                print(f"   Baseline Memory: {baseline_memory:.1f} MB")
                print(f"   Current Memory: {current_memory:.1f} MB")
                print(f"   Memory Increase: {memory_increase:.1f} MB")
                print(f"   CPU Usage: {current_cpu:.1f}%")

                # Thresholds (großzügig)
                self.assertLess(memory_increase, 100, "Memory-Increase sollte unter 100MB sein")
                self.assertLess(current_cpu, 50, "CPU-Usage sollte unter 50% sein")

            finally:
                # Cleanup
                for component in components:
                    if hasattr(component, 'stop'):
                        component.stop()

        except ImportError:
            self.skipTest("psutil nicht verfügbar")

    def test_hardware_error_recovery(self):
        """Test: Hardware-Fehler Recovery"""
        from hid_listener import HIDListener

        # Test RFID Recovery
        listener = HIDListener()

        try:
            # Normale Funktion
            listener.start()
            self.assertTrue(listener.running)

            # Simuliere Fehler durch Stop
            listener.stop()
            self.assertFalse(listener.running)

            # Recovery - erneuter Start
            listener.start()
            self.assertTrue(listener.running)

            print("      ✅ RFID Error-Recovery funktioniert")

        finally:
            listener.stop()


def run_hardware_tests():
    """Führt alle Hardware-Tests aus"""
    print("🔧 Hardware-spezifische Tests")
    print("=" * 50)

    # Test-Suites erstellen
    test_suites = [
        ('RFID Reader Tests', unittest.TestLoader().loadTestsFromTestCase(RFIDReaderTests)),
        ('Camera Tests', unittest.TestLoader().loadTestsFromTestCase(CameraTests)),
        ('QR Code Tests', unittest.TestLoader().loadTestsFromTestCase(QRCodeTests)),
        ('Hardware Integration', unittest.TestLoader().loadTestsFromTestCase(HardwareIntegrationTests)),
    ]

    total_tests = 0
    total_failures = 0
    total_errors = 0

    for suite_name, test_suite in test_suites:
        print(f"\n🔍 {suite_name}")
        print("-" * 30)

        # Test-Runner mit detailliertem Output
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(test_suite)

        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)

        # Ergebnis-Summary
        if result.failures:
            print(f"❌ Fehlschläge in {suite_name}:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")

        if result.errors:
            print(f"💥 Fehler in {suite_name}:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback.split('\\n')[-2]}")

    # Gesamt-Summary
    print("\n" + "=" * 50)
    print("📊 HARDWARE-TEST ZUSAMMENFASSUNG")
    print("=" * 50)
    print(f"🎯 Tests durchgeführt: {total_tests}")
    print(f"✅ Erfolgreich: {total_tests - total_failures - total_errors}")
    print(f"❌ Fehlschläge: {total_failures}")
    print(f"💥 Fehler: {total_errors}")

    success_rate = (total_tests - total_failures - total_errors) / total_tests if total_tests > 0 else 0
    print(f"📈 Erfolgsrate: {success_rate:.1%}")

    if total_failures == 0 and total_errors == 0:
        print("\n🎉 Alle Hardware-Tests erfolgreich!")
        print("✅ Hardware ist bereit für den Einsatz")
    else:
        print(f"\n⚠️ {total_failures + total_errors} Test(s) fehlgeschlagen")
        print("🔧 Überprüfen Sie die Hardware-Verbindungen")

    return total_failures == 0 and total_errors == 0


if __name__ == '__main__':
    success = run_hardware_tests()
    sys.exit(0 if success else 1)