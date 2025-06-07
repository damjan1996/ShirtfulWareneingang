#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hauptfenster der Wareneingang-Anwendung
Verwaltet Login-Screen und Multi-User Tabs
"""

import tkinter as tk
from tkinter import ttk
import logging
import sys
from typing import Dict, Optional
from datetime import datetime

from config.constants import (
    WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    Colors, ScanTypes
)
from config.settings import GUI_SETTINGS, USER_SETTINGS
from src.database import get_connection_pool
from .login_screen import LoginScreen
from .user_panel import UserPanel
from .styles import Styles, apply_theme
from . import center_window, set_main_window, event_manager, Events

logger = logging.getLogger(__name__)


class MainWindow(tk.Tk):
    """
    Hauptfenster der Anwendung
    Verwaltet den Login-Screen und die Benutzer-Tabs
    """

    def __init__(self):
        """Initialisiert das Hauptfenster"""
        super().__init__()

        # Als globales Hauptfenster registrieren
        set_main_window(self)

        # Fenster-Konfiguration
        self.title(GUI_SETTINGS["window"]["title"])
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.geometry(f"{WINDOW_DEFAULT_WIDTH}x{WINDOW_DEFAULT_HEIGHT}")

        # Icon setzen (falls vorhanden)
        try:
            icon_path = GUI_SETTINGS["window"].get("icon")
            if icon_path:
                self.iconbitmap(icon_path)
        except:
            pass

        # Theme anwenden
        apply_theme(self)

        # Variablen
        self.active_users: Dict[int, Dict] = {}  # user_id -> user_data
        self.user_panels: Dict[int, UserPanel] = {}  # user_id -> UserPanel
        self.connection_pool = get_connection_pool()

        # UI erstellen
        self._create_ui()

        # Event-Handler registrieren
        self._register_events()

        # Fenster zentrieren
        center_window(self, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)

        # Beim Schließen aufräumen
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        logger.info("Hauptfenster initialisiert")

    def _create_ui(self):
        """Erstellt die Benutzeroberfläche"""

        # Hauptcontainer
        self.main_container = tk.Frame(self, bg=Styles.COLORS["background"])
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Header erstellen
        self._create_header()

        # Content-Bereich (für Login/Tabs)
        self.content_frame = tk.Frame(
            self.main_container,
            bg=Styles.COLORS["background"]
        )
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Login-Screen anzeigen
        self._show_login_screen()

        # Statusleiste
        self._create_status_bar()

    def _create_header(self):
        """Erstellt den Header-Bereich"""
        self.header_frame = tk.Frame(
            self.main_container,
            bg=Styles.COLORS["primary"],
            height=60
        )
        self.header_frame.pack(fill=tk.X)
        self.header_frame.pack_propagate(False)

        # Logo/Titel
        title_label = tk.Label(
            self.header_frame,
            text="SHIRTFUL - Wareneingang Scanner",
            font=Styles.get_font("bold", "xlarge"),
            fg="white",
            bg=Styles.COLORS["primary"]
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        # Info-Bereich rechts
        info_frame = tk.Frame(self.header_frame, bg=Styles.COLORS["primary"])
        info_frame.pack(side=tk.RIGHT, padx=20, pady=10)

        # Arbeitsplatz
        self.station_label = tk.Label(
            info_frame,
            text=f"Station: Wareneingang-01",
            font=Styles.get_font("normal", "medium"),
            fg="white",
            bg=Styles.COLORS["primary"]
        )
        self.station_label.pack(side=tk.RIGHT)

    def _create_status_bar(self):
        """Erstellt die Statusleiste"""
        self.status_bar = tk.Frame(
            self.main_container,
            bg=Styles.COLORS["surface"],
            height=30
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.pack_propagate(False)

        # Status-Text links
        self.status_label = tk.Label(
            self.status_bar,
            text="Bereit",
            font=Styles.get_font("normal", "small"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["surface"],
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Verbindungsstatus
        self.connection_label = tk.Label(
            self.status_bar,
            text="● Verbunden",
            font=Styles.get_font("normal", "small"),
            fg=Styles.COLORS["success"],
            bg=Styles.COLORS["surface"]
        )
        self.connection_label.pack(side=tk.RIGHT, padx=10)

        # Benutzer-Anzahl
        self.user_count_label = tk.Label(
            self.status_bar,
            text="0 Benutzer angemeldet",
            font=Styles.get_font("normal", "small"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["surface"]
        )
        self.user_count_label.pack(side=tk.RIGHT, padx=20)

    def _show_login_screen(self):
        """Zeigt den Login-Screen an"""
        # Vorhandenen Content entfernen
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Login-Screen erstellen
        self.login_screen = LoginScreen(
            self.content_frame,
            on_login_success=self._on_user_login
        )
        self.login_screen.pack(fill=tk.BOTH, expand=True)

        # Wenn bereits Benutzer angemeldet, Tab-View anzeigen
        if self.active_users:
            self._show_tab_view()

    def _show_tab_view(self):
        """Zeigt die Tab-Ansicht für mehrere Benutzer"""
        # Login-Screen entfernen falls vorhanden
        if hasattr(self, 'login_screen') and self.login_screen.winfo_exists():
            self.login_screen.pack_forget()

        # Tab-Container erstellen falls nicht vorhanden
        if not hasattr(self, 'tab_container'):
            self._create_tab_container()
        else:
            self.tab_container.pack(fill=tk.BOTH, expand=True)

    def _create_tab_container(self):
        """Erstellt den Tab-Container"""
        # Container-Frame
        self.tab_frame = tk.Frame(self.content_frame, bg=Styles.COLORS["background"])
        self.tab_frame.pack(fill=tk.BOTH, expand=True)

        # Button-Leiste für Login-Button
        button_frame = tk.Frame(self.tab_frame, bg=Styles.COLORS["background"])
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        # Neuer Login Button
        self.new_login_button = tk.Button(
            button_frame,
            text="➕ Weiteren Benutzer anmelden",
            font=Styles.get_font("normal", "medium"),
            bg=Styles.COLORS["primary"],
            fg="white",
            activebackground=Styles.COLORS["primary_dark"],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10,
            command=self._show_login_dialog
        )
        self.new_login_button.pack(side=tk.LEFT)

        # Tab-Widget
        style = ttk.Style()
        style.configure(
            "Custom.TNotebook",
            background=Styles.COLORS["background"],
            tabposition="n"
        )
        style.configure(
            "Custom.TNotebook.Tab",
            padding=[20, 10],
            font=Styles.get_font("normal", "medium")
        )

        self.tab_container = ttk.Notebook(
            self.tab_frame,
            style="Custom.TNotebook"
        )
        self.tab_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Tab-Wechsel Event
        self.tab_container.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_user_login(self, user: dict):
        """
        Wird aufgerufen wenn ein Benutzer sich erfolgreich anmeldet

        Args:
            user: Benutzerdaten
        """
        user_id = user["id"]

        # Prüfen ob Benutzer bereits angemeldet
        if user_id in self.active_users:
            # Tab aktivieren
            self._activate_user_tab(user_id)
            return

        logger.info(f"Benutzer angemeldet: {user['benutzer_name']} (ID: {user_id})")

        # Benutzer hinzufügen
        self.active_users[user_id] = user

        # Tab-View anzeigen falls erster Benutzer
        if len(self.active_users) == 1:
            self._show_tab_view()

        # Benutzer-Panel erstellen
        self._create_user_tab(user)

        # Status aktualisieren
        self._update_status()

        # Event auslösen
        event_manager.emit(Events.USER_LOGIN, user)

    def _create_user_tab(self, user: dict):
        """Erstellt einen Tab für einen Benutzer"""
        user_id = user["id"]

        # Tab-Frame
        tab_frame = tk.Frame(self.tab_container, bg=Styles.COLORS["background"])

        # Benutzer-Panel erstellen
        user_panel = UserPanel(
            tab_frame,
            user=user,
            scan_type_id=ScanTypes.WARENEINGANG.value,
            on_logout=lambda: self._on_user_logout(user_id)
        )
        user_panel.pack(fill=tk.BOTH, expand=True)

        # Tab hinzufügen
        tab_name = f"{user['benutzer_name']}"
        self.tab_container.add(tab_frame, text=tab_name)

        # Panel speichern
        self.user_panels[user_id] = user_panel

        # Tab aktivieren
        self.tab_container.select(tab_frame)

    def _activate_user_tab(self, user_id: int):
        """Aktiviert den Tab eines Benutzers"""
        # Tab-Index finden
        for i in range(self.tab_container.index("end")):
            tab_frame = self.tab_container.nametowidget(
                self.tab_container.tabs()[i]
            )
            # Panel im Tab suchen
            for child in tab_frame.winfo_children():
                if isinstance(child, UserPanel) and child.user["id"] == user_id:
                    self.tab_container.select(i)
                    return

    def _on_user_logout(self, user_id: int):
        """
        Wird aufgerufen wenn ein Benutzer sich abmeldet

        Args:
            user_id: ID des Benutzers
        """
        if user_id not in self.active_users:
            return

        user = self.active_users[user_id]
        logger.info(f"Benutzer abgemeldet: {user['benutzer_name']} (ID: {user_id})")

        # Tab entfernen
        self._remove_user_tab(user_id)

        # Benutzer entfernen
        del self.active_users[user_id]

        # Panel entfernen
        if user_id in self.user_panels:
            self.user_panels[user_id].cleanup()
            del self.user_panels[user_id]

        # Login-Screen aus Liste entfernen
        if hasattr(self, 'login_screen'):
            self.login_screen.remove_user_from_list(user_id)

        # Wenn keine Benutzer mehr, Login-Screen anzeigen
        if not self.active_users:
            self.tab_container.pack_forget()
            self._show_login_screen()

        # Status aktualisieren
        self._update_status()

        # Event auslösen
        event_manager.emit(Events.USER_LOGOUT, user)

    def _remove_user_tab(self, user_id: int):
        """Entfernt den Tab eines Benutzers"""
        # Tab-Index finden
        for i in range(self.tab_container.index("end")):
            tab_frame = self.tab_container.nametowidget(
                self.tab_container.tabs()[i]
            )
            # Panel im Tab suchen
            for child in tab_frame.winfo_children():
                if isinstance(child, UserPanel) and child.user["id"] == user_id:
                    self.tab_container.forget(i)
                    tab_frame.destroy()
                    return

    def _show_login_dialog(self):
        """Zeigt einen Dialog für zusätzliche Anmeldungen"""
        # Login-Dialog erstellen
        dialog = tk.Toplevel(self)
        dialog.title("Weiteren Benutzer anmelden")
        dialog.geometry("800x600")
        dialog.transient(self)
        dialog.grab_set()

        # Dialog zentrieren
        center_window(dialog, 800, 600)

        # Login-Screen im Dialog
        login_screen = LoginScreen(
            dialog,
            on_login_success=lambda user: self._on_dialog_login(dialog, user)
        )
        login_screen.pack(fill=tk.BOTH, expand=True)

        # Schließen-Button
        close_button = tk.Button(
            dialog,
            text="Abbrechen",
            font=Styles.get_font("normal", "medium"),
            bg=Styles.COLORS["surface"],
            fg=Styles.COLORS["text_primary"],
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=dialog.destroy
        )
        close_button.pack(pady=10)

    def _on_dialog_login(self, dialog: tk.Toplevel, user: dict):
        """Login aus Dialog heraus"""
        dialog.destroy()
        self._on_user_login(user)

    def _on_tab_changed(self, event):
        """Wird aufgerufen wenn ein Tab gewechselt wird"""
        current_tab = event.widget.index("current")

        # Aktiven Benutzer ermitteln
        if current_tab < len(self.tab_container.tabs()):
            tab_frame = self.tab_container.nametowidget(
                self.tab_container.tabs()[current_tab]
            )

            # Panel im Tab suchen
            for child in tab_frame.winfo_children():
                if isinstance(child, UserPanel):
                    active_user = child.user
                    logger.debug(f"Tab gewechselt zu: {active_user['benutzer_name']}")

                    # Event auslösen
                    event_manager.emit(Events.TAB_CHANGED, active_user)
                    break

    def _update_status(self):
        """Aktualisiert die Statusanzeige"""
        user_count = len(self.active_users)

        # Benutzer-Anzahl
        if user_count == 0:
            self.user_count_label.configure(text="Keine Benutzer angemeldet")
        elif user_count == 1:
            self.user_count_label.configure(text="1 Benutzer angemeldet")
        else:
            self.user_count_label.configure(text=f"{user_count} Benutzer angemeldet")

        # Status-Text
        if user_count > 0:
            self.status_label.configure(text="Scan-Bereit")
        else:
            self.status_label.configure(text="Warte auf Anmeldung")

    def _register_events(self):
        """Registriert Event-Handler"""

        # Fehler-Events
        event_manager.subscribe(
            Events.ERROR_OCCURRED,
            lambda error: self.status_label.configure(
                text=f"Fehler: {error}",
                fg=Styles.COLORS["error"]
            )
        )

    def set_status(self, message: str, status_type: str = "info"):
        """
        Setzt den Status-Text

        Args:
            message: Statusnachricht
            status_type: Typ ("info", "success", "warning", "error")
        """
        color_map = {
            "info": Styles.COLORS["text_secondary"],
            "success": Styles.COLORS["success"],
            "warning": Styles.COLORS["warning"],
            "error": Styles.COLORS["error"]
        }

        color = color_map.get(status_type, Styles.COLORS["text_secondary"])
        self.status_label.configure(text=message, fg=color)

    def _check_connection(self):
        """Prüft die Datenbankverbindung"""
        try:
            # Verbindung testen
            pool_stats = self.connection_pool.statistics

            if pool_stats["total_connections"] > 0:
                self.connection_label.configure(
                    text="● Verbunden",
                    fg=Styles.COLORS["success"]
                )
            else:
                self.connection_label.configure(
                    text="● Getrennt",
                    fg=Styles.COLORS["error"]
                )
        except:
            self.connection_label.configure(
                text="● Getrennt",
                fg=Styles.COLORS["error"]
            )

        # Alle 5 Sekunden prüfen
        self.after(5000, self._check_connection)

    def _on_closing(self):
        """Wird beim Schließen des Fensters aufgerufen"""
        logger.info("Anwendung wird beendet...")

        # Alle Benutzer abmelden
        for user_id in list(self.active_users.keys()):
            self._on_user_logout(user_id)

        # Login-Screen aufräumen
        if hasattr(self, 'login_screen'):
            self.login_screen.cleanup()

        # Verbindungen schließen
        if self.connection_pool:
            self.connection_pool.close_all()

        # Fenster schließen
        self.destroy()

        # Anwendung beenden
        sys.exit(0)

    def run(self):
        """Startet die Hauptschleife"""
        logger.info("Hauptfenster gestartet")

        # Verbindungsprüfung starten
        self._check_connection()

        # Hauptschleife
        self.mainloop()