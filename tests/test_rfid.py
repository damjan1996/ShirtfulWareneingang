#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimale RFID-Reader Tests
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hid_listener import HIDListener


class TestRFIDReader(unittest.TestCase):
    """Basis RFID-Reader Tests"""

    def setUp(self):
        """Setup für Tests"""
        self.listener = HIDListener()

    def test_listener_creation(self):
        """Test Listener-Erstellung"""
        self.assertIsNotNone(self.listener)

    def test_tag_validation(self):
        """Test Tag-Validierung"""
        # Test gültige Tags
        valid_tags = ["53004ECD68", "53004E114B", "53004E0D1B"]
        for tag in valid_tags:
            self.assertTrue(len(tag) == 10)
            # Prüfe ob Hex-String
            try:
                int(tag, 16)
                valid = True
            except:
                valid = False
            self.assertTrue(valid)

    def test_hex_to_decimal_conversion(self):
        """Test Hex zu Decimal Konvertierung"""
        test_cases = [
            ("53004ECD68", 355034188136),
            ("53004E114B", 355034182987),
        ]

        for hex_val, expected_dec in test_cases:
            decimal = int(hex_val, 16)
            self.assertEqual(decimal, expected_dec)


if __name__ == '__main__':
    unittest.main()