#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit-Tests für QR-Scanner Funktionalität
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import cv2

from src.scanner.qr_scanner import QRScanner
from src.scanner.camera_handler import CameraHandler
from src.scanner.decoder import QRDecoder
from src.models.scan_data import ScanData


class TestCameraHandler(unittest.TestCase):
    """Tests für Kamera-Handler"""

    @patch('cv2.VideoCapture')
    def test_camera_initialization(self, mock_video_capture):
        """Test: Kamera-Initialisierung"""
        # Mock konfigurieren
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_video_capture.return_value = mock_cap

        # Test
        camera = CameraHandler(camera_index=0)

        # Assertions
        mock_video_capture.assert_called_once_with(0)
        self.assertTrue(camera.is_opened())

    @patch('cv2.VideoCapture')
    def test_camera_initialization_failure(self, mock_video_capture):
        """Test: Kamera-Initialisierung fehlgeschlagen"""
        # Mock konfigurieren
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap

        # Test
        camera = CameraHandler(camera_index=0)

        # Assertions
        self.assertFalse(camera.is_opened())

    @patch('cv2.VideoCapture')
    def test_read_frame(self, mock_video_capture):
        """Test: Frame lesen"""
        # Mock konfigurieren
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True

        # Dummy-Frame erstellen
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, test_frame)
        mock_video_capture.return_value = mock_cap

        # Test
        camera = CameraHandler()
        success, frame = camera.read_frame()

        # Assertions
        self.assertTrue(success)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (480, 640, 3))

    @patch('cv2.VideoCapture')
    def test_release_camera(self, mock_video_capture):
        """Test: Kamera freigeben"""
        # Mock konfigurieren
        mock_cap = MagicMock()
        mock_video_capture.return_value = mock_cap

        # Test
        camera = CameraHandler()
        camera.release()

        # Assertions
        mock_cap.release.assert_called_once()

    @patch('cv2.VideoCapture')
    def test_camera_properties(self, mock_video_capture):
        """Test: Kamera-Eigenschaften setzen"""
        # Mock konfigurieren
        mock_cap = MagicMock()
        mock_video_capture.return_value = mock_cap

        # Test
        camera = CameraHandler()
        camera.set_resolution(1280, 720)

        # Assertions
        mock_cap.set.assert_any_call(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        mock_cap.set.assert_any_call(cv2.CAP_PROP_FRAME_HEIGHT, 720)


class TestQRDecoder(unittest.TestCase):
    """Tests für QR-Code Decoder"""

    def setUp(self):
        """Setup für jeden Test"""
        self.decoder = QRDecoder()

    def test_parse_type1_format(self):
        """Test: Typ 1 Format (^ getrennt)"""
        # Test-Daten
        qr_data = "VER^NL-2581949^1165^2200212401^1^SBZ23C-11"

        # Test
        result = self.decoder.parse_qr_content(qr_data)

        # Assertions
        self.assertEqual(result['auftrags_nr'], "NL-2581949")
        self.assertEqual(result['paket_nr'], "2200212401")
        self.assertEqual(result['kunden_name'], "Kunden-ID: 1165")

    def test_parse_type2_format(self):
        """Test: Typ 2 Format (Key-Value)"""
        # Test-Daten
        qr_data = "AUFTRAG: NL-123456\nPAKET-NR: 9876543210\nKUNDENNAME: Test GmbH"

        # Test
        result = self.decoder.parse_qr_content(qr_data)

        # Assertions
        self.assertEqual(result['auftrags_nr'], "NL-123456")
        self.assertEqual(result['paket_nr'], "9876543210")
        self.assertEqual(result['kunden_name'], "Test GmbH")

    def test_parse_json_format(self):
        """Test: JSON Format"""
        # Test-Daten
        qr_data = '{"auftrag": "DE-789012", "paket": "1234567890", "kunde": "Mustermann"}'

        # Test
        result = self.decoder.parse_qr_content(qr_data)

        # Assertions
        self.assertEqual(result['auftrags_nr'], "DE-789012")
        self.assertEqual(result['paket_nr'], "1234567890")
        self.assertEqual(result['kunden_name'], "Mustermann")

    def test_parse_url_format(self):
        """Test: URL Format"""
        # Test-Daten
        qr_data = "https://tracking.example.com?order=NL-111111&package=2222222222&customer=Example%20Corp"

        # Test
        result = self.decoder.parse_qr_content(qr_data)

        # Assertions
        self.assertEqual(result['auftrags_nr'], "NL-111111")
        self.assertEqual(result['paket_nr'], "2222222222")
        self.assertEqual(result['kunden_name'], "Example Corp")

    def test_parse_regex_patterns(self):
        """Test: Regex-Pattern Erkennung"""
        # Test-Daten
        qr_data = "Random text with NL-555555 and tracking 3333333333"

        # Test
        result = self.decoder.parse_qr_content(qr_data)

        # Assertions
        self.assertEqual(result['auftrags_nr'], "NL-555555")
        self.assertEqual(result['paket_nr'], "3333333333")

    def test_parse_invalid_format(self):
        """Test: Ungültiges Format"""
        # Test-Daten
        qr_data = "This is just random text without any patterns"

        # Test
        result = self.decoder.parse_qr_content(qr_data)

        # Assertions
        self.assertEqual(result['auftrags_nr'], "")
        self.assertEqual(result['paket_nr'], "")
        self.assertEqual(result['kunden_name'], "")
        self.assertEqual(result['raw_data'], qr_data)

    @patch('pyzbar.pyzbar.decode')
    def test_decode_image(self, mock_pyzbar_decode):
        """Test: Bild decodieren"""
        # Mock-Daten
        mock_qr = MagicMock()
        mock_qr.data = b"VER^NL-2581949^1165^2200212401^1^SBZ23C-11"
        mock_qr.polygon = [(10, 10), (100, 10), (100, 100), (10, 100)]
        mock_pyzbar_decode.return_value = [mock_qr]

        # Dummy-Bild
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)

        # Test
        results = self.decoder.decode_image(test_image)

        # Assertions
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['auftrags_nr'], "NL-2581949")
        self.assertEqual(results[0]['paket_nr'], "2200212401")


