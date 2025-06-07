#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit-Tests für RFID-Funktionalität
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import threading
import time
from pynput import keyboard

from src.rfid.reader import RFIDReader
from src.rfid.hid_listener import HIDListener
from src.rfid.tag_validator import TagValidator


class TestRFIDReader(unittest.TestCase):
    """Tests für RFID-Reader Hauptklasse"""

    def setUp(self):
        """Setup für jeden Test"""
        self.rfid_reader = RFIDReader()

    @patch('src.rfid.hid_listener.HIDListener')
    def test_initialization(self, mock_hid_listener):
        """Test: RFID-Reader Initialisierung"""
        reader = RFIDReader()

        # Assertions
        self.assertIsNotNone(reader)
        self.assertFalse(reader.is_running)
        self.assertEqual(reader.current_buffer, "")
        mock_hid_listener.assert_called_once()

    def test_tag_callback_registration(self):
        """Test: Callback-Registrierung"""
        # Mock-Callback
        mock_callback = Mock()

        # Callback registrieren
        self.rfid_reader.register_callback(mock_callback)

        # Assertions
        self.assertIn(mock_callback, self.rfid_reader.callbacks)

    def test_tag_processing(self):
        """Test: Tag-Verarbeitung"""
        # Mock-Callback
        mock_callback = Mock()
        self.rfid_reader.register_callback(mock_callback)

        # Simuliere Tag-Eingabe
        test_tag = "53004ECD68"
        self.rfid_reader._process_tag(test_tag)

        # Assertions
        mock_callback.assert_called_once_with(test_tag)

    @patch('threading.Thread')
    def test_start_monitoring(self, mock_thread):
        """Test: Monitoring starten"""
        # Mock-Thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Test
        self.rfid_reader.start_monitoring()

        # Assertions
        self.assertTrue(self.rfid_reader.is_running)
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    def test_stop_monitoring(self):
        """Test: Monitoring stoppen"""
        # Setup
        self.rfid_reader.is_running = True
        self.rfid_reader.listener = MagicMock()

        # Test
        self.rfid_reader.stop_monitoring()

        # Assertions
        self.assertFalse(self.rfid_reader.is_running)
        self.rfid_reader.listener.stop.assert_called_once()


class TestHIDListener(unittest.TestCase):
    """Tests für HID-Listener (Keyboard Wedge)"""

    def setUp(self):
        """Setup für jeden Test"""
        self.hid_listener = HIDListener()

    def test_key_buffer_management(self):
        """Test: Tastatur-Buffer-Verwaltung"""
        # Simuliere Tasteneingaben
        test_input = "53004ECD68"

        for char in test_input:
            self.hid_listener._add_to_buffer(char)

        # Assertions
        self.assertEqual(self.hid_listener.buffer, test_input)

    def test_enter_key_processing(self):
        """Test: Enter-Taste verarbeitet Buffer"""
        # Mock-Callback
        mock_callback = Mock()
        self.hid_listener.on_tag_read = mock_callback

        # Buffer füllen
        test_tag = "53004ECD68"
        self.hid_listener.buffer = test_tag

        # Enter simulieren
        self.hid_listener._process_buffer()

        # Assertions
        mock_callback.assert_called_once_with(test_tag)
        self.assertEqual(self.hid_listener.buffer, "")

    @patch('pynput.keyboard.Listener')
    def test_listener_start(self, mock_listener):
        """Test: Listener starten"""
        # Mock konfigurieren
        mock_listener_instance = MagicMock()
        mock_listener.return_value = mock_listener_instance

        # Test
        self.hid_listener.start()

        # Assertions
        mock_listener.assert_called_once()
        mock_listener_instance.start.assert_called_once()

    def test_invalid_character_handling(self):
        """Test: Ungültige Zeichen werden ignoriert"""
        # Gültige Zeichen hinzufügen
        self.hid_listener._add_to_buffer("5")
        self.hid_listener._add_to_buffer("3")

        # Ungültige Zeichen (sollten ignoriert werden)
        self.hid_listener._add_to_buffer("!")
        self.hid_listener._add_to_buffer("@")

        # Weitere gültige Zeichen
        self.hid_listener._add_to_buffer("0")
        self.hid_listener._add_to_buffer("A")

        # Assertions
        self.assertEqual(self.hid_listener.buffer, "530A")

    def test_buffer_overflow_protection(self):
        """Test: Buffer-Überlauf-Schutz"""
        # Buffer mit zu vielen Zeichen füllen
        long_input = "A" * 100  # Sehr lange Eingabe

        for char in long_input:
            self.hid_listener._add_to_buffer(char)

        # Assertions (Buffer sollte begrenzt sein)
        self.assertLessEqual(len(self.hid_listener.buffer), 50)


