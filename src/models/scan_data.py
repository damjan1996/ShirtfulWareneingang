#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan Data Models für die Wareneingang-Anwendung
Repräsentiert Scan-Sessions und Scan-Positionen
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum, IntEnum
from dataclasses import dataclass, field

from . import BaseModel, ValidationError

logger = logging.getLogger(__name__)


# ==============================================================================
# Enums
# ==============================================================================

class ScanType(IntEnum):
    """Scan-Typ Definitionen (muss mit Datenbank übereinstimmen)"""
    WARENEINGANG = 1
    RAHMENSPANNEN = 2
    STICKEN = 3
    VERSAEUBERN = 4
    QUALITAETSKONTROLLE = 5
    WARENAUSGANG = 6

    @classmethod
    def get_name(cls, value: int) -> str:
        """Gibt den Namen für einen Wert zurück"""
        try:
            return cls(value).name
        except ValueError:
            return f"UNBEKANNT_{value}"

    @classmethod
    def get_display_name(cls, value: int) -> str:
        """Gibt den Anzeigenamen zurück"""
        display_names = {
            cls.WARENEINGANG: "Wareneingang",
            cls.RAHMENSPANNEN: "Rahmenspannen",
            cls.STICKEN: "Sticken",
            cls.VERSAEUBERN: "Versäubern",
            cls.QUALITAETSKONTROLLE: "Qualitätskontrolle",
            cls.WARENAUSGANG: "Warenausgang"
        }
        return display_names.get(value, f"Unbekannt ({value})")


class SessionStatus(IntEnum):
    """Status einer Scan-Session"""
    ACTIVE = 0
    CLOSED = 1
    PAUSED = 2
    CANCELLED = 3


# ==============================================================================
# ScanData Base Model
# ==============================================================================

@dataclass
class ScanData(BaseModel):
    """
    Basis-Klasse für Scan-Daten
    Enthält gemeinsame Felder für Sessions und Positionen
    """

    # Zeitstempel
    datum: datetime = field(default_factory=datetime.now)
    tages_datum: datetime = field(default_factory=lambda: datetime.now().date())

    # Metadaten
    x_status: int = 0
    x_datum: datetime = field(default_factory=datetime.now)
    x_benutzer: str = "System"

    def get_datum_int(self) -> int:
        """Konvertiert Datum zu Integer-Format (YYYYMMDDHHMMSS)"""
        return int(self.datum.strftime("%Y%m%d%H%M%S"))

    def get_tages_datum_int(self) -> int:
        """Konvertiert Tagesdatum zu Integer-Format (YYYYMMDD)"""
        return int(self.tages_datum.strftime("%Y%m%d"))


# ==============================================================================
# ScanSession Model
# ==============================================================================

