#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Model für die Wareneingang-Anwendung
Repräsentiert einen Benutzer mit RFID-Authentifizierung
"""

import re
import hashlib
import secrets
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from . import BaseModel, ValidationError

logger = logging.getLogger(__name__)


# ==============================================================================
# Enums
# ==============================================================================

class UserRole(Enum):
    """Benutzerrollen im System"""
    USER = "user"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"
    SYSTEM = "system"

    @classmethod
    def has_permission(cls, role: "UserRole", permission: str) -> bool:
        """Prüft ob eine Rolle eine bestimmte Berechtigung hat"""
        permissions = {
            cls.USER: ["scan", "view_own", "logout"],
            cls.SUPERVISOR: ["scan", "view_own", "view_team", "reports", "logout", "manage_team"],
            cls.ADMIN: ["*"],  # Alle Berechtigungen
            cls.SYSTEM: ["*"]  # System-Benutzer
        }

        role_perms = permissions.get(role, [])
        return "*" in role_perms or permission in role_perms


class UserStatus(Enum):
    """Benutzerstatus"""
    ACTIVE = 0
    INACTIVE = 1
    SUSPENDED = 2
    DELETED = 3

    @property
    def is_active(self) -> bool:
        """Prüft ob der Status aktiv ist"""
        return self == UserStatus.ACTIVE


# ==============================================================================
# User Model
# ==============================================================================

@dataclass
class User(BaseModel):
    """
    Repräsentiert einen Systembenutzer
    """

    # Primärschlüssel
    id: Optional[int] = None

    # Persönliche Daten
    vorname: str = ""
    nachname: str = ""
    email: str = ""

    # Authentifizierung
    benutzer: str = ""  # Login-Name
    benutzer_name: str = ""  # Anzeigename
    benutzer_passwort: str = "rfid"  # Standard für RFID-Login

    # RFID
    epc: Optional[int] = None  # EPC als Decimal
    rfid_tag: str = ""  # RFID als Hex-String

    # Rolle und Status
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE

    # Zeitstempel
    registriert_am: datetime = field(default_factory=datetime.now)
    letzte_aktivitaet: datetime = field(default_factory=datetime.now)

    # Einstellungen
    sprache: str = "de"
    zeitzone: str = "Europe/Berlin"
    benachrichtigungen: bool = True

    # Arbeitszeit
    arbeitszeit_heute: timedelta = timedelta()
    letzte_anmeldung: Optional[datetime] = None
    letzte_abmeldung: Optional[datetime] = None

    # Statistik
    scan_count_heute: int = 0
    scan_count_gesamt: int = 0
    fehler_count_heute: int = 0

    # Metadaten
    x_status: int = 0
    x_datum: datetime = field(default_factory=datetime.now)
    x_benutzer: str = "System"

    def __post_init__(self):
        """Nach der Initialisierung"""
        # Anzeigename generieren falls leer
        if not self.benutzer_name and (self.vorname or self.nachname):
            self.benutzer_name = f"{self.vorname} {self.nachname}".strip()

        # Benutzername generieren falls leer
        if not self.benutzer and (self.vorname and self.nachname):
            self.benutzer = f"{self.vorname.lower()}_{self.nachname.lower()}"
            self.benutzer = re.sub(r'[^a-z0-9_]', '', self.benutzer)

        # RFID konvertieren
        if self.rfid_tag and not self.epc:
            try:
                self.epc = int(self.rfid_tag, 16)
            except ValueError:
                pass
        elif self.epc and not self.rfid_tag:
            self.rfid_tag = format(self.epc, 'X')

    @classmethod
    def from_database(cls, db_row: Dict[str, Any]) -> "User":
        """
        Erstellt einen User aus Datenbankdaten

        Args:
            db_row: Zeile aus der Datenbank

        Returns:
            User: Neues User-Objekt
        """
        # Status konvertieren
        status = UserStatus.ACTIVE
        if db_row.get("xStatus") == 1:
            status = UserStatus.INACTIVE
        elif db_row.get("xStatus") == 2:
            status = UserStatus.SUSPENDED

        return cls(
            id=db_row.get("ID"),
            vorname=db_row.get("Vorname", ""),
            nachname=db_row.get("Nachname", ""),
            email=db_row.get("Email", ""),
            benutzer=db_row.get("Benutzer", ""),
            benutzer_name=db_row.get("BenutzerName", ""),
            benutzer_passwort=db_row.get("BenutzerPasswort", "rfid"),
            epc=db_row.get("EPC"),
            status=status,
            registriert_am=db_row.get("xDatum", datetime.now()),
            x_status=db_row.get("xStatus", 0),
            x_datum=db_row.get("xDatum", datetime.now()),
            x_benutzer=db_row.get("xBenutzer", "System")
        )

    @property
    def full_name(self) -> str:
        """Gibt den vollständigen Namen zurück"""
        return f"{self.vorname} {self.nachname}".strip() or self.benutzer_name or self.benutzer

    @property
    def is_active(self) -> bool:
        """Prüft ob der Benutzer aktiv ist"""
        return self.status == UserStatus.ACTIVE

    @property
    def is_admin(self) -> bool:
        """Prüft ob der Benutzer Admin ist"""
        return self.role == UserRole.ADMIN

    @property
    def is_supervisor(self) -> bool:
        """Prüft ob der Benutzer Supervisor ist"""
        return self.role in [UserRole.SUPERVISOR, UserRole.ADMIN]

    @property
    def can_manage_users(self) -> bool:
        """Prüft ob der Benutzer andere Benutzer verwalten kann"""
        return UserRole.has_permission(self.role, "manage_users")

    def has_permission(self, permission: str) -> bool:
        """
        Prüft ob der Benutzer eine bestimmte Berechtigung hat

        Args:
            permission: Name der Berechtigung

        Returns:
            bool: True wenn berechtigt
        """
        return UserRole.has_permission(self.role, permission)

    def authenticate_rfid(self, rfid_tag: str) -> bool:
        """
        Authentifiziert den Benutzer mit RFID

        Args:
            rfid_tag: RFID-Tag als Hex-String

        Returns:
            bool: True bei erfolgreicher Authentifizierung
        """
        if not self.is_active:
            logger.warning(f"Login-Versuch für inaktiven Benutzer: {self.benutzer}")
            return False

        # RFID vergleichen
        if self.rfid_tag.upper() == rfid_tag.upper():
            self.letzte_anmeldung = datetime.now()
            self.letzte_aktivitaet = datetime.now()
            logger.info(f"Benutzer {self.benutzer_name} erfolgreich per RFID angemeldet")
            return True

        logger.warning(f"Fehlgeschlagener RFID-Login für {self.benutzer}: Tag stimmt nicht überein")
        return False

    def authenticate_password(self, password: str) -> bool:
        """
        Authentifiziert den Benutzer mit Passwort

        Args:
            password: Eingegebenes Passwort

        Returns:
            bool: True bei erfolgreicher Authentifizierung
        """
        if not self.is_active:
            return False

        # Einfacher Vergleich (in Produktion sollte gehashed werden)
        if self.benutzer_passwort == password:
            self.letzte_anmeldung = datetime.now()
            self.letzte_aktivitaet = datetime.now()
            return True

        return False

    def clock_in(self):
        """Stempelt den Benutzer ein"""
        self.letzte_anmeldung = datetime.now()
        self.letzte_aktivitaet = datetime.now()
        logger.info(f"Benutzer {self.benutzer_name} eingestempelt")

    def clock_out(self):
        """Stempelt den Benutzer aus"""
        if self.letzte_anmeldung:
            arbeitszeit = datetime.now() - self.letzte_anmeldung
            self.arbeitszeit_heute += arbeitszeit

        self.letzte_abmeldung = datetime.now()
        logger.info(f"Benutzer {self.benutzer_name} ausgestempelt")

    def update_activity(self):
        """Aktualisiert die letzte Aktivität"""
        self.letzte_aktivitaet = datetime.now()

    def increment_scan_count(self, is_error: bool = False):
        """Erhöht den Scan-Zähler"""
        self.scan_count_heute += 1
        self.scan_count_gesamt += 1

        if is_error:
            self.fehler_count_heute += 1

        self.update_activity()

    def reset_daily_stats(self):
        """Setzt die täglichen Statistiken zurück"""
        self.scan_count_heute = 0
        self.fehler_count_heute = 0
        self.arbeitszeit_heute = timedelta()
        logger.info(f"Tägliche Statistiken für {self.benutzer_name} zurückgesetzt")

    @staticmethod
    def validate_rfid_tag(rfid_tag: str) -> bool:
        """
        Validiert einen RFID-Tag

        Args:
            rfid_tag: RFID-Tag als Hex-String

        Returns:
            bool: True wenn gültig
        """
        if not rfid_tag:
            return False

        # Nur Hex-Zeichen erlaubt
        if not re.match(r'^[0-9A-Fa-f]+$', rfid_tag):
            return False

        # Länge prüfen (typisch 8-12 Zeichen)
        if len(rfid_tag) < 8 or len(rfid_tag) > 12:
            return False

        return True

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validiert eine E-Mail-Adresse

        Args:
            email: E-Mail-Adresse

        Returns:
            bool: True wenn gültig
        """
        if not email:
            return True  # Optional

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def validate(self) -> Tuple[bool, List[str]]:
        """Validiert die Benutzerdaten"""
        errors = []

        # Name
        if not self.vorname and not self.nachname:
            errors.append("Vor- oder Nachname erforderlich")

        if self.vorname and len(self.vorname) > 50:
            errors.append("Vorname zu lang (max. 50 Zeichen)")

        if self.nachname and len(self.nachname) > 50:
            errors.append("Nachname zu lang (max. 50 Zeichen)")

        # Benutzername
        if not self.benutzer:
            errors.append("Benutzername fehlt")
        elif not re.match(r'^[a-z0-9_]+$', self.benutzer):
            errors.append("Benutzername darf nur Kleinbuchstaben, Zahlen und _ enthalten")
        elif len(self.benutzer) < 3:
            errors.append("Benutzername zu kurz (min. 3 Zeichen)")
        elif len(self.benutzer) > 30:
            errors.append("Benutzername zu lang (max. 30 Zeichen)")

        # E-Mail
        if self.email and not self.validate_email(self.email):
            errors.append("Ungültige E-Mail-Adresse")

        # RFID
        if self.rfid_tag and not self.validate_rfid_tag(self.rfid_tag):
            errors.append("Ungültiger RFID-Tag")

        # Sprache
        valid_languages = ["de", "en", "tr", "pl"]
        if self.sprache not in valid_languages:
            errors.append(f"Ungültige Sprache (erlaubt: {', '.join(valid_languages)})")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        data = super().to_dict()

        # Enums zu Strings
        if "role" in data and isinstance(data["role"], UserRole):
            data["role"] = data["role"].value

        if "status" in data and isinstance(data["status"], UserStatus):
            data["status"] = data["status"].value

        # Passwort nicht einschließen
        if "benutzer_passwort" in data:
            del data["benutzer_passwort"]

        # Timedelta zu Sekunden
        if "arbeitszeit_heute" in data and isinstance(data["arbeitszeit_heute"], timedelta):
            data["arbeitszeit_heute_seconds"] = int(data["arbeitszeit_heute"].total_seconds())
            del data["arbeitszeit_heute"]

        return data

    def to_session_data(self) -> Dict[str, Any]:
        """Gibt Daten für Session/Frontend zurück"""
        return {
            "id": self.id,
            "benutzer_name": self.benutzer_name,
            "full_name": self.full_name,
            "vorname": self.vorname,
            "nachname": self.nachname,
            "email": self.email,
            "role": self.role.value,
            "sprache": self.sprache,
            "is_admin": self.is_admin,
            "is_supervisor": self.is_supervisor,
            "permissions": self._get_permissions()
        }

    def _get_permissions(self) -> List[str]:
        """Gibt die Berechtigungen des Benutzers zurück"""
        permission_map = {
            UserRole.USER: ["scan", "view_own", "logout"],
            UserRole.SUPERVISOR: ["scan", "view_own", "view_team", "reports", "logout", "manage_team"],
            UserRole.ADMIN: ["*"],
            UserRole.SYSTEM: ["*"]
        }

        return permission_map.get(self.role, [])

    def __str__(self):
        """String-Repräsentation"""
        return f"User({self.benutzer_name}, Role: {self.role.value}, Status: {self.status.value})"