class TestTagValidator(unittest.TestCase):
    """Tests für Tag-Validierung"""

    def setUp(self):
        """Setup für jeden Test"""
        self.mock_db = MagicMock()
        self.validator = TagValidator(self.mock_db)

    def test_valid_tag_format(self):
        """Test: Gültiges Tag-Format"""
        # Gültige Tags
        valid_tags = [
            "53004ECD68",
            "53004E114B",
            "ABCDEF1234",
            "1234567890"
        ]

        for tag in valid_tags:
            result = self.validator.is_valid_format(tag)
            self.assertTrue(result, f"Tag {tag} sollte gültig sein")

    def test_invalid_tag_format(self):
        """Test: Ungültiges Tag-Format"""
        # Ungültige Tags
        invalid_tags = [
            "",  # Leer
            "12345",  # Zu kurz
            "12345678901234567890",  # Zu lang
            "GHIJKL1234",  # Ungültige Hex-Zeichen
            "12 34 56 78",  # Leerzeichen
            None  # None
        ]

        for tag in invalid_tags:
            result = self.validator.is_valid_format(tag)
            self.assertFalse(result, f"Tag {tag} sollte ungültig sein")

    def test_tag_exists_in_database(self):
        """Test: Tag in Datenbank vorhanden"""
        # Mock-Daten
        test_tag = "53004ECD68"

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)  # Tag existiert
        self.mock_db.cursor.return_value = mock_cursor

        # Test
        result = self.validator.tag_exists(test_tag)

        # Assertions
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()

    def test_tag_not_in_database(self):
        """Test: Tag nicht in Datenbank"""
        # Mock-Daten
        test_tag = "NONEXISTENT"

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Tag existiert nicht
        self.mock_db.cursor.return_value = mock_cursor

        # Test
        result = self.validator.tag_exists(test_tag)

        # Assertions
        self.assertFalse(result)

    def test_get_user_info(self):
        """Test: Benutzerinformationen abrufen"""
        # Mock-Daten
        test_tag = "53004ECD68"

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            1, 'Test', 'User', 'Test User', 'test@shirtful.com'
        )
        self.mock_db.cursor.return_value = mock_cursor

        # Test
        user_info = self.validator.get_user_info(test_tag)

        # Assertions
        self.assertIsNotNone(user_info)
        self.assertEqual(user_info['id'], 1)
        self.assertEqual(user_info['vorname'], 'Test')
        self.assertEqual(user_info['nachname'], 'User')


class TestRFIDIntegration(unittest.TestCase):
    """Integrationstests für RFID-System"""

    @patch('src.rfid.hid_listener.keyboard.Listener')
    def test_full_rfid_workflow(self, mock_keyboard_listener):
        """Test: Kompletter RFID-Workflow"""
        # Mock-Setup
        mock_listener_instance = MagicMock()
        mock_keyboard_listener.return_value = mock_listener_instance

        # Callback für Tag-Erkennung
        detected_tags = []

        def tag_callback(tag):
            detected_tags.append(tag)

        # RFID-Reader erstellen
        reader = RFIDReader()
        reader.register_callback(tag_callback)

        # Simuliere Tag-Scan
        test_tag = "53004ECD68"
        reader._process_tag(test_tag)

        # Assertions
        self.assertEqual(len(detected_tags), 1)
        self.assertEqual(detected_tags[0], test_tag)

    def test_multiple_callbacks(self):
        """Test: Mehrere Callbacks gleichzeitig"""
        # Multiple Callbacks
        callback_results = []

        def callback1(tag):
            callback_results.append(f"CB1: {tag}")

        def callback2(tag):
            callback_results.append(f"CB2: {tag}")

        # Setup
        reader = RFIDReader()
        reader.register_callback(callback1)
        reader.register_callback(callback2)

        # Test
        test_tag = "53004ECD68"
        reader._process_tag(test_tag)

        # Assertions
        self.assertEqual(len(callback_results), 2)
        self.assertIn(f"CB1: {test_tag}", callback_results)
        self.assertIn(f"CB2: {test_tag}", callback_results)


if __name__ == '__main__':
    unittest.main()