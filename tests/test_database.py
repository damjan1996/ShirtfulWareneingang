#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit-Tests für Datenbank-Funktionalität
"""

import unittest
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pyodbc

from src.database.connection import DatabaseConnection
from src.database.user_repository import UserRepository
from src.database.scan_repository import ScanRepository
from src.models.user import User
from src.models.scan_data import ScanData


class TestDatabaseConnection(unittest.TestCase):
    """Tests für die Datenbankverbindung"""

    def setUp(self):
        """Setup für jeden Test"""
        self.db_config = {
            'server': 'test_server',
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_pass'
        }

    @patch('pyodbc.connect')
    def test_connection_success(self, mock_connect):
        """Test: Erfolgreiche Datenbankverbindung"""
        # Mock konfigurieren
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        # Test
        db = DatabaseConnection(**self.db_config)
        result = db.connect()

        # Assertions
        self.assertTrue(result)
        self.assertIsNotNone(db.connection)
        mock_connect.assert_called()

    @patch('pyodbc.connect')
    def test_connection_failure(self, mock_connect):
        """Test: Fehlgeschlagene Datenbankverbindung"""
        # Mock konfigurieren
        mock_connect.side_effect = pyodbc.Error("Connection failed")

        # Test
        db = DatabaseConnection(**self.db_config)
        result = db.connect()

        # Assertions
        self.assertFalse(result)
        self.assertIsNone(db.connection)

    @patch('pyodbc.connect')
    def test_execute_query(self, mock_connect):
        """Test: Query-Ausführung"""
        # Mock konfigurieren
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # Test
        db = DatabaseConnection(**self.db_config)
        db.connect()

        query = "SELECT * FROM ScannBenutzer WHERE ID = ?"
        params = (1,)
        db.execute_query(query, params)

        # Assertions
        mock_cursor.execute.assert_called_with(query, params)

    @patch('pyodbc.connect')
    def test_close_connection(self, mock_connect):
        """Test: Verbindung schließen"""
        # Mock konfigurieren
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        # Test
        db = DatabaseConnection(**self.db_config)
        db.connect()
        db.close()

        # Assertions
        mock_connection.close.assert_called_once()


class TestUserRepository(unittest.TestCase):
    """Tests für User-Repository"""

    def setUp(self):
        """Setup für jeden Test"""
        self.mock_db = MagicMock()
        self.user_repo = UserRepository(self.mock_db)

    def test_get_user_by_rfid(self):
        """Test: Benutzer per RFID-Tag abrufen"""
        # Mock-Daten
        rfid_tag = "53004ECD68"
        epc_decimal = int(rfid_tag, 16)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            1, 'Test', 'User', 'test_user', 'Test User',
            'test@shirtful.com', epc_decimal, 0
        )
        self.mock_db.cursor.return_value = mock_cursor

        # Test
        user = self.user_repo.get_user_by_rfid(rfid_tag)

        # Assertions
        self.assertIsNotNone(user)
        self.assertEqual(user.id, 1)
        self.assertEqual(user.vorname, 'Test')
        self.assertEqual(user.nachname, 'User')
        self.assertEqual(user.rfid_tag, rfid_tag)

    def test_get_user_by_rfid_not_found(self):
        """Test: Benutzer nicht gefunden"""
        # Mock-Daten
        rfid_tag = "INVALID_TAG"

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        self.mock_db.cursor.return_value = mock_cursor

        # Test
        user = self.user_repo.get_user_by_rfid(rfid_tag)

        # Assertions
        self.assertIsNone(user)

    def test_create_user(self):
        """Test: Neuen Benutzer erstellen"""
        # Test-Daten
        user_data = {
            'vorname': 'Neuer',
            'nachname': 'Benutzer',
            'rfid_tag': '53004F3565'
        }

        mock_cursor = MagicMock()
        self.mock_db.cursor.return_value = mock_cursor
        self.mock_db.commit = MagicMock()

        # Test
        result = self.user_repo.create_user(user_data)

        # Assertions
        self.assertTrue(result)
        mock_cursor.execute.assert_called()
        self.mock_db.commit.assert_called()

    def test_update_user_status(self):
        """Test: Benutzerstatus aktualisieren"""
        # Test-Daten
        user_id = 1
        status = 1  # Aktiv

        mock_cursor = MagicMock()
        self.mock_db.cursor.return_value = mock_cursor
        self.mock_db.commit = MagicMock()

        # Test
        result = self.user_repo.update_user_status(user_id, status)

        # Assertions
        self.assertTrue(result)
        mock_cursor.execute.assert_called()
        self.mock_db.commit.assert_called()


class TestScanRepository(unittest.TestCase):
    """Tests für Scan-Repository"""

    def setUp(self):
        """Setup für jeden Test"""
        self.mock_db = MagicMock()
        self.scan_repo = ScanRepository(self.mock_db)

    def test_create_scan_session(self):
        """Test: Neue Scan-Session erstellen"""
        # Test-Daten
        user_id = 1
        arbeitsplatz = "WE-01"

        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 123
        self.mock_db.cursor.return_value = mock_cursor
        self.mock_db.commit = MagicMock()

        # Test
        session_id = self.scan_repo.create_scan_session(user_id, arbeitsplatz)

        # Assertions
        self.assertEqual(session_id, 123)
        mock_cursor.execute.assert_called()
        self.mock_db.commit.assert_called()

    def test_add_scan_position(self):
        """Test: Scan-Position hinzufügen"""
        # Test-Daten
        scan_data = ScanData(
            scan_kopf_id=123,
            auftrags_nr="NL-2581949",
            paket_nr="2200212401",
            kunden_name="Test GmbH"
        )

        mock_cursor = MagicMock()
        self.mock_db.cursor.return_value = mock_cursor
        self.mock_db.commit = MagicMock()

        # Test
        result = self.scan_repo.add_scan_position(scan_data)

        # Assertions
        self.assertTrue(result)
        mock_cursor.execute.assert_called()
        self.mock_db.commit.assert_called()

    def test_get_today_scans(self):
        """Test: Heutige Scans abrufen"""
        # Mock-Daten
        user_id = 1

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, 'NL-123456', '1234567890', 'Test GmbH', datetime.now()),
            (2, 'NL-789012', '0987654321', 'Muster AG', datetime.now())
        ]
        self.mock_db.cursor.return_value = mock_cursor

        # Test
        scans = self.scan_repo.get_today_scans(user_id)

        # Assertions
        self.assertEqual(len(scans), 2)
        self.assertEqual(scans[0]['auftrags_nr'], 'NL-123456')
        self.assertEqual(scans[1]['auftrags_nr'], 'NL-789012')

    def test_close_scan_session(self):
        """Test: Scan-Session beenden"""
        # Test-Daten
        session_id = 123

        mock_cursor = MagicMock()
        self.mock_db.cursor.return_value = mock_cursor
        self.mock_db.commit = MagicMock()

        # Test
        result = self.scan_repo.close_scan_session(session_id)

        # Assertions
        self.assertTrue(result)
        mock_cursor.execute.assert_called()
        self.mock_db.commit.assert_called()


class TestDatabaseIntegration(unittest.TestCase):
    """Integrationstests für Datenbank (nur wenn Testdatenbank verfügbar)"""

    @pytest.mark.integration
    def test_full_workflow(self):
        """Test: Kompletter Workflow (Verbindung -> Query -> Schließen)"""
        # Dieser Test wird nur ausgeführt, wenn eine Test-DB verfügbar ist
        # pytest tests/test_database.py -m integration
        pass


if __name__ == '__main__':
    unittest.main()