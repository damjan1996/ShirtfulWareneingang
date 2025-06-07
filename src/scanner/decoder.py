#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR-Code Decoder
===============

Dekodiert QR-Codes und extrahiert strukturierte Daten
aus Versandetiketten.
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pyzbar import pyzbar
import cv2

logger = logging.getLogger(__name__)


class QRDecoder:
    """
    Dekodiert QR-Codes und extrahiert Paketinformationen

    Unterstützt verschiedene QR-Code-Formate:
    - Caret-getrennt (^): typ^auftragsnummer^kundennummer^paketnummer
    - JSON-Format
    - Key-Value-Paare
    - URL-Format
    """

    def __init__(self):
        """Initialisiert den QR-Decoder"""
        self.last_positions = []
        self.decode_history = []
        self.max_history = 100

        logger.info("QR-Decoder initialisiert")

    def decode_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Dekodiert alle QR-Codes in einem Frame

        Args:
            frame: Das zu dekodierende Bild

        Returns:
            Liste mit dekodierten QR-Code-Daten
        """
        if frame is None:
            return []

        decoded_objects = []
        self.last_positions = []

        try:
            # Bild vorverarbeiten für bessere Erkennung
            processed = self._preprocess_frame(frame)

            # QR-Codes dekodieren
            qr_codes = pyzbar.decode(processed)

            for qr in qr_codes:
                # Position speichern
                points = qr.polygon
                if points and len(points) > 0:
                    hull = np.array([point for point in points], dtype=np.int32)
                    hull = hull.reshape((-1, 1, 2))
                    self.last_positions.append(hull)

                # Daten dekodieren
                try:
                    raw_data = qr.data.decode('utf-8', errors='ignore')
                except:
                    raw_data = str(qr.data)

                # Daten parsen
                parsed_data = self.parse_qr_data(raw_data)
                parsed_data['raw_data'] = raw_data
                parsed_data['timestamp'] = self._get_timestamp()
                parsed_data['position'] = qr.rect

                decoded_objects.append(parsed_data)

                # Zu Historie hinzufügen
                self._add_to_history(parsed_data)

            if decoded_objects:
                logger.info(f"{len(decoded_objects)} QR-Code(s) dekodiert")

        except Exception as e:
            logger.error(f"Fehler beim Dekodieren: {e}")

        return decoded_objects

    def parse_qr_data(self, raw_data: str) -> Dict[str, Any]:
        """
        Parst die Rohdaten eines QR-Codes

        Args:
            raw_data: Die zu parsenden Rohdaten

        Returns:
            Dict mit extrahierten Informationen
        """
        result = {
            'auftrags_nr': '',
            'paket_nr': '',
            'kunden_name': '',
            'zusatz_info': '',
            'format': 'unknown'
        }

        # 1. Caret-getrenntes Format (höchste Priorität)
        if '^' in raw_data:
            parsed = self._parse_caret_format(raw_data)
            if parsed['auftrags_nr'] or parsed['paket_nr']:
                result.update(parsed)
                result['format'] = 'caret'
                return result

        # 2. JSON-Format
        if self._try_parse_json(raw_data, result):
            result['format'] = 'json'
            return result

        # 3. Key-Value-Format
        if self._try_parse_key_value(raw_data, result):
            result['format'] = 'key_value'
            return result

        # 4. URL-Format
        if self._try_parse_url(raw_data, result):
            result['format'] = 'url'
            return result

        # 5. Regex-basierte Erkennung
        self._try_parse_regex(raw_data, result)
        if result['auftrags_nr'] or result['paket_nr']:
            result['format'] = 'regex'

        return result

    def _parse_caret_format(self, data: str) -> Dict[str, Any]:
        """
        Parst das Caret-getrennte Format
        Format: typ^auftragsnummer^kundennummer^paketnummer^anzahl^artikelnummer
        """
        result = {
            'auftrags_nr': '',
            'paket_nr': '',
            'kunden_name': '',
            'zusatz_info': ''
        }

        parts = data.split('^')

        if len(parts) >= 4:
            # Standard-Positionen
            result['auftrags_nr'] = parts[1].strip()
            result['paket_nr'] = parts[3].strip()

            # Kundennummer/Name
            if len(parts) > 2 and parts[2]:
                result['kunden_name'] = f"Kunden-ID: {parts[2].strip()}"

            # Zusatzinformationen
            zusatz = []
            if len(parts) > 4 and parts[4]:
                zusatz.append(f"Anzahl: {parts[4]}")
            if len(parts) > 5 and parts[5]:
                zusatz.append(f"Artikel: {parts[5]}")

            if zusatz:
                result['zusatz_info'] = ", ".join(zusatz)

        return result

    def _try_parse_json(self, data: str, result: Dict[str, Any]) -> bool:
        """Versucht JSON-Parsing"""
        try:
            json_data = json.loads(data)

            # Bekannte Felder mappen
            field_mappings = {
                'auftrags_nr': ['auftrag', 'order', 'bestellung', 'auftrags_nr',
                                'auftragsnummer', 'order_id', 'orderid'],
                'paket_nr': ['paket', 'package', 'sendung', 'paket_nr',
                             'paketnummer', 'tracking', 'package_id'],
                'kunden_name': ['kunde', 'customer', 'client', 'name',
                                'kundenname', 'customer_name']
            }

            for key, value in json_data.items():
                key_lower = key.lower()

                for result_key, possible_keys in field_mappings.items():
                    if any(pk in key_lower for pk in possible_keys):
                        result[result_key] = str(value)
                        break

            return True

        except json.JSONDecodeError:
            return False

    def _try_parse_key_value(self, data: str, result: Dict[str, Any]) -> bool:
        """Versucht Key-Value-Parsing"""
        lines = data.split('\n')
        found_any = False

        key_mappings = {
            'auftrags_nr': ['auftrag', 'order', 'bestellung', 'referenz'],
            'paket_nr': ['paket', 'package', 'sendung', 'tracking'],
            'kunden_name': ['kunde', 'customer', 'name']
        }

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                for result_key, possible_keys in key_mappings.items():
                    if any(pk in key for pk in possible_keys):
                        result[result_key] = value
                        found_any = True
                        break

        return found_any

    def _try_parse_url(self, data: str, result: Dict[str, Any]) -> bool:
        """Versucht URL-Parsing"""
        if not data.startswith(('http://', 'https://')):
            return False

        try:
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(data)
            params = parse_qs(parsed_url.query)

            param_mappings = {
                'auftrags_nr': ['order', 'auftrag', 'orderid'],
                'paket_nr': ['package', 'paket', 'tracking'],
                'kunden_name': ['customer', 'kunde', 'name']
            }

            found_any = False
            for result_key, param_keys in param_mappings.items():
                for param_key in param_keys:
                    if param_key in params:
                        result[result_key] = params[param_key][0]
                        found_any = True
                        break

            return found_any

        except Exception:
            return False

    def _try_parse_regex(self, data: str, result: Dict[str, Any]):
        """Versucht Regex-basierte Erkennung"""
        # Auftragsnummer: Format XX-XXXXXXX
        auftrags_match = re.search(r'\b[A-Z]{2}-\d{5,}\b', data)
        if auftrags_match:
            result['auftrags_nr'] = auftrags_match.group(0)

        # Paketnummer: Lange Zahlenfolge (10-20 Stellen)
        paket_match = re.search(r'\b\d{10,20}\b', data)
        if paket_match:
            result['paket_nr'] = paket_match.group(0)

        # Alternative Patterns
        if not result['auftrags_nr']:
            # Referenz-Pattern
            ref_match = re.search(r'(?:Referenz|Ref|Order):\s*([A-Z0-9-]+)',
                                  data, re.IGNORECASE)
            if ref_match:
                result['auftrags_nr'] = ref_match.group(1)

        if not result['paket_nr']:
            # Tracking-Pattern
            track_match = re.search(r'(?:Tracking|Track|Sendung):\s*(\d+)',
                                    data, re.IGNORECASE)
            if track_match:
                result['paket_nr'] = track_match.group(1)

    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Vorverarbeitung des Frames für bessere QR-Code-Erkennung

        Args:
            frame: Original-Frame

        Returns:
            Vorverarbeitetes Frame
        """
        # In Graustufen konvertieren
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Kontrast erhöhen
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        return enhanced

    def _add_to_history(self, data: Dict[str, Any]):
        """Fügt Daten zur Historie hinzu"""
        self.decode_history.append(data.copy())

        # Größe begrenzen
        if len(self.decode_history) > self.max_history:
            self.decode_history = self.decode_history[-self.max_history:]

    def _get_timestamp(self) -> str:
        """Gibt aktuellen Zeitstempel zurück"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_last_positions(self) -> List[np.ndarray]:
        """Gibt die Positionen der zuletzt erkannten QR-Codes zurück"""
        return self.last_positions

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Gibt die Decode-Historie zurück

        Args:
            limit: Maximale Anzahl Einträge

        Returns:
            Liste mit historischen Dekodierungen
        """
        return self.decode_history[-limit:]

    def clear_history(self):
        """Löscht die Decode-Historie"""
        self.decode_history.clear()
        logger.debug("Decode-Historie gelöscht")


# Test-Funktion
if __name__ == "__main__":
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    decoder = QRDecoder()

    # Test-Daten
    test_cases = [
        # Caret-Format
        "PAK^NL-2581949^123456^4063025047302^1^ABC123",
        # JSON-Format
        '{"order_id": "DE-1234567", "package": "9876543210", "customer": "Max Mustermann"}',
        # Key-Value-Format
        "Auftrag: AT-9876543\nPaket-Nr: 1234567890123456\nKunde: Test GmbH",
        # URL-Format
        "https://tracking.example.com?order=FR-5555555&package=111222333444",
        # Unstrukturiert
        "Referenz: UK-7777777 Tracking: 999888777666555"
    ]

    print("🔍 QR-Decoder Test")
    print("=" * 60)

    for i, test_data in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_data[:50]}...")
        result = decoder.parse_qr_data(test_data)

        print(f"  Format: {result['format']}")
        print(f"  Auftrag: {result['auftrags_nr'] or '-'}")
        print(f"  Paket: {result['paket_nr'] or '-'}")
        print(f"  Kunde: {result['kunden_name'] or '-'}")
        if result['zusatz_info']:
            print(f"  Zusatz: {result['zusatz_info']}")