#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Benutzer-Panel für eingeloggte Benutzer
Zeigt Scanner-Interface und benutzerspezifische Funktionen
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta

from config.constants import StatusCodes, ScanTypes
from config.settings import USER_SETTINGS, AUDIO_SETTINGS
from src.database.scan_repository import ScanRepository
from src.database.user_repository import UserRepository
from src.utils.audio_player import AudioPlayer
from .scanner_screen import ScannerScreen
from .styles import Styles, StylePresets
from .widgets import BigButton, ScanResultList, StatusBar
from . import show_info, show_error, confirm_dialog, event_manager, Events

logger = logging.getLogger(__name__)


class UserPanel(tk.Frame):
    """
    Panel für einen eingeloggten Benutzer
    Enthält Scanner, Scan-Historie und Benutzer-Funktionen
    """

    def __init__(self, parent, user: Dict[str, Any],
                 scan_type_id: int = ScanTypes.WARENEINGANG.value,
                 on_logout: Callable = None, **kwargs):
        """
        Initialisiert das Benutzer-Panel

        Args:
            parent: Eltern-Widget
            user: Benutzerdaten
            scan_type_id: Typ des Scan-Vorgangs
            on_logout: Callback für Logout
            **kwargs: Weitere Tkinter-Argumente
        """
        super().__init__(parent, **kwargs)

        # Benutzer-Daten
        self.user = user
        self.scan_type_id = scan_type_id
        self.on_logout = on_logout

        # Services
        self.scan_repository = ScanRepository()
        self.user_repository = UserRepository()
        self.audio_player = AudioPlayer()

        # Session-Daten
        self.session_id: Optional[int] = None
        self.scan_count = 0
        self.success_count = 0
        self.error_count = 0
        self.session_start_time = datetime.now()
        self.last_activity_time = datetime.now()

        # Timer
        self.activity_timer = None
        self.time_update_timer = None

        # UI erstellen
        self._create_ui()

        # Style anwenden
        self.configure(bg=Styles.COLORS["background"])

        # Session starten
        self._start_session()

        # Timer starten
        self._start_timers()

    def _create_ui(self):
        """Erstellt die Benutzeroberfläche"""

        # Header mit Benutzer-Info
        self._create_header()

        # Hauptbereich (Scanner + Seitenleiste)
        main_frame = tk.Frame(self, bg=Styles.COLORS["background"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Linker Bereich: Scanner
        scanner_container = tk.Frame(main_frame, bg=Styles.COLORS["background"])
        scanner_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 10))

        self.scanner_screen = ScannerScreen(
            scanner_container,
            on_scan_complete=self._on_scan_complete
        )
        self.scanner_screen.pack(fill=tk.BOTH, expand=True)

        # Rechter Bereich: Sidebar
        self._create_sidebar(main_frame)

        # Statusleiste
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _create_header(self):
        """Erstellt den Header-Bereich"""
        header_frame = tk.Frame(
            self,
            bg=Styles.COLORS["surface"],
            height=80
        )
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Benutzer-Info links
        user_info_frame = tk.Frame(header_frame, bg=Styles.COLORS["surface"])
        user_info_frame.pack(side=tk.LEFT, padx=20, pady=15)

        # Benutzer-Icon
        user_icon = tk.Label(
            user_info_frame,
            text="👤",
            font=("Arial", 32),
            bg=Styles.COLORS["surface"]
        )
        user_icon.pack(side=tk.LEFT, padx=(0, 15))

        # Benutzer-Details
        details_frame = tk.Frame(user_info_frame, bg=Styles.COLORS["surface"])
        details_frame.pack(side=tk.LEFT)

        name_label = tk.Label(
            details_frame,
            text=self.user["benutzer_name"],
            font=Styles.get_font("bold", "large"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["surface"]
        )
        name_label.pack(anchor=tk.W)

        self.login_time_label = tk.Label(
            details_frame,
            text=f"Angemeldet seit: {self.session_start_time.strftime('%H:%M')}",
            font=Styles.get_font("normal", "small"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["surface"]
        )
        self.login_time_label.pack(anchor=tk.W)

        # Arbeitszeit
        self.work_time_label = tk.Label(
            details_frame,
            text="Arbeitszeit: 0:00",
            font=Styles.get_font("normal", "small"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["surface"]
        )
        self.work_time_label.pack(anchor=tk.W)

        # Logout-Button rechts
        logout_button = BigButton(
            header_frame,
            text="🚪 Abmelden",
            command=self._handle_logout,
            bg_color=Styles.COLORS["error"],
            hover_color="#D32F2F",
            height=50,
            width=150,
            font_size=16
        )
        logout_button.pack(side=tk.RIGHT, padx=20)

        # Pause-Button
        self.pause_button = BigButton(
            header_frame,
            text="☕ Pause",
            command=self._toggle_pause,
            bg_color=Styles.COLORS["warning"],
            hover_color="#F57C00",
            height=50,
            width=120,
            font_size=16
        )
        self.pause_button.pack(side=tk.RIGHT, padx=10)

    def _create_sidebar(self, parent):
        """Erstellt die Seitenleiste"""
        sidebar = tk.Frame(
            parent,
            bg=Styles.COLORS["surface"],
            width=350
        )
        sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 20), pady=(0, 20))
        sidebar.pack_propagate(False)

        # Statistik
        self._create_statistics_section(sidebar)

        # Letzte Scans
        self._create_recent_scans_section(sidebar)

        # Aktionen
        self._create_actions_section(sidebar)

    def _create_statistics_section(self, parent):
        """Erstellt den Statistik-Bereich"""
        stats_frame = tk.LabelFrame(
            parent,
            text="📊 Heutige Statistik",
            font=Styles.get_font("bold", "medium"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["surface"],
            relief=tk.GROOVE,
            borderwidth=2
        )
        stats_frame.pack(fill=tk.X, padx=10, pady=10)

        # Statistik-Grid
        stats_grid = tk.Frame(stats_frame, bg=Styles.COLORS["surface"])
        stats_grid.pack(padx=15, pady=15)

        # Gesamt-Scans
        self._create_stat_item(
            stats_grid,
            "Scans gesamt:",
            self.scan_count,
            Styles.COLORS["text_primary"],
            0, 0
        )

        # Erfolgreiche Scans
        self._create_stat_item(
            stats_grid,
            "Erfolgreich:",
            self.success_count,
            Styles.COLORS["success"],
            1, 0
        )

        # Fehler
        self._create_stat_item(
            stats_grid,
            "Fehler:",
            self.error_count,
            Styles.COLORS["error"],
            2, 0
        )

        # Durchschnitt pro Stunde
        self.avg_per_hour_label = self._create_stat_item(
            stats_grid,
            "⌀ pro Stunde:",
            "0",
            Styles.COLORS["info"],
            3, 0
        )

    def _create_stat_item(self, parent, label_text: str, value,
                          color: str, row: int, col: int) -> tk.Label:
        """Erstellt ein Statistik-Element"""
        label = tk.Label(
            parent,
            text=label_text,
            font=Styles.get_font("normal", "medium"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["surface"]
        )
        label.grid(row=row, column=col, sticky="w", pady=5)

        value_label = tk.Label(
            parent,
            text=str(value),
            font=Styles.get_font("bold", "large"),
            fg=color,
            bg=Styles.COLORS["surface"]
        )
        value_label.grid(row=row, column=col + 1, sticky="e", padx=(20, 0), pady=5)

        # Label für Updates speichern
        if label_text == "Scans gesamt:":
            self.total_scans_label = value_label
        elif label_text == "Erfolgreich:":
            self.success_scans_label = value_label
        elif label_text == "Fehler:":
            self.error_scans_label = value_label

        return value_label

    def _create_recent_scans_section(self, parent):
        """Erstellt den Bereich für letzte Scans"""
        recent_frame = tk.LabelFrame(
            parent,
            text="📋 Letzte Scans",
            font=Styles.get_font("bold", "medium"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["surface"],
            relief=tk.GROOVE,
            borderwidth=2
        )
        recent_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scan-Liste
        self.scan_list = ScanResultList(
            recent_frame,
            height=8,
            on_select=self._on_scan_selected
        )
        self.scan_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _create_actions_section(self, parent):
        """Erstellt den Aktions-Bereich"""
        actions_frame = tk.LabelFrame(
            parent,
            text="⚡ Aktionen",
            font=Styles.get_font("bold", "medium"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["surface"],
            relief=tk.GROOVE,
            borderwidth=2
        )
        actions_frame.pack(fill=tk.X, padx=10, pady=10)

        button_frame = tk.Frame(actions_frame, bg=Styles.COLORS["surface"])
        button_frame.pack(padx=10, pady=10)

        # Manueller Scan
        manual_scan_btn = tk.Button(
            button_frame,
            text="📝 Manuell erfassen",
            font=Styles.get_font("normal", "medium"),
            bg=Styles.COLORS["secondary"],
            fg="white",
            activebackground=Styles.COLORS["secondary_dark"],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8,
            command=self._show_manual_entry
        )
        manual_scan_btn.pack(fill=tk.X, pady=5)

        # Letzten Scan löschen
        delete_last_btn = tk.Button(
            button_frame,
            text="↩ Letzten Scan löschen",
            font=Styles.get_font("normal", "medium"),
            bg=Styles.COLORS["surface"],
            fg=Styles.COLORS["error"],
            activebackground=Styles.COLORS["hover"],
            activeforeground=Styles.COLORS["error"],
            relief=tk.RAISED,
            cursor="hand2",
            padx=15,
            pady=8,
            borderwidth=1,
            command=self._delete_last_scan
        )
        delete_last_btn.pack(fill=tk.X, pady=5)

        # Report
        report_btn = tk.Button(
            button_frame,
            text="📊 Tagesbericht",
            font=Styles.get_font("normal", "medium"),
            bg=Styles.COLORS["surface"],
            fg=Styles.COLORS["primary"],
            activebackground=Styles.COLORS["hover"],
            activeforeground=Styles.COLORS["primary_dark"],
            relief=tk.RAISED,
            cursor="hand2",
            padx=15,
            pady=8,
            borderwidth=1,
            command=self._show_daily_report
        )
        report_btn.pack(fill=tk.X, pady=5)

    def _start_session(self):
        """Startet eine neue Scan-Session"""
        try:
            # Session in Datenbank erstellen
            self.session_id = self.scan_repository.create_scan_session(
                epc=self.user["epc"],
                scan_type_id=self.scan_type_id,
                arbeitsplatz="Wareneingang-01",
                benutzer=self.user["benutzer_name"]
            )

            if self.session_id:
                logger.info(f"Session {self.session_id} gestartet für {self.user['benutzer_name']}")
                self.status_bar.set_status("Session gestartet", "success")

                # Zeiterfassung starten
                self.user_repository.clock_in(self.user["id"], self.user["epc"])
            else:
                logger.error("Konnte Session nicht starten")
                self.status_bar.set_status("Fehler beim Session-Start", "error")

        except Exception as e:
            logger.error(f"Fehler beim Session-Start: {e}")
            self.status_bar.set_status("Datenbankfehler", "error")

    def _on_scan_complete(self, qr_data: Dict[str, Any]):
        """
        Wird aufgerufen wenn ein QR-Code gescannt wurde

        Args:
            qr_data: Gescannte Daten
        """
        self.last_activity_time = datetime.now()

        # Duplikat prüfen
        duplicate = self.scan_repository.check_duplicate_scan(
            qr_data.get("paket_nr", ""),
            self.scan_type_id
        )

        if duplicate:
            # Warnung anzeigen
            show_warning(
                self,
                f"Paket bereits gescannt!\n\n"
                f"Gescannt von: {duplicate['benutzer']}\n"
                f"Zeit: {duplicate['datum'].strftime('%H:%M:%S')}"
            )

            self.error_count += 1
            self._update_statistics()

            # Audio-Feedback
            if AUDIO_SETTINGS["enabled"]:
                self.audio_player.play_sound("scan_error")

            return

        # In Datenbank speichern
        try:
            position_id = self.scan_repository.add_scan_position(
                session_id=self.session_id,
                kunde=qr_data.get("kunden_name"),
                auftragsnummer=qr_data.get("auftrags_nr"),
                paketnummer=qr_data.get("paket_nr"),
                zusatzinfo=qr_data.get("raw_data", "")[:255],
                benutzer=self.user["benutzer_name"]
            )

            if position_id:
                # Erfolg
                self.scan_count += 1
                self.success_count += 1

                # Zur Liste hinzufügen
                self.scan_list.add_scan({
                    "id": position_id,
                    "timestamp": datetime.now(),
                    "auftragsnummer": qr_data.get("auftrags_nr", ""),
                    "paketnummer": qr_data.get("paket_nr", ""),
                    "kunde": qr_data.get("kunden_name", ""),
                    "status": "success"
                })

                # Status
                self.status_bar.set_status(
                    f"Scan erfolgreich: {qr_data.get('paket_nr', 'N/A')}",
                    "success"
                )

                # Audio-Feedback
                if AUDIO_SETTINGS["enabled"]:
                    self.audio_player.play_sound("scan_success")
            else:
                # Fehler
                self.error_count += 1
                self.status_bar.set_status("Fehler beim Speichern", "error")

                # Audio-Feedback
                if AUDIO_SETTINGS["enabled"]:
                    self.audio_player.play_sound("scan_error")

        except Exception as e:
            logger.error(f"Fehler beim Speichern des Scans: {e}")
            self.error_count += 1
            self.status_bar.set_status("Datenbankfehler", "error")

            # Audio-Feedback
            if AUDIO_SETTINGS["enabled"]:
                self.audio_player.play_sound("scan_error")

        # Statistik aktualisieren
        self._update_statistics()

        # Scanner-Statistik aktualisieren
        self.scanner_screen.update_statistics(
            self.scan_count,
            self.success_count,
            self.error_count
        )

    def _update_statistics(self):
        """Aktualisiert die Statistik-Anzeige"""
        # Labels aktualisieren
        self.total_scans_label.configure(text=str(self.scan_count))
        self.success_scans_label.configure(text=str(self.success_count))
        self.error_scans_label.configure(text=str(self.error_count))

        # Durchschnitt berechnen
        work_time = datetime.now() - self.session_start_time
        hours = work_time.total_seconds() / 3600

        if hours > 0:
            avg_per_hour = int(self.scan_count / hours)
            self.avg_per_hour_label.configure(text=str(avg_per_hour))

    def _update_work_time(self):
        """Aktualisiert die Arbeitszeit-Anzeige"""
        work_time = datetime.now() - self.session_start_time
        hours = int(work_time.total_seconds() // 3600)
        minutes = int((work_time.total_seconds() % 3600) // 60)

        self.work_time_label.configure(
            text=f"Arbeitszeit: {hours}:{minutes:02d}"
        )

        # Pausenerinnerung
        if hours >= 6 and not hasattr(self, '_break_reminder_shown'):
            self._break_reminder_shown = True
            show_info(
                self,
                "Sie arbeiten bereits seit 6 Stunden.\n"
                "Bitte denken Sie an Ihre Pausenzeit!",
                "Pausenerinnerung"
            )

    def _check_idle_timeout(self):
        """Prüft auf Inaktivität"""
        idle_time = datetime.now() - self.last_activity_time
        idle_minutes = idle_time.total_seconds() / 60

        # Warnung vor Timeout
        warning_minutes = USER_SETTINGS["session"]["warning_before_timeout"]
        timeout_minutes = USER_SETTINGS["session"]["idle_timeout_minutes"]

        if idle_minutes > timeout_minutes - warning_minutes and not hasattr(self, '_timeout_warning_shown'):
            self._timeout_warning_shown = True
            show_warning(
                self,
                f"Sie sind seit {int(idle_minutes)} Minuten inaktiv.\n"
                f"Die Session wird in {warning_minutes} Minuten beendet.",
                "Inaktivitäts-Warnung"
            )

        # Auto-Logout
        if idle_minutes > timeout_minutes and USER_SETTINGS["session"]["auto_logout_enabled"]:
            logger.info(f"Auto-Logout nach {idle_minutes} Minuten Inaktivität")
            event_manager.emit(Events.SESSION_TIMEOUT, self.user)
            self._handle_logout()

    def _start_timers(self):
        """Startet die Timer"""
        # Arbeitszeit-Update (jede Minute)
        self._update_work_time()
        self.time_update_timer = self.after(60000, self._start_timers)

        # Idle-Check (alle 30 Sekunden)
        self._check_idle_timeout()
        self.activity_timer = self.after(30000, self._check_idle_timeout)

    def _stop_timers(self):
        """Stoppt alle Timer"""
        if self.time_update_timer:
            self.after_cancel(self.time_update_timer)

        if self.activity_timer:
            self.after_cancel(self.activity_timer)

    def _toggle_pause(self):
        """Pause ein/ausschalten"""
        # TODO: Pause-Funktionalität implementieren
        show_info(self, "Pause-Funktion noch nicht implementiert", "Info")

    def _show_manual_entry(self):
        """Zeigt Dialog für manuelle Eingabe"""
        # TODO: Manueller Eingabe-Dialog
        show_info(self, "Manuelle Eingabe noch nicht implementiert", "Info")

    def _delete_last_scan(self):
        """Löscht den letzten Scan"""
        last_scan = self.scan_list.get_last_scan()

        if not last_scan:
            show_info(self, "Keine Scans zum Löschen vorhanden", "Info")
            return

        # Bestätigung
        if not confirm_dialog(
                self,
                f"Möchten Sie den letzten Scan wirklich löschen?\n\n"
                f"Paket: {last_scan.get('paketnummer', 'N/A')}\n"
                f"Zeit: {last_scan['timestamp'].strftime('%H:%M:%S')}"
        ):
            return

        # Aus Datenbank löschen
        try:
            if self.scan_repository.delete_scan_position(
                    last_scan["id"],
                    self.user["benutzer_name"]
            ):
                # Aus Liste entfernen
                self.scan_list.remove_last()

                # Statistik anpassen
                self.scan_count -= 1
                if last_scan.get("status") == "success":
                    self.success_count -= 1
                else:
                    self.error_count -= 1

                self._update_statistics()

                self.status_bar.set_status("Scan gelöscht", "info")
            else:
                show_error(self, "Fehler beim Löschen des Scans")

        except Exception as e:
            logger.error(f"Fehler beim Löschen: {e}")
            show_error(self, "Datenbankfehler beim Löschen")

    def _on_scan_selected(self, scan_data: Dict[str, Any]):
        """Wird aufgerufen wenn ein Scan ausgewählt wird"""
        # Details anzeigen
        details = (
            f"Scan-Details:\n\n"
            f"Zeit: {scan_data['timestamp'].strftime('%H:%M:%S')}\n"
            f"Auftrag: {scan_data.get('auftragsnummer', 'N/A')}\n"
            f"Paket: {scan_data.get('paketnummer', 'N/A')}\n"
            f"Kunde: {scan_data.get('kunde', 'N/A')}"
        )

        show_info(self, details, "Scan-Details")

    def _show_daily_report(self):
        """Zeigt den Tagesbericht"""
        # TODO: Tagesbericht implementieren
        stats = self.scan_repository.get_daily_statistics()

        report = (
            f"Tagesbericht - {datetime.now().strftime('%d.%m.%Y')}\n\n"
            f"Benutzer: {self.user['benutzer_name']}\n"
            f"Arbeitszeit: {self.work_time_label.cget('text').split(': ')[1]}\n\n"
            f"Scans gesamt: {self.scan_count}\n"
            f"Erfolgreich: {self.success_count}\n"
            f"Fehler: {self.error_count}\n"
            f"Durchschnitt/Stunde: {self.avg_per_hour_label.cget('text')}"
        )

        show_info(self, report, "Tagesbericht")

    def _handle_logout(self):
        """Behandelt den Logout"""
        # Bestätigung
        if not confirm_dialog(
                self,
                "Möchten Sie sich wirklich abmelden?\n\n"
                "Alle nicht gespeicherten Daten gehen verloren."
        ):
            return

        # Session beenden
        if self.session_id:
            self.scan_repository.close_session(self.session_id)

        # Ausstempeln
        self.user_repository.clock_out(self.user["id"])

        # Callback aufrufen
        if self.on_logout:
            self.on_logout()

    def cleanup(self):
        """Aufräumen beim Beenden"""
        logger.info(f"User-Panel wird aufgeräumt für {self.user['benutzer_name']}")

        # Timer stoppen
        self._stop_timers()

        # Scanner aufräumen
        if self.scanner_screen:
            self.scanner_screen.cleanup()

        # Session beenden falls noch offen
        if self.session_id:
            self.scan_repository.close_session(self.session_id)

        # Repositories schließen
        if self.scan_repository:
            self.scan_repository.close()

        if self.user_repository:
            self.user_repository.close()