# ==============================================================================
# UserSession Model
# ==============================================================================

@dataclass
class UserSession:
    """
    Repräsentiert eine aktive Benutzersitzung
    """

    # Session-Daten
    session_id: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    user: User = None

    # Zeitstempel
    login_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    # Session-Status
    is_active: bool = True
    ip_address: str = ""
    user_agent: str = ""

    # Temporäre Daten
    temp_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> timedelta:
        """Gibt die Session-Dauer zurück"""
        return datetime.now() - self.login_time

    @property
    def idle_time(self) -> timedelta:
        """Gibt die Idle-Zeit zurück"""
        return datetime.now() - self.last_activity

    def is_expired(self, max_idle_minutes: int = 30) -> bool:
        """
        Prüft ob die Session abgelaufen ist

        Args:
            max_idle_minutes: Maximale Idle-Zeit in Minuten

        Returns:
            bool: True wenn abgelaufen
        """
        return self.idle_time.total_seconds() > max_idle_minutes * 60

    def update_activity(self):
        """Aktualisiert die letzte Aktivität"""
        self.last_activity = datetime.now()
        if self.user:
            self.user.update_activity()

    def end_session(self):
        """Beendet die Session"""
        self.is_active = False
        if self.user:
            self.user.clock_out()

        logger.info(f"Session {self.session_id} beendet nach {self.duration}")