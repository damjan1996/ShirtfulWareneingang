#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RFID & QR Scanner - Vereinfachte Multi-User Anwendung
Mehrere Benutzer scannen parallel über das gleiche Gerät
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
logger = setup_logger('SimpleApp', APP_CONFIG.get('LOG_LEVEL', 'INFO'))


class SimpleMultiUserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-User QR Scanner - Vereinfacht")
        self.root.geometry("1000x700")
        self.root.minsize(800, 500)

        # State
        self.active_sessions = {}  # {user_id: session_data}
        self.current_user_id = None  # Wer bekommt aktuell QR-Codes
        self.total_scans_today = 0

        # Hardware
        self.hid_listener = HIDListener(self.on_rfid_scan)
        self.qr_scanner = None
        self.scanner_running = False

        # UI Setup
        self.setup_ui()

        # Auto-start
        self.auto_start()

    def setup_ui(self):
        """Erstellt die vereinfachte Benutzeroberfläche"""
        # Hauptcontainer
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = ttk.Label(header_frame, text="Multi-User QR Scanner",
                                font=('Arial', 20, 'bold'))
        title_label.pack(side=tk.LEFT)

        self.status_label = ttk.Label(header_frame, text="Bereit",
                                      font=('Arial', 12), foreground='green')
        self.status_label.pack(side=tk.RIGHT)

        # Hauptbereich - 2 Spalten
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Linke Spalte - Aktive Benutzer
        left_frame = ttk.LabelFrame(content_frame, text="Aktive Benutzer", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Aktueller Benutzer
        current_frame = ttk.Frame(left_frame)
        current_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(current_frame, text="Nächster QR-Code geht an:",
                  font=('Arial', 11)).pack(anchor=tk.W)

        self.current_user_label = ttk.Label(current_frame, text="Niemand - RFID berühren",
                                            font=('Arial', 14, 'bold'), foreground='red')
        self.current_user_label.pack(anchor=tk.W)

        # Benutzerliste
        columns = ('Status', 'Name', 'Start', 'Dauer', 'Scans', 'user_id')
        self.users_tree = ttk.Treeview(left_frame, columns=columns, height=12, show='headings',
                                       displaycolumns=('Status', 'Name', 'Start', 'Dauer', 'Scans'))

        self.users_tree.heading('Status', text='Status')
        self.users_tree.heading('Name', text='Name')
        self.users_tree.heading('Start', text='Start')
        self.users_tree.heading('Dauer', text='Dauer')
        self.users_tree.heading('Scans', text='Scans')

        self.users_tree.column('Status', width=60)
        self.users_tree.column('Name', width=150)
        self.users_tree.column('Start', width=80)
        self.users_tree.column('Dauer', width=80)
        self.users_tree.column('Scans', width=60)

        self.users_tree.pack(fill=tk.BOTH, expand=True)

        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Abmelden",
                   command=self.logout_selected).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="Ich bin dran!",
                   command=self.set_selected_active).pack(side=tk.LEFT)

        # Rechte Spalte - Scanner
        right_frame = ttk.LabelFrame(content_frame, text="QR Scanner", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Scanner Status
        scanner_status_frame = ttk.Frame(right_frame)
        scanner_status_frame.pack(fill=tk.X, pady=(0, 10))

        self.scanner_status_label = ttk.Label(scanner_status_frame, text="Scanner: Startet...",
                                              font=('Arial', 11), foreground='orange')
        self.scanner_status_label.pack(anchor=tk.W)

        # Video Bereich
        self.video_frame = ttk.Frame(right_frame, relief=tk.SUNKEN, borderwidth=2)
        self.video_frame.pack(fill=tk.BOTH, expand=True)

        self.video_label = ttk.Label(self.video_frame, text="Scanner wird gestartet...",
                                     font=('Arial', 12), anchor=tk.CENTER)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Scanner Control
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))

        self.scan_button = ttk.Button(control_frame, text="Scanner startet...",
                                      command=self.toggle_scanner, state='disabled')
        self.scan_button.pack(side=tk.LEFT)

        # Scan Info
        self.scan_info_label = ttk.Label(control_frame, text="Heute: 0 Scans",
                                         font=('Arial', 11))
        self.scan_info_label.pack(side=tk.RIGHT)

        # Letzter Scan
        self.last_scan_label = ttk.Label(right_frame, text="Letzter Scan: -",
                                         font=('Arial', 10))
        self.last_scan_label.pack(pady=(5, 0))

        # Bottom Info
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(15, 0))

        self.info_label = ttk.Label(info_frame,
                                    text="💡 RFID berühren = Anmelden + Du bist dran | Alle arbeiten parallel",
                                    font=('Arial', 11), foreground='blue')
        self.info_label.pack()

    def auto_start(self):
        """Startet automatisch Scanner und RFID Listener"""
        # RFID Listener starten
        self.hid_listener.start()

        # QR Scanner nach kurzer Verzögerung starten
        threading.Thread(target=self._delayed_scanner_start, daemon=True).start()

        # Update Timer starten
        self.update_timer()

        logger.info("Vereinfachte Multi-User App gestartet")

    def _delayed_scanner_start(self):
        """Startet QR Scanner verzögert"""
        time.sleep(2)
        try:
            self.root.after(0, self._start_scanner)
        except:
            pass

    def _start_scanner(self):
        """Startet den QR Scanner"""
        try:
            self.qr_scanner = QRScanner(
                camera_index=APP_CONFIG.get('CAMERA_INDEX', 0),
                callback=self.on_qr_scan,
                video_label=self.video_label
            )
            self.qr_scanner.start()
            self.scanner_running = True

            self.scan_button.config(text="Scanner stoppen", state='normal')
            self.scanner_status_label.config(text="Scanner: Aktiv", foreground='green')

            logger.info("QR Scanner gestartet")

        except Exception as e:
            logger.error(f"Scanner Start Fehler: {e}")
            self.scanner_status_label.config(text="Scanner: Fehler", foreground='red')
            self.scan_button.config(text="Scanner starten", state='normal')

    def toggle_scanner(self):
        """Scanner ein/aus schalten"""
        if self.scanner_running:
            self.stop_scanner()
        else:
            self._start_scanner()

    def stop_scanner(self):
        """Scanner stoppen"""
        if self.qr_scanner:
            self.qr_scanner.stop()
            self.qr_scanner = None

        self.scanner_running = False
        self.scan_button.config(text="Scanner starten")
        self.scanner_status_label.config(text="Scanner: Gestoppt", foreground='red')
        self.video_label.config(text="Scanner gestoppt")

    def on_rfid_scan(self, tag_id):
        """RFID Tag gescannt"""
        logger.info(f"RFID: {tag_id}")

        # Benutzer suchen
        user = User.get_by_epc(tag_id)
        if not user:
            self.show_message(f"Unbekannter Tag: {tag_id}", "error")
            return

        user_id = user['ID']
        user_name = user['BenutzerName']

        # Bereits angemeldet?
        if user_id in self.active_sessions:
            # Setze als aktiven Benutzer
            self.current_user_id = user_id
            self.update_current_user_display()
            self.show_message(f"⚡ {user_name} ist jetzt dran", "success")
            logger.info(f"{user_name} als aktiver Benutzer gesetzt")
        else:
            # Neue Anmeldung
            self.login_user(user)

    def login_user(self, user):
        """Benutzer anmelden"""
        try:
            # Session erstellen
            session = Session.create(user['ID'])
            if not session:
                self.show_message("Session konnte nicht erstellt werden", "error")
                return

            user_id = user['ID']
            user_name = user['BenutzerName']

            # Session hinzufügen
            self.active_sessions[user_id] = {
                'session': session,
                'user': user,
                'scan_count': 0,
                'start_time': datetime.now()
            }

            # Als aktiven Benutzer setzen
            self.current_user_id = user_id

            # UI aktualisieren
            self.update_users_list()
            self.update_current_user_display()
            self.update_scan_counter()

            self.show_message(f"✅ {user_name} angemeldet + ist dran", "success")
            logger.info(f"Benutzer angemeldet: {user_name}")

        except Exception as e:
            logger.error(f"Login Fehler: {e}")
            self.show_message(f"Anmeldung fehlgeschlagen: {e}", "error")

    def logout_selected(self):
        """Ausgewählten Benutzer abmelden"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte Benutzer auswählen")
            return

        # User ID aus den Values holen
        item = self.users_tree.item(selection[0])
        values = item['values']
        user_id = int(values[5])  # user_id ist an Position 5
        self.logout_user(user_id)

    def logout_user(self, user_id):
        """Benutzer abmelden"""
        if user_id not in self.active_sessions:
            return

        try:
            session_data = self.active_sessions[user_id]
            session = session_data['session']
            user_name = session_data['user']['BenutzerName']

            # Session beenden
            Session.end(session['ID'])

            # Duplikat-Cache leeren
            try:
                from duplicate_prevention import clear_session_duplicates
                clear_session_duplicates(session['ID'])
            except:
                pass

            # Aus aktiven Sessions entfernen
            del self.active_sessions[user_id]

            # Neuen aktiven Benutzer bestimmen
            if self.current_user_id == user_id:
                if self.active_sessions:
                    # Ersten verfügbaren Benutzer als aktiv setzen
                    self.current_user_id = next(iter(self.active_sessions.keys()))
                else:
                    self.current_user_id = None

            # UI aktualisieren
            self.update_users_list()
            self.update_current_user_display()
            self.update_scan_counter()

            self.show_message(f"👋 {user_name} abgemeldet", "info")
            logger.info(f"Benutzer abgemeldet: {user_name}")

        except Exception as e:
            logger.error(f"Logout Fehler: {e}")
            self.show_message(f"Abmeldung fehlgeschlagen: {e}", "error")

    def set_selected_active(self):
        """Ausgewählten Benutzer als aktiv setzen"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte Benutzer auswählen")
            return

        try:
            # User ID aus den Values holen
            item = self.users_tree.item(selection[0])
            values = item['values']
            user_id = int(values[5])  # user_id ist an Position 5

            if user_id in self.active_sessions:
                self.current_user_id = user_id
                self.update_users_list()
                self.update_current_user_display()

                user_name = self.active_sessions[user_id]['user']['BenutzerName']
                self.show_message(f"⚡ {user_name} ist jetzt dran", "success")

        except Exception as e:
            logger.error(f"Aktivierung Fehler: {e}")

    def on_qr_scan(self, payload):
        """QR Code gescannt"""
        if not self.current_user_id or self.current_user_id not in self.active_sessions:
            self.show_message("⚠️ Niemand aktiv - RFID berühren", "warning")
            return

        try:
            # Duplikat-Check
            from duplicate_prevention import check_qr_duplicate, register_qr_scan

            session_id = self.active_sessions[self.current_user_id]['session']['ID']
            duplicate_check = check_qr_duplicate(payload, None)  # Global check

            if duplicate_check['is_duplicate']:
                remaining = duplicate_check.get('remaining_seconds', 0)
                if remaining > 60:
                    time_str = f"{remaining // 60}m {remaining % 60}s"
                else:
                    time_str = f"{remaining}s"

                self.show_message(f"⚠️ Code bereits vor {time_str} gescannt", "warning")
                self.last_scan_label.config(text=f"Duplikat: {datetime.now().strftime('%H:%M:%S')}",
                                            foreground='red')
                return

            # QR Code speichern
            qr_scan = QrScan.create(session_id, payload)
            if not qr_scan:
                self.show_message("Fehler beim Speichern", "error")
                return

            # Registrieren für Duplikat-Verhinderung
            register_qr_scan(payload, None)

            # Scan Count erhöhen
            self.active_sessions[self.current_user_id]['scan_count'] += 1
            self.total_scans_today += 1

            # UI aktualisieren
            self.update_users_list()
            self.update_scan_counter()

            # Feedback
            user_name = self.active_sessions[self.current_user_id]['user']['BenutzerName']
            display_payload = payload[:40] + "..." if len(payload) > 40 else payload

            self.show_message(f"✅ Code für {user_name} gespeichert", "success")
            self.last_scan_label.config(text=f"Gespeichert: {datetime.now().strftime('%H:%M:%S')} - {display_payload}",
                                        foreground='green')

            # Farbe nach 3 Sekunden zurücksetzen
            self.root.after(3000, lambda: self.last_scan_label.config(foreground='black'))

            logger.info(f"QR Code für {user_name} gespeichert")

        except Exception as e:
            logger.error(f"QR Scan Fehler: {e}")
            self.show_message(f"QR Fehler: {e}", "error")

    def update_users_list(self):
        """Benutzerliste aktualisieren"""
        # Auswahl merken
        current_selection = None
        try:
            selection = self.users_tree.selection()
            if selection:
                values = self.users_tree.item(selection[0])['values']
                current_selection = values[5]  # user_id ist an Position 5
        except:
            pass

        # Liste leeren
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)

        # Benutzer hinzufügen
        for user_id, data in self.active_sessions.items():
            user = data['user']
            start_time = data['start_time']
            duration = int((datetime.now() - start_time).total_seconds())

            # Status anzeigen
            status = "⚡ Aktiv" if user_id == self.current_user_id else "○ Bereit"

            tree_id = self.users_tree.insert('', 'end',
                                             values=(
                                                 status,
                                                 user['BenutzerName'],
                                                 start_time.strftime('%H:%M'),
                                                 format_duration(duration),
                                                 data['scan_count'],
                                                 str(user_id)  # user_id als letzte Spalte
                                             ))

            # Auswahl wiederherstellen
            if current_selection == str(user_id):
                self.users_tree.selection_set(tree_id)

    def update_current_user_display(self):
        """Aktueller Benutzer Anzeige aktualisieren"""
        if self.current_user_id and self.current_user_id in self.active_sessions:
            user_name = self.active_sessions[self.current_user_id]['user']['BenutzerName']
            self.current_user_label.config(text=f"⚡ {user_name}", foreground='green')
        else:
            self.current_user_label.config(text="Niemand - RFID berühren", foreground='red')

    def update_scan_counter(self):
        """Scan Counter aktualisieren"""
        total = sum(data['scan_count'] for data in self.active_sessions.values())
        self.scan_info_label.config(text=f"Heute: {total} Scans")

    def update_timer(self):
        """Update Timer - läuft jede Sekunde"""
        # Zeiten in der Liste aktualisieren
        for item in self.users_tree.get_children():
            try:
                values = self.users_tree.item(item)['values']
                user_id = int(values[5])  # user_id ist an Position 5

                if user_id in self.active_sessions:
                    data = self.active_sessions[user_id]
                    duration = int((datetime.now() - data['start_time']).total_seconds())

                    # Status Symbol
                    status = "⚡ Aktiv" if user_id == self.current_user_id else "○ Bereit"

                    # Alle Werte aktualisieren
                    new_values = (
                        status,
                        data['user']['BenutzerName'],
                        data['start_time'].strftime('%H:%M'),
                        format_duration(duration),
                        data['scan_count'],
                        str(user_id)
                    )
                    self.users_tree.item(item, values=new_values)
            except:
                continue

        # Nächster Timer
        self.root.after(1000, self.update_timer)

    def show_message(self, text, msg_type="info"):
        """Status Nachricht anzeigen"""
        colors = {
            "info": "blue",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }

        self.status_label.config(text=text, foreground=colors.get(msg_type, "black"))
        self.info_label.config(text=text, foreground=colors.get(msg_type, "blue"))

    def on_closing(self):
        """Beim Schließen aufräumen"""
        # Scanner stoppen
        if self.qr_scanner:
            self.qr_scanner.stop()

        # RFID Listener stoppen
        self.hid_listener.stop()

        # Alle Benutzer abmelden
        for user_id in list(self.active_sessions.keys()):
            self.logout_user(user_id)

        logger.info("App beendet")
        self.root.destroy()


def main():
    """Hauptfunktion"""
    root = tk.Tk()
    app = SimpleMultiUserApp(root)

    # Schließen Handler
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # App starten
    root.mainloop()


if __name__ == "__main__":
    main()