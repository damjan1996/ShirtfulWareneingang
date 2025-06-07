#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Login-Screen für RFID-basierte Authentifizierung
Zeigt einen großen, touch-freundlichen Login-Bildschirm
"""

import tkinter as tk
from tkinter import ttk
import logging
import threading
import time
from typing import Optional, Callable
from datetime import datetime

from config.constants import Colors, Fonts, RFIDMessages, RFID_SCAN_TIMEOUT
from config.settings import GUI_SETTINGS, RFID_SETTINGS, AUDIO_SETTINGS
from src.database.user_repository import UserRepository
from src.rfid.hid_listener import HIDListener
from src.utils.audio_player import AudioPlayer
from .styles import Styles
from .widgets import BigButton, RFIDIndicator

logger = logging.getLogger(__name__)


class LoginScreen(tk.Frame):
    """
    RFID-Login-Bildschirm
    Ermöglicht die Anmeldung mehrerer Benutzer über RFID-Tags
    """

    def __init__(self, parent, on_login_success: Callable = None, **kwargs):
        """
        Initialisiert den Login-Screen

        Args:
            parent: Eltern-Widget
            on_login_success: Callback-Funktion bei erfolgreichem Login
            **kwargs: Weitere Tkinter-Argumente
        """
        super().__init__(parent, **kwargs)

        # Callbacks
        self.on_login_success = on_login_success

        # Services
        self.user_repository = UserRepository()
        self.rfid_listener = HIDListener()
        self.audio_player = AudioPlayer()

        # Status
        self.is_scanning = False
        self.current_scan_buffer = ""
        self.scan_timeout_timer = None
        self.logged_in_users = set()  # Set von User-IDs die bereits eingeloggt sind

        # UI erstellen
        self._create_ui()

        # RFID-Listener konfigurieren
        self.rfid_listener.on_tag_received = self._on_rfid_tag_received

        # Style anwenden
        self.configure(bg=Styles.COLORS["background"])

    def _create_ui(self):
        """Erstellt die Benutzeroberfläche"""

        # Hauptcontainer mit Padding
        main_container = tk.Frame(self, bg=Styles.COLORS["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)

        # Logo/Titel-Bereich
        self._create_header(main_container)

        # RFID-Scan-Bereich
        self._create_scan_area(main_container)

        # Status-Bereich
        self._create_status_area(main_container)

        # Benutzer-Liste (bereits eingeloggte)
        self._create_user_list(main_container)

        # Footer
        self._create_footer(main_container)

    def _create_header(self, parent):
        """Erstellt den Header-Bereich"""
        header_frame = tk.Frame(parent, bg=Styles.COLORS["background"])
        header_frame.pack(fill=tk.X, pady=(0, 30))

        # Titel
        title_label = tk.Label(
            header_frame,
            text="Wareneingang Scanner",
            font=Styles.get_font("title", "xxlarge"),
            fg=Styles.COLORS["primary"],
            bg=Styles.COLORS["background"]
        )
        title_label.pack()

        # Untertitel
        subtitle_label = tk.Label(
            header_frame,
            text="RFID-Karte zum Anmelden scannen",
            font=Styles.get_font("normal", "large"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["background"]
        )
        subtitle_label.pack()

        # Datum und Uhrzeit
        self.datetime_label = tk.Label(
            header_frame,
            text="",
            font=Styles.get_font("normal", "medium"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["background"]
        )
        self.datetime_label.pack(pady=(10, 0))
        self._update_datetime()

    def _create_scan_area(self, parent):
        """Erstellt den RFID-Scan-Bereich"""
        scan_frame = tk.Frame(parent, bg=Styles.COLORS["background"])
        scan_frame.pack(fill=tk.BOTH, expand=True, pady=30)

        # RFID-Indikator
        self.rfid_indicator = RFIDIndicator(
            scan_frame,
            size=200,
            bg=Styles.COLORS["background"]
        )
        self.rfid_indicator.pack()

        # Scan-Button
        self.scan_button = BigButton(
            scan_frame,
            text="🔓 RFID-Karte scannen",
            command=self._toggle_scanning,
            bg_color=Styles.COLORS["primary"],
            hover_color=Styles.COLORS["primary_dark"],
            height=100,
            font_size=32
        )
        self.scan_button.pack(pady=30)

        # Status-Text
        self.status_label = tk.Label(
            scan_frame,
            text=RFIDMessages.WAITING,
            font=Styles.get_font("normal", "large"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["background"]
        )
        self.status_label.pack()

    def _create_status_area(self, parent):
        """Erstellt den Status-Bereich"""
        status_frame = tk.Frame(parent, bg=Styles.COLORS["background"])
        status_frame.pack(fill=tk.X, pady=20)

        # Letzter Scan
        self.last_scan_frame = tk.Frame(status_frame, bg=Styles.COLORS["surface"])
        self.last_scan_frame.pack(fill=tk.X, padx=50)

        self.last_scan_label = tk.Label(
            self.last_scan_frame,
            text="",
            font=Styles.get_font("normal", "medium"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["surface"],
            pady=10
        )
        self.last_scan_label.pack()

    def _create_user_list(self, parent):
        """Erstellt die Liste der eingeloggten Benutzer"""
        # Frame für Benutzerliste
        user_frame = tk.LabelFrame(
            parent,
            text="Angemeldete Benutzer",
            font=Styles.get_font("bold", "medium"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["background"],
            relief=tk.FLAT,
            borderwidth=2
        )
        user_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        # Scrollbare Liste
        list_container = tk.Frame(user_frame, bg=Styles.COLORS["surface"])
        list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas für Scrolling
        canvas = tk.Canvas(
            list_container,
            bg=Styles.COLORS["surface"],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            list_container,
            orient="vertical",
            command=canvas.yview
        )

        self.user_list_frame = tk.Frame(canvas, bg=Styles.COLORS["surface"])

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_frame = canvas.create_window(
            (0, 0),
            window=self.user_list_frame,
            anchor="nw"
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Canvas-Größe anpassen
        def configure_canvas(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_frame, width=canvas.winfo_width())

        self.user_list_frame.bind("<Configure>", configure_canvas)
        canvas.bind("<Configure>", configure_canvas)

        # Keine Benutzer Nachricht
        self.no_users_label = tk.Label(
            self.user_list_frame,
            text="Noch keine Benutzer angemeldet",
            font=Styles.get_font("normal", "medium"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["surface"],
            pady=20
        )
        self.no_users_label.pack()

    def _create_footer(self, parent):
        """Erstellt den Footer-Bereich"""
        footer_frame = tk.Frame(parent, bg=Styles.COLORS["background"])
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Info-Text
        info_label = tk.Label(
            footer_frame,
            text="Halten Sie Ihre RFID-Karte an den Reader",
            font=Styles.get_font("normal", "small"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["background"]
        )
        info_label.pack(pady=(0, 10))

    def _toggle_scanning(self):
        """Schaltet den Scan-Modus um"""
        if self.is_scanning:
            self.stop_scanning()
        else:
            self.start_scanning()

    def start_scanning(self):
        """Startet das RFID-Scanning"""
        if self.is_scanning:
            return

        logger.info("RFID-Scanning gestartet")
        self.is_scanning = True

        # UI aktualisieren
        self.scan_button.configure(
            text="⏹ Scannen beenden",
            bg_color=Styles.COLORS["secondary"]
        )
        self.status_label.configure(
            text=RFIDMessages.SCANNING,
            fg=Styles.COLORS["info"]
        )
        self.rfid_indicator.set_scanning(True)

        # RFID-Listener starten
        self.rfid_listener.start()

        # Timeout starten
        self._start_scan_timeout()

    def stop_scanning(self):
        """Stoppt das RFID-Scanning"""
        if not self.is_scanning:
            return

        logger.info("RFID-Scanning gestoppt")
        self.is_scanning = False

        # UI zurücksetzen
        self.scan_button.configure(
            text="🔓 RFID-Karte scannen",
            bg_color=Styles.COLORS["primary"]
        )
        self.status_label.configure(
            text=RFIDMessages.WAITING,
            fg=Styles.COLORS["text_secondary"]
        )
        self.rfid_indicator.set_scanning(False)

        # RFID-Listener stoppen
        self.rfid_listener.stop()

        # Timeout stoppen
        self._stop_scan_timeout()

        # Buffer leeren
        self.current_scan_buffer = ""

    def _start_scan_timeout(self):
        """Startet den Scan-Timeout"""
        self._stop_scan_timeout()
        self.scan_timeout_timer = self.after(
            RFID_SCAN_TIMEOUT * 1000,
            self._on_scan_timeout
        )

    def _stop_scan_timeout(self):
        """Stoppt den Scan-Timeout"""
        if self.scan_timeout_timer:
            self.after_cancel(self.scan_timeout_timer)
            self.scan_timeout_timer = None

    def _on_scan_timeout(self):
        """Wird aufgerufen wenn der Scan-Timeout erreicht wird"""
        logger.warning("RFID-Scan Timeout")
        self.stop_scanning()

        # Fehlermeldung
        self.status_label.configure(
            text=RFIDMessages.ERROR_TIMEOUT,
            fg=Styles.COLORS["error"]
        )
        self.rfid_indicator.set_error()

        # Audio-Feedback
        if AUDIO_SETTINGS["enabled"]:
            self.audio_player.play_sound("login_error")

    def _on_rfid_tag_received(self, tag_id: str):
        """
        Wird aufgerufen wenn ein RFID-Tag erkannt wurde

        Args:
            tag_id: RFID-Tag ID als Hex-String
        """
        if not self.is_scanning:
            return

        logger.info(f"RFID-Tag empfangen: {tag_id}")

        # Scanning stoppen
        self.stop_scanning()

        # Tag verarbeiten in separatem Thread
        threading.Thread(
            target=self._process_rfid_tag,
            args=(tag_id,),
            daemon=True
        ).start()

    def _process_rfid_tag(self, tag_id: str):
        """
        Verarbeitet einen RFID-Tag

        Args:
            tag_id: RFID-Tag ID
        """
        # UI-Update (im Haupt-Thread)
        self.after(0, lambda: self.status_label.configure(
            text="Karte wird überprüft...",
            fg=Styles.COLORS["info"]
        ))
        self.after(0, lambda: self.rfid_indicator.set_processing())

        try:
            # Benutzer authentifizieren
            user = self.user_repository.authenticate_by_rfid(tag_id)

            if user:
                # Prüfen ob Benutzer bereits eingeloggt
                if user["id"] in self.logged_in_users:
                    # Bereits eingeloggt
                    self.after(0, lambda: self._show_already_logged_in(user))
                else:
                    # Erfolgreich authentifiziert
                    self.after(0, lambda: self._on_login_success(user))
            else:
                # Authentifizierung fehlgeschlagen
                self.after(0, lambda: self._on_login_failed(tag_id))

        except Exception as e:
            logger.error(f"Fehler bei RFID-Verarbeitung: {e}")
            self.after(0, lambda: self._on_login_error(str(e)))

    def _on_login_success(self, user: dict):
        """Erfolgreiche Anmeldung"""
        logger.info(f"Login erfolgreich: {user['benutzer_name']}")

        # Benutzer zur Liste hinzufügen
        self.logged_in_users.add(user["id"])

        # UI aktualisieren
        self.status_label.configure(
            text=f"{RFIDMessages.SUCCESS} - {user['benutzer_name']}",
            fg=Styles.COLORS["success"]
        )
        self.rfid_indicator.set_success()

        # Letzter Scan
        self.last_scan_label.configure(
            text=f"✅ {user['benutzer_name']} - {datetime.now().strftime('%H:%M:%S')}"
        )

        # Benutzer zur Liste hinzufügen
        self._add_user_to_list(user)

        # Audio-Feedback
        if AUDIO_SETTINGS["enabled"]:
            self.audio_player.play_sound("login_success")

        # Callback aufrufen
        if self.on_login_success:
            self.on_login_success(user)

        # Nach 3 Sekunden zurücksetzen
        self.after(3000, self._reset_ui)

    def _on_login_failed(self, tag_id: str):
        """Fehlgeschlagene Anmeldung"""
        logger.warning(f"Login fehlgeschlagen: Unbekannter Tag {tag_id}")

        # UI aktualisieren
        self.status_label.configure(
            text=RFIDMessages.ERROR_UNKNOWN,
            fg=Styles.COLORS["error"]
        )
        self.rfid_indicator.set_error()

        # Letzter Scan
        self.last_scan_label.configure(
            text=f"❌ Unbekannter Tag: {tag_id} - {datetime.now().strftime('%H:%M:%S')}"
        )

        # Audio-Feedback
        if AUDIO_SETTINGS["enabled"]:
            self.audio_player.play_sound("login_error")

        # Nach 3 Sekunden zurücksetzen
        self.after(3000, self._reset_ui)

    def _on_login_error(self, error_msg: str):
        """Login-Fehler"""
        logger.error(f"Login-Fehler: {error_msg}")

        # UI aktualisieren
        self.status_label.configure(
            text=RFIDMessages.ERROR_DATABASE,
            fg=Styles.COLORS["error"]
        )
        self.rfid_indicator.set_error()

        # Audio-Feedback
        if AUDIO_SETTINGS["enabled"]:
            self.audio_player.play_sound("login_error")

        # Nach 3 Sekunden zurücksetzen
        self.after(3000, self._reset_ui)

    def _show_already_logged_in(self, user: dict):
        """Zeigt an dass Benutzer bereits eingeloggt ist"""
        logger.info(f"Benutzer bereits eingeloggt: {user['benutzer_name']}")

        # UI aktualisieren
        self.status_label.configure(
            text=f"{user['benutzer_name']} ist bereits angemeldet",
            fg=Styles.COLORS["warning"]
        )
        self.rfid_indicator.set_warning()

        # Audio-Feedback
        if AUDIO_SETTINGS["enabled"]:
            self.audio_player.play_sound("warning")

        # Nach 3 Sekunden zurücksetzen
        self.after(3000, self._reset_ui)

    def _add_user_to_list(self, user: dict):
        """Fügt einen Benutzer zur Liste hinzu"""
        # "Keine Benutzer" Label entfernen
        if self.no_users_label.winfo_exists():
            self.no_users_label.pack_forget()

        # Benutzer-Frame erstellen
        user_frame = tk.Frame(
            self.user_list_frame,
            bg=Styles.COLORS["surface"],
            relief=tk.RAISED,
            borderwidth=1
        )
        user_frame.pack(fill=tk.X, padx=5, pady=2)

        # Benutzer-Info
        info_frame = tk.Frame(user_frame, bg=Styles.COLORS["surface"])
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)

        name_label = tk.Label(
            info_frame,
            text=user["benutzer_name"],
            font=Styles.get_font("bold", "medium"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["surface"]
        )
        name_label.pack(anchor=tk.W)

        time_label = tk.Label(
            info_frame,
            text=f"Angemeldet: {datetime.now().strftime('%H:%M')}",
            font=Styles.get_font("normal", "small"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["surface"]
        )
        time_label.pack(anchor=tk.W)

        # Status-Indikator
        status_label = tk.Label(
            user_frame,
            text="●",
            font=("Arial", 16),
            fg=Styles.COLORS["success"],
            bg=Styles.COLORS["surface"]
        )
        status_label.pack(side=tk.RIGHT, padx=10)

        # Frame für späteres Entfernen speichern
        user_frame.user_id = user["id"]

    def remove_user_from_list(self, user_id: int):
        """Entfernt einen Benutzer aus der Liste"""
        # Benutzer aus Set entfernen
        self.logged_in_users.discard(user_id)

        # Frame finden und entfernen
        for child in self.user_list_frame.winfo_children():
            if hasattr(child, 'user_id') and child.user_id == user_id:
                child.destroy()
                break

        # Wenn keine Benutzer mehr, Label anzeigen
        if not self.logged_in_users:
            self.no_users_label.pack()

    def _reset_ui(self):
        """Setzt die UI zurück"""
        self.status_label.configure(
            text=RFIDMessages.WAITING,
            fg=Styles.COLORS["text_secondary"]
        )
        self.rfid_indicator.reset()

    def _update_datetime(self):
        """Aktualisiert Datum und Uhrzeit"""
        now = datetime.now()
        self.datetime_label.configure(
            text=now.strftime("%A, %d. %B %Y - %H:%M:%S")
        )
        # Alle Sekunde aktualisieren
        self.after(1000, self._update_datetime)

    def cleanup(self):
        """Aufräumen beim Beenden"""
        logger.info("Login-Screen wird aufgeräumt")

        # RFID-Listener stoppen
        if self.rfid_listener:
            self.rfid_listener.stop()

        # Timer stoppen
        self._stop_scan_timeout()

        # Repository schließen
        if self.user_repository:
            self.user_repository.close()