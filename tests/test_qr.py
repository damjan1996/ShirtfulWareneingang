#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimale QR-Scanner Tests
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qr_scanner import QRScanner


class TestQRScanner(unittest.TestCase):
    """Basis QR-Scanner Tests"""

    def setUp(self):
        """Setup für Tests"""
        self.scanner = QRScanner(camera_index=0)

    def test_scanner_creation(self):
        """Test Scanner-Erstellung"""
        self.assertIsNotNone(self.scanner)

    def test_payload_validation(self):
        """Test Payload-Validierung"""
        # Test verschiedene Payload-Formate
        test_payloads = [
            '{"kunde":"ABC","auftrag":"12345"}',
            'Kunde:ABC^Auftrag:12345',
            'Einfacher Text',
            '{"invalid_json": }'
        ]

        for payload in test_payloads:
            result = self.scanner.validate_payload(payload)
            self.assertIsNotNone(result)

    def tearDown(self):
        """Cleanup nach Tests"""
        if hasattr(self.scanner, 'release'):
            self.scanner.release()


if __name__ == '__main__':
    unittest.main()