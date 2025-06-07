#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package Model für die Wareneingang-Anwendung
Repräsentiert ein Paket mit QR-Code-Daten
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from . import BaseModel, ValidationError

logger = logging.getLogger(__name__)


# ==============================================================================
# Enums
# ==============================================================================

class PackageStatus(Enum):
    """Status eines Pakets im System"""
    UNKNOWN = "unknown"
    SCANNED = "scanned"
    IN_WAREHOUSE = "in_warehouse"
    IN_PROCESSING = "in_processing"
    QUALITY_CHECK = "quality_check"
    READY_TO_SHIP = "ready_to_ship"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    RETURNED = "returned"
    LOST = "lost"
    DAMAGED = "damaged"


# ==============================================================================
# Package Model
# ==============================================================================

@dataclass
class Package(BaseModel):
    """
    Repräsentiert ein Paket mit allen relevanten Daten
    """

    # Pflichtfelder
    paketnummer: str
    auftragsnummer: str = ""

    # Optionale Felder
    kunde: str = ""
    kunden_id: str = ""
    kunden_name: str = ""

    # Tracking
    status: PackageStatus = PackageStatus.UNKNOWN
    scan_timestamp: datetime = field(default_factory=datetime.now)

    # QR-Code Daten
    raw_data: str = ""
    qr_format: str = ""  # delimited, json, url, key_value, regex

    # Zusätzliche Informationen
    artikelnummer: str = ""
    anzahl: int = 1
    gewicht: float = 0.0
    groesse: str = ""

    # Versand-Informationen
    versandart: str = ""
    tracking_nummer: str = ""
    lieferadresse: Dict[str, str] = field(default_factory=dict)

    # Metadaten
    erstellt_am: datetime = field(default_factory=datetime.now)
    aktualisiert_am: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Nach der Initialisierung"""
        # Paketnummer normalisieren
        self.paketnummer = self.paketnummer.strip()
        self.auftragsnummer = self.auftragsnummer.strip()

        # Kunde normalisieren
        if not self.kunden_name and self.kunde:
            self.kunden_name = self.kunde
        elif not self.kunde and self.kunden_name:
            self.kunde = self.kunden_name

    @classmethod
    def from_qr_code(cls, raw_data: str) -> "Package":
        """
        Erstellt ein Package-Objekt aus QR-Code-Daten

        Args:
            raw_data: Rohdaten des QR-Codes

        Returns:
            Package: Neues Package-Objekt
        """
        parsed_data = cls.parse_qr_code(raw_data)

        return cls(
            paketnummer=parsed_data.get("paket_nr", ""),
            auftragsnummer=parsed_data.get("auftrags_nr", ""),
            kunde=parsed_data.get("kunden_name", ""),
            kunden_id=parsed_data.get("kunden_id", ""),
            raw_data=raw_data,
            qr_format=parsed_data.get("format", "unknown"),
            artikelnummer=parsed_data.get("artikel_nr", ""),
            anzahl=parsed_data.get("anzahl", 1),
            status=PackageStatus.SCANNED
        )

    @staticmethod
    def parse_qr_code(raw_data: str) -> Dict[str, Any]:
        """
        Parst QR-Code-Daten in strukturierte Form

        Args:
            raw_data: Rohdaten des QR-Codes

        Returns:
            dict: Geparste Daten
        """
        result = {
            "auftrags_nr": "",
            "paket_nr": "",
            "kunden_name": "",
            "kunden_id": "",
            "artikel_nr": "",
            "anzahl": 1,
            "format": "unknown",
            "raw_data": raw_data
        }

        # 1. Spezielles ^ delimited Format (höchste Priorität)
        if '^' in raw_data:
            parsed = Package._parse_delimited_format(raw_data)
            if parsed["paket_nr"] or parsed["auftrags_nr"]:
                result.update(parsed)
                result["format"] = "delimited"
                return result

        # 2. JSON Format
        try:
            parsed = Package._parse_json_format(raw_data)
            if parsed["paket_nr"] or parsed["auftrags_nr"]:
                result.update(parsed)
                result["format"] = "json"
                return result
        except:
            pass

        # 3. URL Format
        if raw_data.startswith(("http://", "https://")):
            parsed = Package._parse_url_format(raw_data)
            if parsed["paket_nr"] or parsed["auftrags_nr"]:
                result.update(parsed)
                result["format"] = "url"
                return result

        # 4. Key-Value Format
        if ":" in raw_data or "=" in raw_data:
            parsed = Package._parse_key_value_format(raw_data)
            if parsed["paket_nr"] or parsed["auftrags_nr"]:
                result.update(parsed)
                result["format"] = "key_value"
                return result

        # 5. Regex Patterns
        parsed = Package._parse_regex_patterns(raw_data)
        if parsed["paket_nr"] or parsed["auftrags_nr"]:
            result.update(parsed)
            result["format"] = "regex"

        return result

    @staticmethod
    def _parse_delimited_format(data: str) -> Dict[str, Any]:
        """
        Parst Format: typ^auftragsnummer^kundennummer^paketnummer^anzahl^artikelnummer
        """
        result = {
            "auftrags_nr": "",
            "paket_nr": "",
            "kunden_id": "",
            "artikel_nr": "",
            "anzahl": 1
        }

        parts = data.split('^')

        if len(parts) >= 4:
            # Standardfelder
            result["auftrags_nr"] = parts[1] if len(parts) > 1 else ""
            result["kunden_id"] = parts[2] if len(parts) > 2 else ""
            result["paket_nr"] = parts[3] if len(parts) > 3 else ""

            # Optionale Felder
            if len(parts) > 4 and parts[4].isdigit():
                result["anzahl"] = int(parts[4])
            if len(parts) > 5:
                result["artikel_nr"] = parts[5]

            # Kundenname aus ID generieren
            if result["kunden_id"]:
                result["kunden_name"] = f"Kunde {result['kunden_id']}"

        return result

    @staticmethod
    def _parse_json_format(data: str) -> Dict[str, Any]:
        """Parst JSON-formatierte Daten"""
        result = {
            "auftrags_nr": "",
            "paket_nr": "",
            "kunden_name": "",
            "kunden_id": ""
        }

        try:
            json_data = json.loads(data)

            # Mapping von verschiedenen möglichen Feldnamen
            field_mappings = {
                "auftrags_nr": ["auftragsnummer", "auftrags_nr", "order", "orderid", "bestellung"],
                "paket_nr": ["paketnummer", "paket_nr", "package", "packageid", "sendung"],
                "kunden_name": ["kunde", "kundenname", "kunden_name", "customer", "client"],
                "kunden_id": ["kundennummer", "kunden_id", "customerid", "client_id"]
            }

            for result_key, possible_keys in field_mappings.items():
                for json_key in possible_keys:
                    if json_key in json_data:
                        result[result_key] = str(json_data[json_key])
                        break
                    # Case-insensitive Suche
                    for k, v in json_data.items():
                        if k.lower() == json_key.lower():
                            result[result_key] = str(v)
                            break

        except json.JSONDecodeError:
            pass

        return result

    @staticmethod
    def _parse_url_format(data: str) -> Dict[str, Any]:
        """Parst URL-formatierte Daten"""
        result = {
            "auftrags_nr": "",
            "paket_nr": "",
            "kunden_name": ""
        }

        try:
            from urllib.parse import urlparse, parse_qs

            parsed_url = urlparse(data)
            params = parse_qs(parsed_url.query)

            # Parameter-Mappings
            param_mappings = {
                "auftrags_nr": ["order", "auftrag", "orderid", "auftragsid", "o"],
                "paket_nr": ["package", "paket", "packageid", "paketid", "tracking", "p"],
                "kunden_name": ["customer", "kunde", "name", "customername", "kundenname", "c"]
            }

            for result_key, param_keys in param_mappings.items():
                for param_key in param_keys:
                    if param_key in params and params[param_key]:
                        result[result_key] = params[param_key][0]
                        break

        except Exception:
            pass

        return result

    @staticmethod
    def _parse_key_value_format(data: str) -> Dict[str, Any]:
        """Parst Key-Value formatierte Daten"""
        result = {
            "auftrags_nr": "",
            "paket_nr": "",
            "kunden_name": ""
        }

        # Verschiedene Trennzeichen unterstützen
        lines = data.replace(';', '\n').replace(',', '\n').split('\n')

        key_mappings = {
            "auftrags_nr": ["auftrag", "order", "bestellung", "auftrags-nr", "auftragsnr", "referenz"],
            "paket_nr": ["paket", "package", "sendung", "paket-nr", "paketnr", "tracking"],
            "kunden_name": ["kunde", "customer", "client", "name", "kundenname"]
        }

        for line in lines:
            # Sowohl : als auch = als Trenner
            for separator in [':', '=']:
                if separator in line:
                    parts = line.split(separator, 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower()
                        value = parts[1].strip()

                        for result_key, possible_keys in key_mappings.items():
                            if any(possible_key in key for possible_key in possible_keys):
                                result[result_key] = value
                                break
                    break

        return result

    @staticmethod
    def _parse_regex_patterns(data: str) -> Dict[str, Any]:
        """Parst Daten mit Regex-Patterns"""
        result = {
            "auftrags_nr": "",
            "paket_nr": "",
            "kunden_name": ""
        }

        # Auftragsnummer Patterns
        order_patterns = [
            r'[A-Z]{2}-\d{6,}',  # z.B. NL-2581949
            r'[A-Z]{3}\d{6,}',  # z.B. ABC123456
            r'ORD-\d{6,}',  # z.B. ORD-123456
            r'#\d{6,}',  # z.B. #123456
            r'Auftrag:\s*(\S+)',  # z.B. Auftrag: 12345
            r'Order:\s*(\S+)',  # z.B. Order: 12345
            r'Referenz:\s*(\S+)'  # z.B. Referenz: ABC123
        ]

        for pattern in order_patterns:
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                result["auftrags_nr"] = match.group(0) if match.lastindex is None else match.group(1)
                break

        # Paketnummer Patterns
        package_patterns = [
            r'\d{10,18}',  # 10-18 stellige Nummer
            r'[A-Z]{2}\d{9,}',  # z.B. DE123456789
            r'Tracking:\s*(\d+)',  # z.B. Tracking: 123456
            r'Paket:\s*(\S+)',  # z.B. Paket: ABC123
        ]

        for pattern in package_patterns:
            match = re.search(pattern, data)
            if match:
                result["paket_nr"] = match.group(0) if match.lastindex is None else match.group(1)
                break

        # Kundenname Patterns
        customer_patterns = [
            r'Kunde:\s*([^\n\r,;]+)',  # z.B. Kunde: Max Mustermann
            r'Customer:\s*([^\n\r,;]+)',  # z.B. Customer: John Doe
            r'An:\s*([^\n\r,;]+)',  # z.B. An: Firma GmbH
            r'Empfänger:\s*([^\n\r,;]+)',  # z.B. Empfänger: Test AG
        ]

        for pattern in customer_patterns:
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                result["kunden_name"] = match.group(1).strip()
                break

        return result

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validiert die Paketdaten

        Returns:
            tuple: (is_valid, errors)
        """
        errors = []

        # Paketnummer ist Pflicht
        if not self.paketnummer:
            errors.append("Paketnummer fehlt")
        elif not re.match(r'^[\w\-\.]+$', self.paketnummer):
            errors.append("Paketnummer enthält ungültige Zeichen")

        # Auftragsnummer validieren (optional)
        if self.auftragsnummer and not re.match(r'^[\w\-\.]+$', self.auftragsnummer):
            errors.append("Auftragsnummer enthält ungültige Zeichen")

        # Anzahl validieren
        if self.anzahl < 1:
            errors.append("Anzahl muss mindestens 1 sein")

        # Gewicht validieren
        if self.gewicht < 0:
            errors.append("Gewicht kann nicht negativ sein")

        return len(errors) == 0, errors

    def update_status(self, new_status: PackageStatus, user: str = "System"):
        """
        Aktualisiert den Paketstatus

        Args:
            new_status: Neuer Status
            user: Benutzer der die Änderung durchführt
        """
        old_status = self.status
        self.status = new_status
        self.aktualisiert_am = datetime.now()

        logger.info(
            f"Paket {self.paketnummer} Status geändert: "
            f"{old_status.value} -> {new_status.value} (durch {user})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        data = super().to_dict()

        # Enum zu String
        if "status" in data and isinstance(data["status"], PackageStatus):
            data["status"] = data["status"].value

        # Datetime zu String
        for field in ["scan_timestamp", "erstellt_am", "aktualisiert_am"]:
            if field in data and isinstance(data[field], datetime):
                data[field] = data[field].isoformat()

        return data

    def __str__(self):
        """String-Repräsentation"""
        return f"Paket {self.paketnummer} (Auftrag: {self.auftragsnummer or 'N/A'})"


# ==============================================================================
# Package Validation
# ==============================================================================

class PackageValidation:
    """Validierungs-Klasse für Paketdaten"""

    @staticmethod
    def validate(package_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validiert Paketdaten

        Args:
            package_data: Zu validierende Daten

        Returns:
            tuple: (is_valid, errors)
        """
        errors = []

        # Pflichtfelder
        required_fields = ["paketnummer"]
        for field in required_fields:
            if field not in package_data or not package_data[field]:
                errors.append(f"Feld '{field}' ist erforderlich")

        # Paketnummer Format
        if "paketnummer" in package_data:
            paket_nr = package_data["paketnummer"]
            if not isinstance(paket_nr, str):
                errors.append("Paketnummer muss ein String sein")
            elif len(paket_nr) < 5:
                errors.append("Paketnummer zu kurz (min. 5 Zeichen)")
            elif len(paket_nr) > 50:
                errors.append("Paketnummer zu lang (max. 50 Zeichen)")
            elif not re.match(r'^[\w\-\.]+$', paket_nr):
                errors.append("Paketnummer enthält ungültige Zeichen")

        # Auftragsnummer Format (optional)
        if "auftragsnummer" in package_data and package_data["auftragsnummer"]:
            auftrags_nr = package_data["auftragsnummer"]
            if not isinstance(auftrags_nr, str):
                errors.append("Auftragsnummer muss ein String sein")
            elif len(auftrags_nr) > 50:
                errors.append("Auftragsnummer zu lang (max. 50 Zeichen)")
            elif not re.match(r'^[\w\-\.]+$', auftrags_nr):
                errors.append("Auftragsnummer enthält ungültige Zeichen")

        # Anzahl validieren
        if "anzahl" in package_data:
            try:
                anzahl = int(package_data["anzahl"])
                if anzahl < 1:
                    errors.append("Anzahl muss mindestens 1 sein")
                elif anzahl > 9999:
                    errors.append("Anzahl zu groß (max. 9999)")
            except (ValueError, TypeError):
                errors.append("Anzahl muss eine ganze Zahl sein")

        # Gewicht validieren
        if "gewicht" in package_data:
            try:
                gewicht = float(package_data["gewicht"])
                if gewicht < 0:
                    errors.append("Gewicht kann nicht negativ sein")
                elif gewicht > 99999:
                    errors.append("Gewicht zu groß (max. 99999 kg)")
            except (ValueError, TypeError):
                errors.append("Gewicht muss eine Zahl sein")

        return len(errors) == 0, errors

    @staticmethod
    def sanitize(package_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bereinigt Paketdaten

        Args:
            package_data: Zu bereinigende Daten

        Returns:
            dict: Bereinigte Daten
        """
        sanitized = package_data.copy()

        # Strings trimmen
        string_fields = [
            "paketnummer", "auftragsnummer", "kunde", "kunden_name",
            "artikelnummer", "versandart", "tracking_nummer"
        ]

        for field in string_fields:
            if field in sanitized and isinstance(sanitized[field], str):
                sanitized[field] = sanitized[field].strip()

        # Zahlen konvertieren
        if "anzahl" in sanitized:
            try:
                sanitized["anzahl"] = int(sanitized["anzahl"])
            except (ValueError, TypeError):
                sanitized["anzahl"] = 1

        if "gewicht" in sanitized:
            try:
                sanitized["gewicht"] = float(sanitized["gewicht"])
            except (ValueError, TypeError):
                sanitized["gewicht"] = 0.0

        return sanitized