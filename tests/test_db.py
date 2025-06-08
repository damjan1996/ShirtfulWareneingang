#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimale Datenbank-Tests
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connection import get_connection
from models import User, Session, QrScan


class TestDatabase(unittest.TestCase):
    """Basis Datenbank-Tests"""

    def test_connection(self):
        """Test Datenbankverbindung"""
        conn = get_connection()
        self.assertIsNotNone(conn)
        conn.close()

    def test_user_query(self):
        """Test Benutzer-Abfrage"""
        user = User.get_by_epc("53004ECD68")
        self.assertIsNotNone(user)

    def test_session_create(self):
        """Test Session erstellen"""
        # Teste ob Session-Erstellung funktioniert
        user = User.get_by_epc("53004ECD68")
        if user:
            session = Session.create(user['ID'])
            self.assertIsNotNone(session)


if __name__ == '__main__':
    unittest.main()