#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RFID & QR Scanner - Hauptanwendung
Minimale Tkinter GUI
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


class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("RFID & QR Scanner - Wareneingang")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # State
        self.active_sessions = {}  # {user_id: session_data}
        self.current_session_id = None

        # Hardware
        self.hid_listener = HIDListener(self.on_rfid_scan)
        self.qr_scanner = None
        self.scanning_qr = False

        # UI Setup
        self.setup_ui()

        # Timer für Session-Updates
        self.update_timer()

        # RFID Listener starten
        self.hid_listener.start()
        logger.info("Anwendung gestartet")

    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        # Hauptframe
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Grid-Konfiguration
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(header_frame, text="RFID & QR Scanner",
                  font=('Arial', 20, 'bold')).pack(side=tk.LEFT)

        self.status_label = ttk.Label(header_frame, text="Bereit",
                                      font=('Arial', 12))
        self.status_label.pack(side=tk.RIGHT, padx=20)

        # Linke Seite - Aktive Benutzer
        left_frame = ttk.LabelFrame(main_frame, text="Aktive Benutzer", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))

        # Treeview für Sessions
        columns = ('Name', 'Start', 'Dauer', 'Scans')
        self.session_tree = ttk.Treeview(left_frame, columns=columns, height=15)
        self.session_tree.heading('#0', text='ID')
        self.session_tree.heading('Name', text='Name')
        self.session_tree.heading('Start', text='Start')
        self.session_tree.heading('Dauer', text='Dauer')
        self.session_tree.heading('Scans', text='Scans')

        self.session_tree.column('#0', width=50)
        self.session_tree.column('Name', width=150)
        self.session_tree.column('Start', width=100)
        self.session_tree.column('Dauer', width=80)
        self.session_tree.column('Scans', width=60)

        self.session_tree.pack(fill=tk.BOTH, expand=True)

        # Session auswählen bei Klick
        self.session_tree.bind('<<TreeviewSelect>>', self.on_session_select)

        # Logout Button
        ttk.Button(left_frame, text="Logout",
                   command=self.logout_selected).pack(pady=(10, 0))

        # Rechte Seite - QR Scanner
        right_frame = ttk.LabelFrame(main_frame, text="QR-Code Scanner", padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))

        # Video Frame (Placeholder)
        self.video_frame = ttk.Frame(right_frame, relief=tk.SUNKEN)
        self.video_frame.pack(fill=tk.BOTH, expand=True)

        self.video_label = ttk.Label(self.video_frame,
                                     text="Kamera nicht aktiv\n\nKlicken Sie 'Scanner starten'",
                                     font=('Arial', 14), anchor=tk.CENTER)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Scanner Controls
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))

        self.scan_button = ttk.Button(control_frame, text="Scanner starten",
                                      command=self.toggle_qr_scanner)
        self.scan_button.pack(side=tk.LEFT, padx=(0, 10))

        # Letzter Scan
        self.last_scan_label = ttk.Label(control_frame, text="Letzter Scan: -")
        self.last_scan_label.pack(side=tk.LEFT)

        # Bottom - Info
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        self.info_label = ttk.Label(info_frame,
                                    text="Halten Sie Ihren RFID-Tag an den Reader zum Anmelden",
                                    font=('Arial', 11))
        self.info_label.pack()

    def on_rfid_scan(self, tag_id):
        """Callback für RFID-Scans"""
        logger.info(f"RFID Tag erkannt: {tag_id}")

        # Benutzer suchen
        user = User.get_by_epc(tag_id)
        if not user:
            self.show_error(f"Unbekannter Tag: {tag_id}")
            return

        user_id = user['ID']

        # Prüfe ob Benutzer bereits angemeldet
        if user_id in self.active_sessions:
            # Logout
            self.logout_user(user_id)
        else:
            # Login
            self.login_user(user)

    def login_user(self, user):
        """Benutzer anmelden"""
        try:
            # Session erstellen
            session = Session.create(user['ID'])
            if not session:
                self.show_error("Fehler beim Erstellen der Session")
                return

            # Zu aktiven Sessions hinzufügen
            self.active_sessions[user['ID']] = {
                'session': session,
                'user': user,
                'scan_count': 0,
                'tree_id': None
            }

            # UI aktualisieren
            self.update_session_list()
            self.set_status(f"✅ {user['BenutzerName']} angemeldet")
            logger.info(f"Benutzer angemeldet: {user['BenutzerName']}")

        except Exception as e:
            logger.error(f"Login-Fehler: {e}")
            self.show_error(f"Login fehlgeschlagen: {str(e)}")

    def logout_user(self, user_id):
        """Benutzer abmelden"""
        if user_id not in self.active_sessions:
            return

        try:
            session_data = self.active_sessions[user_id]
            session = session_data['session']
            user = session_data['user']

            # Session beenden
            Session.end(session['ID'])

            # Aus aktiven Sessions entfernen
            del self.active_sessions[user_id]

            # UI aktualisieren
            self.update_session_list()
            self.set_status(f"👋 {user['BenutzerName']} abgemeldet")
            logger.info(f"Benutzer abgemeldet: {user['BenutzerName']}")

            # Wenn das die aktuelle Session war
            if self.current_session_id == session['ID']:
                self.current_session_id = None

        except Exception as e:
            logger.error(f"Logout-Fehler: {e}")
            self.show_error(f"Logout fehlgeschlagen: {str(e)}")

    def logout_selected(self):
        """Ausgewählten Benutzer abmelden"""
        selection = self.session_tree.selection()
        if not selection:
            return

        # User ID aus Tree holen
        item = self.session_tree.item(selection[0])
        user_id = int(item['text'])

        self.logout_user(user_id)

    def on_session_select(self, event):
        """Session auswählen"""
        selection = self.session_tree.selection()
        if not selection:
            self.current_session_id = None
            return

        # Session ID aus Daten holen
        item = self.session_tree.item(selection[0])
        user_id = int(item['text'])

        if user_id in self.active_sessions:
            self.current_session_id = self.active_sessions[user_id]['session']['ID']
            logger.debug(f"Session ausgewählt: {self.current_session_id}")

    def toggle_qr_scanner(self):
        """QR Scanner ein/aus"""
        if self.scanning_qr:
            self.stop_qr_scanner()
        else:
            self.start_qr_scanner()

    def start_qr_scanner(self):
        """QR Scanner starten"""
        if not self.current_session_id:
            self.show_error("Bitte wählen Sie zuerst einen Benutzer aus")
            return

        try:
            self.qr_scanner = QRScanner(
                camera_index=APP_CONFIG.get('CAMERA_INDEX', 0),
                callback=self.on_qr_scan,
                video_label=self.video_label
            )
            self.qr_scanner.start()
            self.scanning_qr = True
            self.scan_button.config(text="Scanner stoppen")
            self.set_status("📸 QR-Scanner aktiv")

        except Exception as e:
            logger.error(f"QR-Scanner Fehler: {e}")
            self.show_error("Kamera konnte nicht gestartet werden")

    def stop_qr_scanner(self):
        """QR Scanner stoppen"""
        if self.qr_scanner:
            self.qr_scanner.stop()
            self.qr_scanner = None

        self.scanning_qr = False
        self.scan_button.config(text="Scanner starten")
        self.video_label.config(text="Kamera nicht aktiv\n\nKlicken Sie 'Scanner starten'")
        self.set_status("QR-Scanner gestoppt")

    def on_qr_scan(self, payload):
        """Callback für QR-Code Scans"""
        if not self.current_session_id:
            return

        try:
            # QR-Code speichern
            qr_scan = QrScan.create(self.current_session_id, payload)
            if qr_scan:
                # Scan-Count erhöhen
                for user_id, data in self.active_sessions.items():
                    if data['session']['ID'] == self.current_session_id:
                        data['scan_count'] += 1
                        break

                # UI aktualisieren
                self.update_session_list()
                self.last_scan_label.config(
                    text=f"Letzter Scan: {datetime.now().strftime('%H:%M:%S')} - {payload[:50]}..."
                )
                self.set_status(f"✅ QR-Code erfasst")
                logger.info(f"QR-Code gescannt: {payload[:100]}")

        except Exception as e:
            logger.error(f"QR-Scan Fehler: {e}")
            self.show_error("Fehler beim Speichern des QR-Codes")

    def update_session_list(self):
        """Session-Liste aktualisieren"""
        # Alte Einträge löschen
        for item in self.session_tree.get_children():
            self.session_tree.delete(item)

        # Neue Einträge
        for user_id, data in self.active_sessions.items():
            session = data['session']
            user = data['user']

            # Dauer berechnen
            start_time = datetime.fromisoformat(str(session['StartTS']))
            duration = int((datetime.now() - start_time).total_seconds())

            # Tree-Item hinzufügen
            tree_id = self.session_tree.insert('', 'end',
                                               text=str(user_id),
                                               values=(
                                                   user['BenutzerName'],
                                                   start_time.strftime('%H:%M'),
                                                   format_duration(duration),
                                                   data['scan_count']
                                               )
                                               )
            data['tree_id'] = tree_id

    def update_timer(self):
        """Timer für Session-Updates"""
        # Session-Zeiten aktualisieren
        for user_id, data in self.active_sessions.items():
            if data['tree_id']:
                session = data['session']
                start_time = datetime.fromisoformat(str(session['StartTS']))
                duration = int((datetime.now() - start_time).total_seconds())

                # Nur Dauer aktualisieren
                values = list(self.session_tree.item(data['tree_id'])['values'])
                values[2] = format_duration(duration)
                self.session_tree.item(data['tree_id'], values=values)

        # Nächster Timer
        self.root.after(1000, self.update_timer)

    def set_status(self, text):
        """Status-Text setzen"""
        self.status_label.config(text=text)
        self.info_label.config(text=text)

    def show_error(self, message):
        """Fehlermeldung anzeigen"""
        logger.error(message)
        self.set_status(f"❌ {message}")
        messagebox.showerror("Fehler", message)

    def on_closing(self):
        """Beim Schließen aufräumen"""
        # QR Scanner stoppen
        if self.qr_scanner:
            self.qr_scanner.stop()

        # RFID Listener stoppen
        self.hid_listener.stop()

        # Alle Sessions beenden
        for user_id in list(self.active_sessions.keys()):
            self.logout_user(user_id)

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