#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RFID & QR Scanner - Tab-Version mit geteiltem Scanner
Ein Scanner für alle Benutzer, Scans gehen an aktiven Tab
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
import time

from config import APP_CONFIG
from hid_listener import HIDListener
from qr_scanner import QRScanner
from models import User, Session, QrScan
from utils import setup_logger, format_duration

# Logger setup
logger = setup_logger('MainApp', APP_CONFIG.get('LOG_LEVEL', 'INFO'))


class UserTab:
    """Tab für jeden Benutzer"""

    def __init__(self, notebook, user_data, session_data, on_logout_callback):
        self.notebook = notebook
        self.user = user_data
        self.session = session_data
        self.on_logout_callback = on_logout_callback
        self.scan_count = 0
        self.is_active = False

        # Tab erstellen
        self.frame = ttk.Frame(notebook)
        self.notebook.add(self.frame, text=user_data['BenutzerName'])

        self.setup_ui()
        self.update_timer()

        # Tab aktivieren
        self.notebook.select(self.frame)

    def setup_ui(self):
        """UI für Benutzer-Tab"""
        main_frame = ttk.Frame(self.frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header mit Benutzer-Info
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Links: Benutzer-Info
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side=tk.LEFT)

        ttk.Label(info_frame, text=f"Benutzer: {self.user['BenutzerName']}",
                  font=('Arial', 14, 'bold')).pack(anchor=tk.W)

        self.timer_label = ttk.Label(info_frame, text="Zeit: 00:00:00",
                                     font=('Arial', 12))
        self.timer_label.pack(anchor=tk.W)

        self.scan_count_label = ttk.Label(info_frame, text="Scans: 0",
                                          font=('Arial', 12))
        self.scan_count_label.pack(anchor=tk.W)

        # Rechts: Logout Button
        ttk.Button(header_frame, text="Abmelden",
                   command=self.logout).pack(side=tk.RIGHT, padx=10)

        # Scanner Bereich
        scanner_frame = ttk.LabelFrame(main_frame, text="QR-Code Scanner", padding="10")
        scanner_frame.pack(fill=tk.BOTH, expand=True)

        # Video Label
        self.video_label = ttk.Label(scanner_frame,
                                     text="Wählen Sie diesen Tab aus um zu scannen",
                                     font=('Arial', 12), anchor=tk.CENTER)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Status Bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_label = ttk.Label(status_frame, text="Tab aktivieren um zu scannen")
        self.status_label.pack(side=tk.LEFT)

        self.last_scan_label = ttk.Label(status_frame, text="")
        self.last_scan_label.pack(side=tk.RIGHT)

    def set_active(self, active):
        """Tab als aktiv/inaktiv markieren"""
        self.is_active = active
        if active:
            self.status_label.config(text="✅ Scanner aktiv - QR-Codes werden automatisch erfasst")
            self.video_label.config(text="")  # Video wird extern gesetzt
        else:
            self.status_label.config(text="Tab aktivieren um zu scannen")
            self.video_label.config(text="Wählen Sie diesen Tab aus um zu scannen")

    def on_qr_scan(self, payload):
        """QR-Code wurde gescannt"""
        try:
            # QR-Code speichern
            qr_scan = QrScan.create(self.session['ID'], payload)
            if qr_scan:
                self.scan_count += 1

                # UI aktualisieren
                self.scan_count_label.config(text=f"Scans: {self.scan_count}")
                self.last_scan_label.config(
                    text=f"Letzter: {datetime.now().strftime('%H:%M:%S')} - {payload[:40]}..."
                )

                # Visuelles Feedback
                original_bg = self.status_label.cget('background')
                self.status_label.config(background='lightgreen',
                                         text=f"✅ Erfasst: {payload[:50]}...")
                self.frame.after(1000, lambda: self.status_label.config(
                    background=original_bg,
                    text="✅ Scanner aktiv - QR-Codes werden automatisch erfasst"
                ))

                logger.info(f"QR-Code für {self.user['BenutzerName']}: {payload[:50]}")

        except Exception as e:
            logger.error(f"QR-Scan Fehler: {e}")
            self.status_label.config(text=f"❌ Fehler beim Speichern")

    def update_timer(self):
        """Timer aktualisieren"""
        try:
            # Prüfe ob Tab noch existiert
            if not self.frame.winfo_exists():
                return

            # Dauer berechnen
            start_time = datetime.fromisoformat(str(self.session['StartTS']))
            duration = int((datetime.now() - start_time).total_seconds())

            # Format: HH:MM:SS
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60

            self.timer_label.config(text=f"Zeit: {hours:02d}:{minutes:02d}:{seconds:02d}")

            # Tab-Text mit Zeit aktualisieren
            tab_text = f"{self.user['BenutzerName']} ({hours:02d}:{minutes:02d}:{seconds:02d})"
            self.notebook.tab(self.frame, text=tab_text)

            # Nächster Update
            self.frame.after(1000, self.update_timer)

        except:
            # Tab wurde entfernt
            pass

    def logout(self):
        """Benutzer abmelden"""
        if self.on_logout_callback:
            self.on_logout_callback(self.user['ID'])