@dataclass
class ScanSession(ScanData):
    """
    Repräsentiert eine Scan-Session (ScannKopf)
    Eine Session gruppiert mehrere Scan-Positionen
    """

    # Primärschlüssel
    id: Optional[int] = None

    # Benutzer-Referenz
    user_id: int = 0
    epc: int = 0  # RFID als Decimal

    # Session-Daten
    scan_type_id: int = ScanType.WARENEINGANG
    arbeitsplatz: str = "Station-01"
    status: SessionStatus = SessionStatus.ACTIVE

    # Statistik
    position_count: int = 0
    error_count: int = 0
    duration_minutes: int = 0

    # Verknüpfte Positionen
    positions: List["ScanPosition"] = field(default_factory=list)

    def __post_init__(self):
        """Nach der Initialisierung"""
        # Arbeitsplatz normalisieren
        if not self.arbeitsplatz:
            self.arbeitsplatz = f"Station-{self.scan_type_id:02d}"

    @property
    def scan_type_name(self) -> str:
        """Gibt den Namen des Scan-Typs zurück"""
        return ScanType.get_display_name(self.scan_type_id)

    @property
    def is_active(self) -> bool:
        """Prüft ob die Session aktiv ist"""
        return self.status == SessionStatus.ACTIVE

    @property
    def is_closed(self) -> bool:
        """Prüft ob die Session geschlossen ist"""
        return self.status == SessionStatus.CLOSED

    def add_position(self, position: "ScanPosition"):
        """Fügt eine Position zur Session hinzu"""
        if not isinstance(position, ScanPosition):
            raise ValueError("Position muss vom Typ ScanPosition sein")

        position.session_id = self.id
        self.positions.append(position)
        self.position_count = len(self.positions)

        # Fehler zählen
        if position.is_error:
            self.error_count += 1

    def close(self, user: str = "System"):
        """Schließt die Session"""
        self.status = SessionStatus.CLOSED
        self.x_datum = datetime.now()
        self.x_benutzer = user

        # Dauer berechnen
        if self.datum:
            duration = datetime.now() - self.datum
            self.duration_minutes = int(duration.total_seconds() / 60)

        logger.info(
            f"Session {self.id} geschlossen: "
            f"{self.position_count} Scans in {self.duration_minutes} Minuten"
        )

    def pause(self, user: str = "System"):
        """Pausiert die Session"""
        self.status = SessionStatus.PAUSED
        self.x_datum = datetime.now()
        self.x_benutzer = user

        logger.info(f"Session {self.id} pausiert")

    def resume(self, user: str = "System"):
        """Setzt eine pausierte Session fort"""
        if self.status != SessionStatus.PAUSED:
            raise ValueError("Session ist nicht pausiert")

        self.status = SessionStatus.ACTIVE
        self.x_datum = datetime.now()
        self.x_benutzer = user

        logger.info(f"Session {self.id} fortgesetzt")

    def validate(self) -> Tuple[bool, List[str]]:
        """Validiert die Session-Daten"""
        errors = []

        # Benutzer-Referenz
        if self.user_id <= 0:
            errors.append("Ungültige Benutzer-ID")

        if self.epc <= 0:
            errors.append("Ungültiger EPC-Wert")

        # Scan-Typ
        try:
            ScanType(self.scan_type_id)
        except ValueError:
            errors.append(f"Ungültiger Scan-Typ: {self.scan_type_id}")

        # Arbeitsplatz
        if not self.arbeitsplatz:
            errors.append("Arbeitsplatz fehlt")
        elif len(self.arbeitsplatz) > 50:
            errors.append("Arbeitsplatz zu lang (max. 50 Zeichen)")

        return len(errors) == 0, errors

    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken zur Session zurück"""
        success_count = self.position_count - self.error_count
        success_rate = (success_count / self.position_count * 100) if self.position_count > 0 else 0

        avg_scan_time = 0
        if self.duration_minutes > 0 and self.position_count > 0:
            avg_scan_time = self.duration_minutes * 60 / self.position_count  # Sekunden pro Scan

        return {
            "session_id": self.id,
            "scan_type": self.scan_type_name,
            "status": self.status.name,
            "total_scans": self.position_count,
            "successful_scans": success_count,
            "error_scans": self.error_count,
            "success_rate": round(success_rate, 1),
            "duration_minutes": self.duration_minutes,
            "avg_scan_time_seconds": round(avg_scan_time, 1),
            "scans_per_hour": int(
                self.position_count / (self.duration_minutes / 60)) if self.duration_minutes > 0 else 0
        }

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        data = super().to_dict()

        # Enums zu Strings
        if "status" in data and isinstance(data["status"], SessionStatus):
            data["status"] = data["status"].value

        # Positionen nicht standardmäßig einschließen (zu groß)
        if "positions" in data:
            data["position_count"] = len(data["positions"])
            del data["positions"]

        return data


# ==============================================================================
# ScanPosition Model
# ==============================================================================

@dataclass
class ScanPosition(ScanData):
    """
    Repräsentiert eine Scan-Position (ScannPosition)
    Ein einzelner Scan innerhalb einer Session
    """

    # Primärschlüssel
    id: Optional[int] = None

    # Session-Referenz
    session_id: int = 0

    # Scan-Daten
    kunde: str = ""
    auftragsnummer: str = ""
    paketnummer: str = ""
    zusatzinfo: str = ""

    # Status
    is_error: bool = False
    error_message: str = ""
    is_duplicate: bool = False

    # QR-Code Rohdaten
    raw_data: str = ""

    def __post_init__(self):
        """Nach der Initialisierung"""
        # Felder trimmen
        self.kunde = self.kunde.strip() if self.kunde else ""
        self.auftragsnummer = self.auftragsnummer.strip() if self.auftragsnummer else ""
        self.paketnummer = self.paketnummer.strip() if self.paketnummer else ""

        # Zusatzinfo begrenzen
        if self.zusatzinfo and len(self.zusatzinfo) > 255:
            self.zusatzinfo = self.zusatzinfo[:255]

    @classmethod
    def from_qr_data(cls, session_id: int, qr_data: Dict[str, Any]) -> "ScanPosition":
        """
        Erstellt eine Position aus QR-Code-Daten

        Args:
            session_id: ID der zugehörigen Session
            qr_data: Geparste QR-Code-Daten

        Returns:
            ScanPosition: Neue Position
        """
        return cls(
            session_id=session_id,
            kunde=qr_data.get("kunden_name", ""),
            auftragsnummer=qr_data.get("auftrags_nr", ""),
            paketnummer=qr_data.get("paket_nr", ""),
            zusatzinfo=qr_data.get("zusatzinfo", ""),
            raw_data=qr_data.get("raw_data", "")
        )

    @property
    def has_complete_data(self) -> bool:
        """Prüft ob alle wichtigen Daten vorhanden sind"""
        return bool(self.paketnummer and (self.auftragsnummer or self.kunde))

    def mark_as_error(self, message: str):
        """Markiert die Position als Fehler"""
        self.is_error = True
        self.error_message = message
        self.x_status = 2  # Fehler-Status

    def mark_as_duplicate(self):
        """Markiert die Position als Duplikat"""
        self.is_duplicate = True
        self.zusatzinfo = "DUPLIKAT: " + self.zusatzinfo

    def validate(self) -> Tuple[bool, List[str]]:
        """Validiert die Positions-Daten"""
        errors = []

        # Session-Referenz
        if self.session_id <= 0:
            errors.append("Ungültige Session-ID")

        # Mindestens Paketnummer erforderlich
        if not self.paketnummer:
            errors.append("Paketnummer fehlt")
        elif len(self.paketnummer) > 50:
            errors.append("Paketnummer zu lang (max. 50 Zeichen)")

        # Weitere Felder validieren
        if self.auftragsnummer and len(self.auftragsnummer) > 50:
            errors.append("Auftragsnummer zu lang (max. 50 Zeichen)")

        if self.kunde and len(self.kunde) > 100:
            errors.append("Kundenname zu lang (max. 100 Zeichen)")

        if self.zusatzinfo and len(self.zusatzinfo) > 255:
            errors.append("Zusatzinfo zu lang (max. 255 Zeichen)")

        return len(errors) == 0, errors

    def get_display_text(self) -> str:
        """Gibt einen Anzeigetext zurück"""
        parts = []

        if self.paketnummer:
            parts.append(f"Paket: {self.paketnummer}")

        if self.auftragsnummer:
            parts.append(f"Auftrag: {self.auftragsnummer}")

        if self.kunde:
            parts.append(f"Kunde: {self.kunde}")

        if self.is_error:
            parts.append(f"❌ FEHLER: {self.error_message}")
        elif self.is_duplicate:
            parts.append("⚠️ DUPLIKAT")

        return " | ".join(parts) if parts else "Leere Position"

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        data = super().to_dict()

        # Raw-Daten nicht standardmäßig einschließen (zu groß)
        if "raw_data" in data and len(data["raw_data"]) > 100:
            data["raw_data_truncated"] = data["raw_data"][:100] + "..."
            del data["raw_data"]

        return data

    def __str__(self):
        """String-Repräsentation"""
        return self.get_display_text()


# ==============================================================================
# ScanStatistics Model
# ==============================================================================

@dataclass
class ScanStatistics:
    """
    Statistik-Model für Scan-Daten
    Aggregierte Daten für Berichte und Dashboards
    """

    # Zeitraum
    start_date: datetime
    end_date: datetime

    # Gesamt-Statistiken
    total_sessions: int = 0
    total_scans: int = 0
    total_errors: int = 0
    total_users: int = 0

    # Durchschnittswerte
    avg_scans_per_session: float = 0.0
    avg_session_duration: float = 0.0
    avg_scans_per_hour: float = 0.0

    # Nach Typ
    scans_by_type: Dict[int, int] = field(default_factory=dict)
    errors_by_type: Dict[int, int] = field(default_factory=dict)

    # Nach Benutzer
    scans_by_user: Dict[int, int] = field(default_factory=dict)

    # Nach Stunde
    scans_by_hour: Dict[int, int] = field(default_factory=dict)

    # Top-Listen
    top_users: List[Tuple[str, int]] = field(default_factory=list)
    top_customers: List[Tuple[str, int]] = field(default_factory=list)

    def calculate_averages(self):
        """Berechnet Durchschnittswerte"""
        if self.total_sessions > 0:
            self.avg_scans_per_session = self.total_scans / self.total_sessions

        # Arbeitsstunden berechnen (Zeitraum in Stunden)
        if self.start_date and self.end_date:
            duration = self.end_date - self.start_date
            work_hours = duration.total_seconds() / 3600

            if work_hours > 0:
                self.avg_scans_per_hour = self.total_scans / work_hours

    def get_success_rate(self) -> float:
        """Berechnet die Erfolgsrate"""
        if self.total_scans > 0:
            return ((self.total_scans - self.total_errors) / self.total_scans) * 100
        return 0.0

    def get_peak_hour(self) -> Tuple[int, int]:
        """Gibt die Stunde mit den meisten Scans zurück"""
        if not self.scans_by_hour:
            return 0, 0

        peak_hour = max(self.scans_by_hour.items(), key=lambda x: x[1])
        return peak_hour

    def get_most_active_scan_type(self) -> Tuple[str, int]:
        """Gibt den aktivsten Scan-Typ zurück"""
        if not self.scans_by_type:
            return "Keine Daten", 0

        type_id, count = max(self.scans_by_type.items(), key=lambda x: x[1])
        type_name = ScanType.get_display_name(type_id)
        return type_name, count

    def to_report_dict(self) -> Dict[str, Any]:
        """Konvertiert zu einem Report-Dictionary"""
        return {
            "period": {
                "start": self.start_date.isoformat() if self.start_date else None,
                "end": self.end_date.isoformat() if self.end_date else None
            },
            "summary": {
                "total_sessions": self.total_sessions,
                "total_scans": self.total_scans,
                "total_errors": self.total_errors,
                "total_users": self.total_users,
                "success_rate": round(self.get_success_rate(), 1)
            },
            "averages": {
                "scans_per_session": round(self.avg_scans_per_session, 1),
                "session_duration_minutes": round(self.avg_session_duration, 1),
                "scans_per_hour": round(self.avg_scans_per_hour, 1)
            },
            "by_type": {
                ScanType.get_display_name(k): v
                for k, v in self.scans_by_type.items()
            },
            "by_hour": self.scans_by_hour,
            "top_users": self.top_users[:10],
            "top_customers": self.top_customers[:10],
            "peak_hour": {
                "hour": self.get_peak_hour()[0],
                "count": self.get_peak_hour()[1]
            },
            "most_active_type": {
                "name": self.get_most_active_scan_type()[0],
                "count": self.get_most_active_scan_type()[1]
            }
        }