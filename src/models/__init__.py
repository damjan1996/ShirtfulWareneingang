#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Models Package für die Wareneingang-Anwendung

Dieses Package enthält die Datenmodelle für:
- Benutzer (User)
- Scan-Daten (ScanData)
- Pakete (Package)

Die Models implementieren Datenvalidierung und Business-Logik
"""

from typing import TYPE_CHECKING

# Versionsinformation
__version__ = "1.0.0"
__author__ = "Shirtful GmbH"

# Lazy imports für bessere Performance
if TYPE_CHECKING:
    from .user import User, UserRole, UserStatus
    from .scan_data import ScanData, ScanSession, ScanPosition, ScanType
    from .package import Package, PackageStatus, PackageValidation

# Package-Level Imports
__all__ = [
    # User Model
    "User",
    "UserRole",
    "UserStatus",
    "create_user",
    "validate_rfid_tag",

    # Scan Models
    "ScanData",
    "ScanSession",
    "ScanPosition",
    "ScanType",
    "create_scan_session",
    "create_scan_position",

    # Package Model
    "Package",
    "PackageStatus",
    "PackageValidation",
    "parse_qr_code",
    "validate_package_data",

    # Exceptions
    "ModelError",
    "ValidationError",
    "DuplicateError",
    "NotFoundError",
]


# ==============================================================================
# Exceptions
# ==============================================================================

class ModelError(Exception):
    """Basis-Exception für Model-Fehler"""
    pass


class ValidationError(ModelError):
    """Fehler bei der Datenvalidierung"""
    pass


class DuplicateError(ModelError):
    """Fehler bei doppelten Einträgen"""
    pass


class NotFoundError(ModelError):
    """Fehler wenn Daten nicht gefunden wurden"""
    pass


# ==============================================================================
# Helper Functions
# ==============================================================================

def create_user(vorname: str, nachname: str, rfid_tag: str,
                email: str = None, **kwargs):
    """
    Factory-Funktion zum Erstellen eines Benutzers

    Args:
        vorname: Vorname des Benutzers
        nachname: Nachname des Benutzers
        rfid_tag: RFID-Tag (Hex-String)
        email: E-Mail-Adresse (optional)
        **kwargs: Weitere Benutzer-Attribute

    Returns:
        User: Neues User-Objekt

    Raises:
        ValidationError: Bei ungültigen Daten
    """
    from .user import User
    return User(
        vorname=vorname,
        nachname=nachname,
        rfid_tag=rfid_tag,
        email=email,
        **kwargs
    )


def validate_rfid_tag(rfid_tag: str) -> bool:
    """
    Validiert einen RFID-Tag

    Args:
        rfid_tag: RFID-Tag als Hex-String

    Returns:
        bool: True wenn gültig
    """
    from .user import User
    return User.validate_rfid_tag(rfid_tag)


def create_scan_session(user_id: int, epc: int, scan_type_id: int,
                        arbeitsplatz: str = None, **kwargs):
    """
    Factory-Funktion zum Erstellen einer Scan-Session

    Args:
        user_id: Benutzer-ID
        epc: EPC (RFID als Decimal)
        scan_type_id: Typ der Scan-Session
        arbeitsplatz: Arbeitsplatz-Bezeichnung
        **kwargs: Weitere Session-Attribute

    Returns:
        ScanSession: Neue Session
    """
    from .scan_data import ScanSession
    return ScanSession(
        user_id=user_id,
        epc=epc,
        scan_type_id=scan_type_id,
        arbeitsplatz=arbeitsplatz,
        **kwargs
    )


def create_scan_position(session_id: int, qr_data: dict, **kwargs):
    """
    Factory-Funktion zum Erstellen einer Scan-Position

    Args:
        session_id: Session-ID
        qr_data: Gescannte QR-Code-Daten
        **kwargs: Weitere Positions-Attribute

    Returns:
        ScanPosition: Neue Position
    """
    from .scan_data import ScanPosition
    return ScanPosition(
        session_id=session_id,
        kunde=qr_data.get("kunden_name"),
        auftragsnummer=qr_data.get("auftrags_nr"),
        paketnummer=qr_data.get("paket_nr"),
        zusatzinfo=qr_data.get("raw_data"),
        **kwargs
    )


def parse_qr_code(raw_data: str) -> dict:
    """
    Parst QR-Code-Daten

    Args:
        raw_data: Rohdaten des QR-Codes

    Returns:
        dict: Geparste Daten
    """
    from .package import Package
    return Package.parse_qr_code(raw_data)


def validate_package_data(package_data: dict) -> tuple:
    """
    Validiert Paketdaten

    Args:
        package_data: Zu validierende Paketdaten

    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    from .package import PackageValidation
    return PackageValidation.validate(package_data)


# ==============================================================================
# Model Registry
# ==============================================================================

class ModelRegistry:
    """
    Zentrale Registry für alle Models
    Ermöglicht dynamisches Laden und Caching
    """

    _models = {}
    _instances = {}

    @classmethod
    def register(cls, model_name: str, model_class):
        """Registriert ein Model"""
        cls._models[model_name] = model_class

    @classmethod
    def get(cls, model_name: str):
        """Holt ein registriertes Model"""
        return cls._models.get(model_name)

    @classmethod
    def create_instance(cls, model_name: str, **kwargs):
        """Erstellt eine Model-Instanz"""
        model_class = cls.get(model_name)
        if model_class:
            return model_class(**kwargs)
        raise ValueError(f"Unbekanntes Model: {model_name}")

    @classmethod
    def cache_instance(cls, key: str, instance):
        """Cached eine Model-Instanz"""
        cls._instances[key] = instance

    @classmethod
    def get_cached(cls, key: str):
        """Holt eine gecachte Instanz"""
        return cls._instances.get(key)

    @classmethod
    def clear_cache(cls):
        """Leert den Instance-Cache"""
        cls._instances.clear()


# ==============================================================================
# Model Base Class
# ==============================================================================

class BaseModel:
    """
    Basis-Klasse für alle Models
    Implementiert gemeinsame Funktionalität
    """

    def __init__(self, **kwargs):
        """Initialisiert das Model mit Keyword-Argumenten"""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> dict:
        """Konvertiert das Model zu einem Dictionary"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }

    def validate(self) -> tuple:
        """
        Validiert das Model

        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        # Muss in Subklassen implementiert werden
        raise NotImplementedError("validate() muss implementiert werden")

    def __repr__(self):
        """String-Repräsentation"""
        class_name = self.__class__.__name__
        attrs = ', '.join(f"{k}={v!r}" for k, v in self.to_dict().items())
        return f"{class_name}({attrs})"

    def __eq__(self, other):
        """Gleichheits-Vergleich"""
        if not isinstance(other, self.__class__):
            return False
        return self.to_dict() == other.to_dict()


# ==============================================================================
# Initialisierung
# ==============================================================================

def _register_models():
    """Registriert alle Models beim Start"""
    # Models werden bei Bedarf registriert
    pass


_register_models()