class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("RFID & QR Scanner - Multi-User Tab System")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # State
        self.active_sessions = {}  # {user_id: {'session': ..., 'tab': UserTab}}
        self.current_tab = None

        # Hardware
        self.hid_listener = HIDListener(self.on_rfid_scan)
        self.qr_scanner = None  # Gemeinsamer Scanner

        # UI Setup
        self.setup_ui()

        # Scanner starten
        self.start_shared_scanner()

        # RFID Listener starten
        self.hid_listener.start()
        logger.info("Tab-basierte Multi-Scanner Anwendung mit geteiltem Scanner gestartet")

    def setup_ui(self):
        """Hauptfenster UI mit Tabs"""
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(header_frame, text="RFID & QR Scanner System",
                  font=('Arial', 16, 'bold')).pack(side=tk.LEFT)

        # RFID Status
        self.rfid_status = ttk.Label(header_frame,
                                     text="RFID-Reader bereit",
                                     font=('Arial', 11))
        self.rfid_status.pack(side=tk.RIGHT, padx=10)

        # Scanner Status
        self.scanner_status = ttk.Label(header_frame,
                                        text="Scanner: Initialisierung...",
                                        font=('Arial', 11))
        self.scanner_status.pack(side=tk.RIGHT, padx=10)

        # Notebook für Tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab-Wechsel Event
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

        # Start-Tab
        self.start_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.start_frame, text="Start")

        self.setup_start_tab()

        # Status Bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))

        self.status_label = ttk.Label(status_frame,
                                      text="Bereit - Halten Sie Ihren RFID-Tag an den Reader",
                                      font=('Arial', 11))
        self.status_label.pack(side=tk.LEFT)

        # Aktive Benutzer Zähler
        self.user_count_label = ttk.Label(status_frame,
                                          text="Aktive Benutzer: 0",
                                          font=('Arial', 11))
        self.user_count_label.pack(side=tk.RIGHT)

    def setup_start_tab(self):
        """Start-Tab mit Anleitung"""
        content = ttk.Frame(self.start_frame, padding="20")
        content.pack(fill=tk.BOTH, expand=True)

        # Willkommen
        ttk.Label(content, text="Willkommen zum Multi-User Scanner System",
                  font=('Arial', 18, 'bold')).pack(pady=(0, 20))

        # Anleitung
        instructions = ttk.LabelFrame(content, text="Anleitung", padding="15")
        instructions.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        instruction_text = """So funktioniert's:

1. RFID-Tag an Reader halten
   → Neuer Tab mit Ihrem Namen öffnet sich automatisch

2. Tab auswählen zum Scannen
   → Der Scanner ist immer für den aktiven Tab aktiv
   → QR-Codes werden automatisch erfasst

3. Abmelden
   → "Abmelden" Button im Tab klicken
   → Oder RFID-Tag erneut scannen

Mehrere Benutzer können gleichzeitig eingeloggt sein!
Der Scanner wird zwischen den Tabs geteilt."""

        ttk.Label(instructions, text=instruction_text,
                  font=('Arial', 12), justify=tk.LEFT).pack()

        # Aktive Benutzer Liste
        active_frame = ttk.LabelFrame(content, text="Aktive Benutzer", padding="10")
        active_frame.pack(fill=tk.BOTH, expand=True)

        self.active_listbox = tk.Listbox(active_frame, height=8, font=('Arial', 11))
        self.active_listbox.pack(fill=tk.BOTH, expand=True)

        # Update Timer
        self.update_active_list()

    def start_shared_scanner(self):
        """Gemeinsamen QR-Scanner starten"""
        try:
            # Dummy Video Label für Scanner (wird nicht angezeigt)
            self.scanner_video_label = ttk.Label(self.root)

            self.qr_scanner = QRScanner(
                camera_index=APP_CONFIG.get('CAMERA_INDEX', 0),
                callback=self.on_qr_scan,
                video_label=self.scanner_video_label
            )
            self.qr_scanner.start()
            self.scanner_status.config(text="Scanner: Aktiv")
            logger.info("Gemeinsamer QR-Scanner gestartet")

        except Exception as e:
            logger.error(f"Scanner Start Fehler: {e}")
            self.scanner_status.config(text="Scanner: Fehler")
            messagebox.showerror("Fehler", "Kamera konnte nicht gestartet werden")

    def on_tab_changed(self, event):
        """Tab wurde gewechselt"""
        # Alten Tab deaktivieren
        if self.current_tab:
            self.current_tab.set_active(False)

        # Neuen aktiven Tab finden
        current_widget = self.notebook.select()
        self.current_tab = None

        # Video-Label updaten
        for user_id, data in self.active_sessions.items():
            tab = data['tab']
            if str(tab.frame) == current_widget:
                self.current_tab = tab
                tab.set_active(True)
                # Video-Label umleiten
                if self.qr_scanner:
                    self.qr_scanner.video_label = tab.video_label
                break

        # Wenn Start-Tab aktiv ist
        if current_widget == str(self.start_frame):
            if self.qr_scanner:
                self.qr_scanner.video_label = self.scanner_video_label

    def on_qr_scan(self, payload):
        """QR-Code wurde gescannt - an aktiven Tab weiterleiten"""
        if self.current_tab and self.current_tab.is_active:
            self.current_tab.on_qr_scan(payload)
        else:
            logger.debug(f"QR-Code ignoriert (kein aktiver Benutzer-Tab): {payload[:50]}")

    def on_rfid_scan(self, tag_id):
        """RFID Tag wurde gescannt"""
        logger.info(f"RFID Tag erkannt: {tag_id}")
        self.rfid_status.config(text=f"Tag erkannt: {tag_id}")

        # Nach 2 Sekunden zurücksetzen
        self.root.after(2000, lambda: self.rfid_status.config(text="RFID-Reader bereit"))

        # Benutzer suchen
        user = User.get_by_epc(tag_id)
        if not user:
            self.show_status(f"❌ Unbekannter Tag: {tag_id}", error=True)
            return

        user_id = user['ID']

        # Prüfe ob bereits angemeldet
        if user_id in self.active_sessions:
            # Abmelden
            self.logout_user(user_id)
        else:
            # Anmelden und Tab erstellen
            self.login_user(user)

    def login_user(self, user):
        """Benutzer anmelden und Tab erstellen"""
        try:
            # Session erstellen
            session = Session.create(user['ID'])
            if not session:
                self.show_status("❌ Fehler beim Erstellen der Session", error=True)
                return

            # Tab erstellen
            user_tab = UserTab(
                self.notebook,
                user,
                session,
                self.logout_user
            )

            # Zu aktiven Sessions hinzufügen
            self.active_sessions[user['ID']] = {
                'session': session,
                'user': user,
                'tab': user_tab
            }

            # UI aktualisieren
            self.update_user_count()
            self.show_status(f"✅ {user['BenutzerName']} angemeldet - Tab erstellt")
            logger.info(f"Benutzer angemeldet: {user['BenutzerName']}")

        except Exception as e:
            logger.error(f"Login-Fehler: {e}")
            self.show_status(f"❌ Login fehlgeschlagen: {str(e)}", error=True)

    def logout_user(self, user_id):
        """Benutzer abmelden und Tab entfernen"""
        if user_id not in self.active_sessions:
            return

        try:
            session_data = self.active_sessions[user_id]
            session = session_data['session']
            user = session_data['user']
            tab = session_data['tab']

            # Session beenden
            Session.end(session['ID'])

            # Wenn das der aktive Tab war
            if self.current_tab == tab:
                self.current_tab = None

            # Tab entfernen
            self.notebook.forget(tab.frame)

            # Aus aktiven Sessions entfernen
            del self.active_sessions[user_id]

            # UI aktualisieren
            self.update_user_count()
            self.show_status(f"👋 {user['BenutzerName']} abgemeldet")
            logger.info(f"Benutzer abgemeldet: {user['BenutzerName']}")

            # Wenn keine aktiven Benutzer mehr, Start-Tab anzeigen
            if not self.active_sessions:
                self.notebook.select(self.start_frame)

        except Exception as e:
            logger.error(f"Logout-Fehler: {e}")

    def update_active_list(self):
        """Aktive Benutzerliste im Start-Tab aktualisieren"""
        self.active_listbox.delete(0, tk.END)

        for user_id, data in self.active_sessions.items():
            user = data['user']
            session = data['session']
            tab = data['tab']

            # Info zusammenstellen
            start_time = datetime.fromisoformat(str(session['StartTS']))
            duration = int((datetime.now() - start_time).total_seconds())

            active_marker = " ⚡" if tab.is_active else ""
            entry = f"{user['BenutzerName']}{active_marker} - {format_duration(duration)} - {tab.scan_count} Scans"
            self.active_listbox.insert(tk.END, entry)

        # Nächster Update
        self.root.after(1000, self.update_active_list)

    def update_user_count(self):
        """Benutzer-Zähler aktualisieren"""
        count = len(self.active_sessions)
        self.user_count_label.config(text=f"Aktive Benutzer: {count}")

    def show_status(self, text, error=False):
        """Status anzeigen"""
        self.status_label.config(text=text)
        if error:
            logger.error(text)
            # Nach 3 Sekunden zurücksetzen
            self.root.after(3000, lambda: self.status_label.config(
                text="Bereit - Halten Sie Ihren RFID-Tag an den Reader"
            ))

    def on_closing(self):
        """Beim Schließen aufräumen"""
        # Scanner stoppen
        if self.qr_scanner:
            self.qr_scanner.stop()

        # Alle Benutzer abmelden
        for user_id in list(self.active_sessions.keys()):
            self.logout_user(user_id)

        # RFID Listener stoppen
        self.hid_listener.stop()

        logger.info("Anwendung beendet")
        self.root.destroy()


def main():
    """Hauptfunktion"""
    root = tk.Tk()
    app = MainApplication(root)

    # Schließen-Handler
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Starten
    root.mainloop()


if __name__ == "__main__":
    main()