class TestQRScanner(unittest.TestCase):
    """Tests für QR-Scanner Hauptklasse"""

    def setUp(self):
        """Setup für jeden Test"""
        self.scanner = QRScanner()

    @patch('src.scanner.camera_handler.CameraHandler')
    @patch('src.scanner.decoder.QRDecoder')
    def test_scanner_initialization(self, mock_decoder, mock_camera):
        """Test: Scanner-Initialisierung"""
        scanner = QRScanner()

        # Assertions
        self.assertIsNotNone(scanner)
        self.assertFalse(scanner.is_scanning)
        mock_camera.assert_called_once()
        mock_decoder.assert_called_once()

    def test_callback_registration(self):
        """Test: Callback-Registrierung"""
        # Mock-Callback
        mock_callback = Mock()

        # Callback registrieren
        self.scanner.register_callback(mock_callback)

        # Assertions
        self.assertIn(mock_callback, self.scanner.callbacks)

    @patch('threading.Thread')
    def test_start_scanning(self, mock_thread):
        """Test: Scanning starten"""
        # Mock konfigurieren
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Test
        self.scanner.start_scanning()

        # Assertions
        self.assertTrue(self.scanner.is_scanning)
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    def test_stop_scanning(self):
        """Test: Scanning stoppen"""
        # Setup
        self.scanner.is_scanning = True
        self.scanner.camera = MagicMock()

        # Test
        self.scanner.stop_scanning()

        # Assertions
        self.assertFalse(self.scanner.is_scanning)
        self.scanner.camera.release.assert_called_once()

    def test_process_qr_code(self):
        """Test: QR-Code verarbeiten"""
        # Mock-Callback
        mock_callback = Mock()
        self.scanner.register_callback(mock_callback)

        # Test-Daten
        qr_data = {
            'auftrags_nr': 'NL-123456',
            'paket_nr': '1234567890',
            'kunden_name': 'Test GmbH',
            'raw_data': 'VER^NL-123456^1^1234567890^1^ABC'
        }

        # Test
        self.scanner._process_qr_code(qr_data)

        # Assertions
        mock_callback.assert_called_once_with(qr_data)

    @patch('cv2.imread')
    def test_scan_from_file(self, mock_imread):
        """Test: QR-Code aus Datei scannen"""
        # Mock-Daten
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_imread.return_value = test_image

        # Mock-Decoder
        self.scanner.decoder = MagicMock()
        self.scanner.decoder.decode_image.return_value = [{
            'auftrags_nr': 'NL-999999',
            'paket_nr': '9999999999',
            'kunden_name': 'File Test',
            'raw_data': 'test'
        }]

        # Mock-Callback
        mock_callback = Mock()
        self.scanner.register_callback(mock_callback)

        # Test
        result = self.scanner.scan_from_file('test.png')

        # Assertions
        self.assertTrue(result)
        mock_imread.assert_called_once_with('test.png')
        mock_callback.assert_called_once()

    def test_duplicate_detection(self):
        """Test: Duplikat-Erkennung"""
        # Mock-Callback
        call_count = 0

        def counting_callback(data):
            nonlocal call_count
            call_count += 1

        self.scanner.register_callback(counting_callback)

        # Gleiche QR-Daten mehrmals verarbeiten
        qr_data = {
            'auftrags_nr': 'NL-123456',
            'paket_nr': '1234567890',
            'kunden_name': 'Test',
            'raw_data': 'duplicate_test'
        }

        # Ersten Scan
        self.scanner._process_qr_code(qr_data)
        self.assertEqual(call_count, 1)

        # Zweiten Scan (sollte ignoriert werden)
        self.scanner._process_qr_code(qr_data)
        self.assertEqual(call_count, 1)  # Sollte immer noch 1 sein

        # Nach Reset
        self.scanner.reset_duplicate_cache()
        self.scanner._process_qr_code(qr_data)
        self.assertEqual(call_count, 2)  # Jetzt sollte es 2 sein


class TestScannerIntegration(unittest.TestCase):
    """Integrationstests für Scanner-System"""

    @patch('cv2.VideoCapture')
    @patch('pyzbar.pyzbar.decode')
    def test_full_scan_workflow(self, mock_decode, mock_video_capture):
        """Test: Kompletter Scan-Workflow"""
        # Mock-Setup
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, test_frame)
        mock_video_capture.return_value = mock_cap

        # Mock QR-Code
        mock_qr = MagicMock()
        mock_qr.data = b"VER^NL-2581949^1165^2200212401^1^SBZ23C-11"
        mock_qr.polygon = [(10, 10), (100, 10), (100, 100), (10, 100)]
        mock_decode.return_value = [mock_qr]

        # Scanner erstellen
        scanner = QRScanner()

        # Callback für Ergebnisse
        scan_results = []
        scanner.register_callback(lambda data: scan_results.append(data))

        # Simuliere einen Scan-Durchlauf
        scanner.camera = CameraHandler()
        scanner._scan_frame()

        # Assertions
        self.assertEqual(len(scan_results), 1)
        self.assertEqual(scan_results[0]['auftrags_nr'], "NL-2581949")
        self.assertEqual(scan_results[0]['paket_nr'], "2200212401")


if __name__ == '__main__':
    unittest.main()