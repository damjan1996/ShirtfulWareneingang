#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wareneingang Scanner Anwendung - Haupteinstiegspunkt

Diese Anwendung ermöglicht:
- RFID-basierte Benutzeranmeldung
- QR-Code Scanning von Paketen
- Multi-User Support
- Automatische Zeiterfassung
- Datenbank-Integration

Autor: Shirtful GmbH
Version: 1.0.0
"""

import sys
import os
import logging
import tkinter as tk
from tkinter import messagebox
import signal
import argparse
from datetime import datetime

# Füge src-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Imports aus unserem Projekt
from src.gui.main_window import MainWindow
from src.database.connection import DatabaseConnection
from src.utils.logger import setup_logger
from config.settings import Settings
from config.constants import *


class WareneingangApp:
    """Hauptanwendungsklasse für die Wareneingang-Scanner-Anwendung"""

    def __init__(self, debug=False):
        """
        Initialisiert die Anwendung

        Args:
            debug: Debug-Modus aktivieren
        """
        self.debug = debug
        self.logger = None
        self.settings = None
        self.db_connection = None
        self.root = None
        self.main_window = None

    def setup_logging(self):
        """Logging-System konfigurieren"""
        log_level = logging.DEBUG if self.debug else logging.INFO
        self.logger = setup_logging(level=log_level)
        self.logger.info("=" * 60)
        self.logger.info(f"Wareneingang Scanner v{APP_VERSION} gestartet")
        self.logger.info(f"Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Debug-Modus: {self.debug}")
        self.logger.info("=" * 60)

    def load_settings(self):
        """Einstellungen laden"""
        try:
            self.settings = Settings()
            self.settings.load()
            self.logger.info("Einstellungen erfolgreich geladen")
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Einstellungen: {e}")
            return False

    def test_database_connection(self):
        """Datenbankverbindung testen"""
        try:
            self.logger.info("Teste Datenbankverbindung...")

            self.db_connection = DatabaseConnection(
                server=self.settings.db_server,
                database=self.settings.db_name,
                username=self.settings.db_user,
                password=self.settings.db_password
            )

            if self.db_connection.connect():
                self.logger.info("✅ Datenbankverbindung erfolgreich")

                # Teste eine einfache Query
                cursor = self.db_connection.execute_query(
                    "SELECT COUNT(*) FROM dbo.ScannBenutzer WHERE xStatus = 0"
                )
                count = cursor.fetchone()[0]
                self.logger.info(f"Aktive Benutzer in Datenbank: {count}")

                return True
            else:
                self.logger.error("❌ Datenbankverbindung fehlgeschlagen")
                return False

        except Exception as e:
            self.logger.error(f"Datenbankfehler: {e}")
            return False

    def check_hardware(self):
        """Hardware-Komponenten prüfen"""
        self.logger.info("Prüfe Hardware-Komponenten...")

        # RFID-Reader prüfen (später implementieren)
        self.logger.info("- RFID-Reader: Wird im HID-Modus betrieben (keine Prüfung nötig)")

        # Kamera prüfen
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                self.logger.info("- Kamera: ✅ Verfügbar")
                cap.release()
            else:
                self.logger.warning("- Kamera: ⚠️ Nicht verfügbar")
        except Exception as e:
            self.logger.warning(f"- Kamera: ⚠️ Fehler beim Prüfen: {e}")

    def create_gui(self):
        """GUI erstellen und konfigurieren"""
        try:
            self.logger.info("Erstelle Benutzeroberfläche...")

            # Tkinter Root-Fenster
            self.root = tk.Tk()
            self.root.title(f"Wareneingang Scanner v{APP_VERSION}")

            # Fenster-Icon setzen (falls vorhanden)
            icon_path = os.path.join("assets", "images", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)

            # Fenster zentrieren
            self.center_window(1024, 768)

            # Hauptfenster erstellen
            self.main_window = MainWindow(
                self.root,
                self.db_connection,
                self.settings,
                self.logger
            )

            # Event-Handler
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # Tastenkombinationen
            self.setup_keyboard_shortcuts()

            self.logger.info("GUI erfolgreich erstellt")
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der GUI: {e}")
            return False

    def center_window(self, width, height):
        """Fenster auf dem Bildschirm zentrieren"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(800, 600)

    def setup_keyboard_shortcuts(self):
        """Globale Tastenkombinationen einrichten"""
        # F11 - Vollbild
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        # Escape - Vollbild verlassen
        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())
        # Ctrl+Q - Beenden
        self.root.bind("<Control-q>", lambda e: self.on_closing())
        # F1 - Hilfe
        self.root.bind("<F1>", lambda e: self.show_help())

    def toggle_fullscreen(self):
        """Vollbildmodus umschalten"""
        current_state = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not current_state)

    def exit_fullscreen(self):
        """Vollbildmodus verlassen"""
        self.root.attributes("-fullscreen", False)

    def show_help(self):
        """Hilfe-Dialog anzeigen"""
        help_text = f"""
Wareneingang Scanner v{APP_VERSION}

Tastenkombinationen:
- F11: Vollbildmodus
- ESC: Vollbild verlassen
- F1: Diese Hilfe
- Ctrl+Q: Programm beenden

RFID-Login:
Halten Sie Ihre RFID-Karte an den Reader

QR-Code scannen:
Klicken Sie auf "Paket scannen" oder
halten Sie das Paket vor die Kamera
        """
        messagebox.showinfo("Hilfe", help_text)

    def on_closing(self):
        """Anwendung beenden"""
        # Bestätigung
        if messagebox.askokcancel("Beenden", "Möchten Sie die Anwendung wirklich beenden?"):
            self.logger.info("Anwendung wird beendet...")

            # Aufräumen
            if self.main_window:
                self.main_window.cleanup()

            if self.db_connection:
                self.db_connection.close()

            # GUI schließen
            if self.root:
                self.root.destroy()

            self.logger.info("Anwendung beendet")
            sys.exit(0)

    def run(self):
        """Anwendung starten"""
        try:
            # 1. Logging einrichten
            self.setup_logging()

            # 2. Einstellungen laden
            if not self.load_settings():
                messagebox.showerror(
                    "Fehler",
                    "Einstellungen konnten nicht geladen werden.\n"
                    "Bitte prüfen Sie die config/settings.py"
                )
                return False

            # 3. Datenbankverbindung testen
            if not self.test_database_connection():
                response = messagebox.askyesno(
                    "Datenbankfehler",
                    "Keine Verbindung zur Datenbank möglich.\n\n"
                    "Möchten Sie trotzdem fortfahren?\n"
                    "(Eingeschränkte Funktionalität)"
                )
                if not response:
                    return False

            # 4. Hardware prüfen
            self.check_hardware()

            # 5. GUI erstellen
            if not self.create_gui():
                messagebox.showerror("Fehler", "GUI konnte nicht erstellt werden")
                return False

            # 6. GUI-Hauptschleife starten
            self.logger.info("Starte GUI-Hauptschleife...")
            self.root.mainloop()

            return True

        except Exception as e:
            self.logger.critical(f"Kritischer Fehler: {e}", exc_info=True)
            messagebox.showerror("Kritischer Fehler", f"Ein schwerwiegender Fehler ist aufgetreten:\n\n{e}")
            return False


def handle_signal(signum, frame):
    """Signal-Handler für sauberes Beenden"""
    print("\nProgramm wird beendet...")
    sys.exit(0)


def main():
    """Hauptfunktion"""
    # Kommandozeilen-Argumente
    parser = argparse.ArgumentParser(
        description="Wareneingang Scanner Anwendung"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug-Modus aktivieren"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Wareneingang Scanner v{APP_VERSION}"
    )

    args = parser.parse_args()

    # Signal-Handler registrieren
    signal.signal(signal.SIGINT, handle_signal)

    # Anwendung erstellen und starten
    app = WareneingangApp(debug=args.debug)
    success = app.run()

    # Exit-Code basierend auf Erfolg
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()