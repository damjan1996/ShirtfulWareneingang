#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RFID & QR Scanner - Paralleles Multi-User System
Alle Benutzer können parallel alle verfügbaren Scanner nutzen
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
logger = setup_logger('ParallelApp', APP_CONFIG.get('LOG_LEVEL', 'INFO'))


class ParallelMultiUserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Paralleles Multi-User QR Scanner System")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        # State
        self.active_sessions = {}  # {user_id: session_data}
        self.qr_assignment_mode = "round_robin"  # "round_robin", "manual", "last_rfid"
        self.last_rfid_user = None
        self.round_robin_index = 0
        self.total_scans_today = 0

        # Hardware
        self.hid_listener = HIDListener(self.on_rfid_scan)
        self.scanners = []  # Liste aller Scanner
        self.scanning_active = False

        # UI State
        self.pending_qr_assignment = None

        # UI Setup
        self.setup_ui()

        # Auto-start
        self.auto_start()

    def setup_ui(self):
        """Erstellt die Benutzeroberfläche für paralleles Scannen"""
        # Hauptcontainer
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        title_label = ttk.Label(header_frame, text="Paralleles Multi-User Scanner System",
                                font=('Arial', 18, 'bold'))
        title_label.pack(side=tk.LEFT)

        # Status und Einstellungen
        settings_frame = ttk.Frame(header_frame)
        settings_frame.pack(side=tk.RIGHT)

        ttk.Label(settings_frame, text="QR-Zuordnung:", font=('Arial', 10)).pack(side=tk.LEFT, padx=(0, 5))

        self.assignment_var = tk.StringVar(value=self.qr_assignment_mode)
        assignment_combo = ttk.Combobox(settings_frame, textvariable=self.assignment_var,
                                        values=["round_robin", "manual", "last_rfid"],
                                        state="readonly", width=12)
        assignment_combo.pack(side=tk.LEFT, padx=(0, 10))
        assignment_combo.bind('<<ComboboxSelected>>', self.on_assignment_mode_changed)

        self.status_label = ttk.Label(settings_frame, text="System bereit",
                                      font=('Arial', 11), foreground='green')
        self.status_label.pack(side=tk.LEFT)

        # Hauptbereich - 3 Spalten
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Linke Spalte - Aktive Benutzer (40%)
        left_frame = ttk.LabelFrame(content_frame, text="Aktive Benutzer", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Benutzer-Info
        info_frame = ttk.Frame(left_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.users_count_label = ttk.Label(info_frame, text="Angemeldete Benutzer: 0",
                                           font=('Arial', 12, 'bold'))
        self.users_count_label.pack(anchor=tk.W)

        self.next_assignment_label = ttk.Label(info_frame, text="Nächster QR-Code: -",
                                               font=('Arial', 11), foreground='blue')
        self.next_assignment_label.pack(anchor=tk.W)

        # Benutzerliste
        columns = ('Name', 'Start', 'Dauer', 'Scans', 'Letzter Scan', 'user_id')
        self.users_tree = ttk.Treeview(left_frame, columns=columns, height=15, show='headings',
                                       displaycolumns=('Name', 'Start', 'Dauer', 'Scans', 'Letzter Scan'))

        self.users_tree.heading('Name', text='Name')
        self.users_tree.heading('Start', text='Start')
        self.users_tree.heading('Dauer', text='Dauer')
        self.users_tree.heading('Scans', text='Scans')
        self.users_tree.heading('Letzter Scan', text='Letzter Scan')

        self.users_tree.column('Name', width=150)
        self.users_tree.column('Start', width=80)
        self.users_tree.column('Dauer', width=80)
        self.users_tree.column('Scans', width=60)
        self.users_tree.column('Letzter Scan', width=120)

        self.users_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Benutzer-Buttons
        user_buttons_frame = ttk.Frame(left_frame)
        user_buttons_frame.pack(fill=tk.X)

        ttk.Button(user_buttons_frame, text="Ausgewählten abmelden",
                   command=self.logout_selected).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(user_buttons_frame, text="Alle abmelden",
                   command=self.logout_all).pack(side=tk.LEFT)

        # Mittlere Spalte - Scanner Status (30%)
        middle_frame = ttk.LabelFrame(content_frame, text="Scanner Status", padding="10")
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Scanner-Info
        scanner_info_frame = ttk.Frame(middle_frame)
        scanner_info_frame.pack(fill=tk.X, pady=(0, 10))

        self.scanner_count_label = ttk.Label(scanner_info_frame, text="Verfügbare Scanner: 0",
                                             font=('Arial', 12, 'bold'))
        self.scanner_count_label.pack(anchor=tk.W)

        self.scanning_status_label = ttk.Label(scanner_info_frame, text="Scanner: Initialisierung...",
                                               font=('Arial', 11))
        self.scanning_status_label.pack(anchor=tk.W)

        # Scanner-Liste
        scanner_columns = ('Index', 'Status', 'Letzte Aktivität')
        self.scanner_tree = ttk.Treeview(middle_frame, columns=scanner_columns, height=8, show='headings')

        for col in scanner_columns:
            self.scanner_tree.heading(col, text=col)
            self.scanner_tree.column(col, width=100)

        self.scanner_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Scanner-Buttons
        scanner_buttons_frame = ttk.Frame(middle_frame)
        scanner_buttons_frame.pack(fill=tk.X)

        self.toggle_scanning_btn = ttk.Button(scanner_buttons_frame, text="Scanner starten",
                                              command=self.toggle_scanning)
        self.toggle_scanning_btn.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(scanner_buttons_frame, text="Scanner neu starten",
                   command=self.restart_scanners).pack(side=tk.LEFT)

        # Live Video Bereich
        video_frame = ttk.LabelFrame(middle_frame, text="Live Video", padding="5")
        video_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.video_label = ttk.Label(video_frame, text="Scanner wird gestartet...",
                                     font=('Arial', 12), anchor=tk.CENTER, relief=tk.SUNKEN)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Rechte Spalte - QR-Code Verwaltung (30%)
        right_frame = ttk.LabelFrame(content_frame, text="QR-Code Verwaltung", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # QR-Statistics
        stats_frame = ttk.Frame(right_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        self.total_scans_label = ttk.Label(stats_frame, text="Heutige Scans: 0",
                                           font=('Arial', 12, 'bold'))
        self.total_scans_label.pack(anchor=tk.W)

        self.scan_rate_label = ttk.Label(stats_frame, text="Scans/Min: 0.0",
                                         font=('Arial', 11))
        self.scan_rate_label.pack(anchor=tk.W)

        # Manual Assignment (nur wenn manual mode)
        self.manual_frame = ttk.LabelFrame(right_frame, text="Manuelle Zuordnung", padding="10")

        manual_info = ttk.Label(self.manual_frame, text="Bei QR-Scan Benutzer auswählen:",
                                font=('Arial', 10))
        manual_info.pack(anchor=tk.W, pady=(0, 5))

        self.quick_assign_frame = ttk.Frame(self.manual_frame)
        self.quick_assign_frame.pack(fill=tk.X)

        # Letzte Scans
        recent_frame = ttk.LabelFrame(right_frame, text="Letzte QR-Codes", padding="10")
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Recent scans liste
        recent_columns = ('Zeit', 'Benutzer', 'QR-Code')
        self.recent_tree = ttk.Treeview(recent_frame, columns=recent_columns, height=10, show='headings')

        for col in recent_columns:
            self.recent_tree.heading(col, text=col)

        self.recent_tree.column('Zeit', width=80)
        self.recent_tree.column('Benutzer', width=100)
        self.recent_tree.column('QR-Code', width=150)

        self.recent_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # QR Assignment Buttons (dynamisch erstellt)
        self.assignment_buttons_frame = ttk.Frame(right_frame)
        self.assignment_buttons_frame.pack(fill=tk.X)

        # Bottom Info
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(15, 0))

        self.info_label = ttk.Label(bottom_frame,
                                    text="💡 RFID scannen = Anmelden | Alle Benutzer können parallel alle Scanner nutzen",
                                    font=('Arial', 11), foreground='blue')
        self.info_label.pack()

    def auto_start(self):
        """Startet automatisch alle Komponenten"""
        # RFID Listener starten
        self.hid_listener.start()

        # Scanner verzögert starten
        threading.Thread(target=self._delayed_scanner_start, daemon=True).start()

        # Update Timer starten
        self.update_timer()

        logger.info("Paralleles Multi-User Scanner System gestartet")

    def _delayed_scanner_start(self):
        """Startet Scanner verzögert"""
        time.sleep(2)
        try:
            self.root.after(0, self.start_all_scanners)
        except:
            pass

    def start_all_scanners(self):
        """Startet alle verfügbaren Scanner"""
        try:
            # Versuche mehrere Kamera-Indizes
            camera_indices = APP_CONFIG.get('CAMERA_INDICES', [0, 1, 2])
            if not isinstance(camera_indices, list):
                camera_indices = [APP_CONFIG.get('CAMERA_INDEX', 0)]

            logger.info(f"Versuche Scanner für Kameras: {camera_indices}")

            for camera_index in camera_indices:
                try:
                    scanner = QRScanner(
                        camera_index=camera_index,
                        callback=self.on_qr_scan,
                        video_label=self.video_label if camera_index == camera_indices[0] else None
                    )
                    scanner.start()
                    self.scanners.append({
                        'scanner': scanner,
                        'index': camera_index,
                        'status': 'active',
                        'last_activity': datetime.now()
                    })
                    logger.info(f"Scanner {camera_index} erfolgreich gestartet")
                except Exception as e:
                    logger.warning(f"Scanner {camera_index} konnte nicht gestartet werden: {e}")

            if self.scanners:
                self.scanning_active = True
                self.toggle_scanning_btn.config(text="Scanner stoppen")
                self.scanning_status_label.config(text=f"Scanner: {len(self.scanners)} aktiv", foreground='green')
                logger.info(f"{len(self.scanners)} Scanner gestartet")
            else:
                self.scanning_status_label.config(text="Scanner: Keine verfügbar", foreground='red')
                logger.error("Keine Scanner verfügbar")

            self.update_scanner_list()

        except Exception as e:
            logger.error(f"Fehler beim Starten der Scanner: {e}")
            self.scanning_status_label.config(text="Scanner: Fehler beim Start", foreground='red')

    def toggle_scanning(self):
        """Scanner ein/aus schalten"""
        if self.scanning_active:
            self.stop_all_scanners()
        else:
            self.start_all_scanners()

    def stop_all_scanners(self):
        """Stoppt alle Scanner"""
        for scanner_info in self.scanners:
            try:
                scanner_info['scanner'].stop()
            except:
                pass

        self.scanners.clear()
        self.scanning_active = False
        self.toggle_scanning_btn.config(text="Scanner starten")
        self.scanning_status_label.config(text="Scanner: Gestoppt", foreground='red')
        self.video_label.config(text="Scanner gestoppt")
        self.update_scanner_list()
        logger.info("Alle Scanner gestoppt")

    def restart_scanners(self):
        """Startet alle Scanner neu"""
        self.stop_all_scanners()
        time.sleep(1)
        self.start_all_scanners()

    def update_scanner_list(self):
        """Aktualisiert die Scanner-Liste"""
        # Scanner-Liste leeren
        for item in self.scanner_tree.get_children():
            self.scanner_tree.delete(item)

        # Scanner hinzufügen
        for scanner_info in self.scanners:
            last_activity = scanner_info['last_activity'].strftime('%H:%M:%S')
            self.scanner_tree.insert('', 'end', values=(
                f"Kamera {scanner_info['index']}",
                scanner_info['status'],
                last_activity
            ))

        self.scanner_count_label.config(text=f"Verfügbare Scanner: {len(self.scanners)}")

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
            # Abmelden
            self.logout_user(user_id)
        else:
            # Anmelden
            self.login_user(user)

        # Merke letzten RFID Benutzer für last_rfid Modus
        self.last_rfid_user = user_id
        self.update_assignment_display()

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
                'start_time': datetime.now(),
                'last_scan_time': None
            }

            # UI aktualisieren
            self.update_users_list()
            self.update_assignment_buttons()
            self.update_assignment_display()

            self.show_message(f"✅ {user_name} angemeldet", "success")
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

            # UI aktualisieren
            self.update_users_list()
            self.update_assignment_buttons()
            self.update_assignment_display()

            self.show_message(f"👋 {user_name} abgemeldet", "info")
            logger.info(f"Benutzer abgemeldet: {user_name}")

        except Exception as e:
            logger.error(f"Logout Fehler: {e}")
            self.show_message(f"Abmeldung fehlgeschlagen: {e}", "error")

    def logout_all(self):
        """Alle Benutzer abmelden"""
        if not self.active_sessions:
            messagebox.showinfo("Info", "Keine Benutzer angemeldet")
            return

        if messagebox.askyesno("Bestätigung", "Alle Benutzer abmelden?"):
            for user_id in list(self.active_sessions.keys()):
                self.logout_user(user_id)

    def on_qr_scan(self, payload):
        """QR Code gescannt - automatische oder manuelle Zuordnung"""
        if not self.active_sessions:
            self.show_message("⚠️ Keine Benutzer angemeldet - RFID scannen", "warning")
            return

        # Update Scanner-Aktivität
        self.update_scanner_activity()

        # Assignment-Modus bestimmen
        assignment_mode = self.assignment_var.get()

        if assignment_mode == "manual":
            self.handle_manual_assignment(payload)
        else:
            self.handle_automatic_assignment(payload, assignment_mode)

    def handle_automatic_assignment(self, payload, mode):
        """Automatische QR-Code Zuordnung"""
        try:
            # Benutzer bestimmen
            target_user_id = None

            if mode == "round_robin":
                # Round-robin zwischen allen angemeldeten Benutzern
                user_ids = list(self.active_sessions.keys())
                if user_ids:
                    target_user_id = user_ids[self.round_robin_index % len(user_ids)]
                    self.round_robin_index += 1

            elif mode == "last_rfid":
                # Letzter RFID-Benutzer
                if self.last_rfid_user and self.last_rfid_user in self.active_sessions:
                    target_user_id = self.last_rfid_user
                else:
                    # Fallback auf ersten verfügbaren
                    target_user_id = next(iter(self.active_sessions.keys()), None)

            if target_user_id:
                self.assign_qr_to_user(payload, target_user_id)
            else:
                self.show_message("⚠️ Kein Benutzer für Zuordnung verfügbar", "warning")

        except Exception as e:
            logger.error(f"Automatische Zuordnung Fehler: {e}")
            self.show_message(f"QR Zuordnung fehlgeschlagen: {e}", "error")

    def handle_manual_assignment(self, payload):
        """Manuelle QR-Code Zuordnung"""
        self.pending_qr_assignment = payload
        self.show_message(f"🔄 QR-Code bereit - Benutzer auswählen", "info")
        self.update_assignment_buttons()

    def assign_qr_to_user(self, payload, user_id):
        """Ordnet QR-Code einem spezifischen Benutzer zu"""
        try:
            # Duplikat-Check
            from duplicate_prevention import check_qr_duplicate, register_qr_scan

            session_id = self.active_sessions[user_id]['session']['ID']
            duplicate_check = check_qr_duplicate(payload, None)  # Global check

            if duplicate_check['is_duplicate']:
                remaining = duplicate_check.get('remaining_seconds', 0)
                if remaining > 60:
                    time_str = f"{remaining // 60}m {remaining % 60}s"
                else:
                    time_str = f"{remaining}s"

                self.show_message(f"⚠️ Code bereits vor {time_str} gescannt", "warning")
                return False

            # QR Code speichern
            qr_scan = QrScan.create(session_id, payload)
            if not qr_scan:
                self.show_message("Fehler beim Speichern", "error")
                return False

            # Registrieren für Duplikat-Verhinderung
            register_qr_scan(payload, None)

            # Scan Count erhöhen
            self.active_sessions[user_id]['scan_count'] += 1
            self.active_sessions[user_id]['last_scan_time'] = datetime.now()
            self.total_scans_today += 1

            # UI aktualisieren
            self.update_users_list()
            self.add_to_recent_scans(payload, user_id)

            # Feedback
            user_name = self.active_sessions[user_id]['user']['BenutzerName']
            display_payload = payload[:40] + "..." if len(payload) > 40 else payload

            self.show_message(f"✅ Code für {user_name} gespeichert", "success")

            # Pending assignment löschen
            self.pending_qr_assignment = None
            self.update_assignment_buttons()

            logger.info(f"QR Code für {user_name} gespeichert")
            return True

        except Exception as e:
            logger.error(f"QR Assignment Fehler: {e}")
            self.show_message(f"QR Fehler: {e}", "error")
            return False

    def update_scanner_activity(self):
        """Aktualisiert Scanner-Aktivität"""
        for scanner_info in self.scanners:
            scanner_info['last_activity'] = datetime.now()
        self.update_scanner_list()

    def add_to_recent_scans(self, payload, user_id):
        """Fügt Scan zur Recent-Liste hinzu"""
        user_name = self.active_sessions[user_id]['user']['BenutzerName']
        timestamp = datetime.now().strftime('%H:%M:%S')
        display_payload = payload[:30] + "..." if len(payload) > 30 else payload

        # Am Anfang hinzufügen
        self.recent_tree.insert('', 0, values=(timestamp, user_name, display_payload))

        # Nur die letzten 20 behalten
        children = self.recent_tree.get_children()
        if len(children) > 20:
            for item in children[20:]:
                self.recent_tree.delete(item)

    def on_assignment_mode_changed(self, event=None):
        """Assignment-Modus wurde geändert"""
        self.qr_assignment_mode = self.assignment_var.get()
        self.update_assignment_display()
        self.update_assignment_buttons()

        if self.qr_assignment_mode == "manual":
            self.manual_frame.pack(fill=tk.X, pady=(10, 0))
        else:
            self.manual_frame.pack_forget()

        logger.info(f"QR-Zuordnungsmodus geändert: {self.qr_assignment_mode}")

    def update_assignment_display(self):
        """Aktualisiert die Anzeige für nächste Zuordnung"""
        mode = self.assignment_var.get()

        if mode == "round_robin":
            if self.active_sessions:
                user_ids = list(self.active_sessions.keys())
                next_user_id = user_ids[self.round_robin_index % len(user_ids)]
                next_user_name = self.active_sessions[next_user_id]['user']['BenutzerName']
                self.next_assignment_label.config(text=f"Nächster QR-Code: {next_user_name}")
            else:
                self.next_assignment_label.config(text="Nächster QR-Code: -")

        elif mode == "last_rfid":
            if self.last_rfid_user and self.last_rfid_user in self.active_sessions:
                user_name = self.active_sessions[self.last_rfid_user]['user']['BenutzerName']
                self.next_assignment_label.config(text=f"Nächster QR-Code: {user_name} (letzter RFID)")
            else:
                self.next_assignment_label.config(text="Nächster QR-Code: Ersten verfügbaren")

        elif mode == "manual":
            self.next_assignment_label.config(text="Nächster QR-Code: Manuelle Auswahl")

    def update_assignment_buttons(self):
        """Aktualisiert die manuellen Zuordnungs-Buttons"""
        # Alte Buttons entfernen
        for widget in self.assignment_buttons_frame.winfo_children():
            widget.destroy()

        if self.assignment_var.get() == "manual" and self.pending_qr_assignment:
            ttk.Label(self.assignment_buttons_frame, text="QR-Code zuordnen an:",
                      font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))

            for user_id, session_data in self.active_sessions.items():
                user_name = session_data['user']['BenutzerName']
                btn = ttk.Button(self.assignment_buttons_frame, text=user_name,
                                 command=lambda uid=user_id: self.manual_assign_to_user(uid))
                btn.pack(fill=tk.X, pady=1)

    def manual_assign_to_user(self, user_id):
        """Manuelle Zuordnung zu spezifischem Benutzer"""
        if self.pending_qr_assignment:
            self.assign_qr_to_user(self.pending_qr_assignment, user_id)

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
            last_scan = data['last_scan_time'].strftime('%H:%M:%S') if data['last_scan_time'] else '-'

            tree_id = self.users_tree.insert('', 'end', values=(
                user['BenutzerName'],
                start_time.strftime('%H:%M'),
                format_duration(duration),
                data['scan_count'],
                last_scan,
                str(user_id)  # user_id als letzte Spalte
            ))

            # Auswahl wiederherstellen
            if current_selection == str(user_id):
                self.users_tree.selection_set(tree_id)

        # Counter aktualisieren
        count = len(self.active_sessions)
        self.users_count_label.config(text=f"Angemeldete Benutzer: {count}")

    def update_timer(self):
        """Update Timer - läuft jede Sekunde"""
        # Benutzer-Zeiten aktualisieren
        for item in self.users_tree.get_children():
            try:
                values = self.users_tree.item(item)['values']
                user_id = int(values[5])  # user_id ist an Position 5

                if user_id in self.active_sessions:
                    data = self.active_sessions[user_id]
                    duration = int((datetime.now() - data['start_time']).total_seconds())
                    last_scan = data['last_scan_time'].strftime('%H:%M:%S') if data['last_scan_time'] else '-'

                    # Alle Werte aktualisieren
                    new_values = (
                        data['user']['BenutzerName'],
                        data['start_time'].strftime('%H:%M'),
                        format_duration(duration),
                        data['scan_count'],
                        last_scan,
                        str(user_id)
                    )
                    self.users_tree.item(item, values=new_values)
            except:
                continue

        # Statistiken aktualisieren
        total_scans = sum(data['scan_count'] for data in self.active_sessions.values())
        self.total_scans_label.config(text=f"Heutige Scans: {total_scans}")

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

        # Nach 5 Sekunden zurücksetzen
        self.root.after(5000, lambda: self.status_label.config(text="System bereit", foreground="green"))

    def on_closing(self):
        """Beim Schließen aufräumen"""
        # Scanner stoppen
        self.stop_all_scanners()

        # RFID Listener stoppen
        self.hid_listener.stop()

        # Alle Benutzer abmelden
        for user_id in list(self.active_sessions.keys()):
            self.logout_user(user_id)

        logger.info("Paralleles System beendet")
        self.root.destroy()


def main():
    """Hauptfunktion"""
    root = tk.Tk()
    app = ParallelMultiUserApp(root)

    # Schließen Handler
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # App starten
    root.mainloop()


if __name__ == "__main__":
    main()