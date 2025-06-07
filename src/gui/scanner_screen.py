#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner-Screen für QR-Code-Scanning
Zeigt Kamera-Feed und verarbeitet gescannte QR-Codes
"""

import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import logging
import threading
import queue
import time
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from config.constants import (
    Colors, ScannerMessages,
    QR_SCAN_INTERVAL, QR_DETECTION_COOLDOWN,
    CAMERA_RESOLUTION
)
from config.settings import CAMERA_SETTINGS, SCANNER_SETTINGS, AUDIO_SETTINGS
from src.scanner.qr_scanner import QRScanner
from src.scanner.camera_handler import CameraHandler
from src.utils.audio_player import AudioPlayer
from .styles import Styles
from .widgets import BigButton, CameraView
from . import event_manager, Events

logger = logging.getLogger(__name__)


class ScannerScreen(tk.Frame):
    """
    QR-Code Scanner Interface
    Zeigt Kamera-Vorschau und verarbeitet QR-Codes
    """

    def __init__(self, parent, on_scan_complete: Callable = None, **kwargs):
        """
        Initialisiert den Scanner-Screen

        Args:
            parent: Eltern-Widget
            on_scan_complete: Callback bei erfolgreichem Scan
            **kwargs: Weitere Tkinter-Argumente
        """
        super().__init__(parent, **kwargs)

        # Callbacks
        self.on_scan_complete = on_scan_complete

        # Services
        self.camera_handler = CameraHandler()
        self.qr_scanner = QRScanner()
        self.audio_player = AudioPlayer()

        # Status
        self.is_scanning = False
        self.camera_active = False
        self.last_scan_time = 0
        self.scan_queue = queue.Queue()
        self.camera_thread = None

        # UI erstellen
        self._create_ui()

        # Style anwenden
        self.configure(bg=Styles.COLORS["background"])

        # Kamera automatisch starten
        self.after(500, self.start_camera)

    def _create_ui(self):
        """Erstellt die Benutzeroberfläche"""

        # Hauptlayout: Links Kamera, Rechts Infos
        main_frame = tk.Frame(self, bg=Styles.COLORS["background"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Linke Seite: Kamera
        camera_frame = tk.Frame(main_frame, bg=Styles.COLORS["background"])
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._create_camera_section(camera_frame)

        # Trennlinie
        separator = tk.Frame(
            main_frame,
            bg=Styles.COLORS["border"],
            width=2
        )
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=20)

        # Rechte Seite: Scan-Info
        info_frame = tk.Frame(
            main_frame,
            bg=Styles.COLORS["background"],
            width=400
        )
        info_frame.pack(side=tk.LEFT, fill=tk.Y)
        info_frame.pack_propagate(False)

        self._create_info_section(info_frame)

    def _create_camera_section(self, parent):
        """Erstellt den Kamera-Bereich"""

        # Titel
        title_label = tk.Label(
            parent,
            text="QR-Code Scanner",
            font=Styles.get_font("bold", "large"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["background"]
        )
        title_label.pack(pady=(0, 10))

        # Kamera-View
        self.camera_view = CameraView(
            parent,
            width=640,
            height=480,
            bg=Styles.COLORS["surface"]
        )
        self.camera_view.pack()

        # Status-Label
        self.camera_status_label = tk.Label(
            parent,
            text=ScannerMessages.READY,
            font=Styles.get_font("normal", "medium"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["background"]
        )
        self.camera_status_label.pack(pady=10)

        # Kamera-Kontrollen
        controls_frame = tk.Frame(parent, bg=Styles.COLORS["background"])
        controls_frame.pack(pady=10)

        # Start/Stop Button
        self.camera_button = BigButton(
            controls_frame,
            text="📷 Kamera starten",
            command=self.toggle_camera,
            bg_color=Styles.COLORS["primary"],
            hover_color=Styles.COLORS["primary_dark"],
            height=50,
            font_size=16
        )
        self.camera_button.pack(side=tk.LEFT, padx=5)

        # Kamera-Auswahl
        self.camera_combo = ttk.Combobox(
            controls_frame,
            state="readonly",
            width=20,
            font=Styles.get_font("normal", "medium")
        )
        self.camera_combo.pack(side=tk.LEFT, padx=5)
        self._refresh_camera_list()
        self.camera_combo.bind("<<ComboboxSelected>>", self._on_camera_changed)

    def _create_info_section(self, parent):
        """Erstellt den Info-Bereich"""

        # Titel
        title_label = tk.Label(
            parent,
            text="Scan-Informationen",
            font=Styles.get_font("bold", "large"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["background"]
        )
        title_label.pack(pady=(0, 20))

        # Letzter Scan
        self.last_scan_frame = tk.LabelFrame(
            parent,
            text="Letzter Scan",
            font=Styles.get_font("bold", "medium"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["background"],
            relief=tk.GROOVE,
            borderwidth=2
        )
        self.last_scan_frame.pack(fill=tk.X, pady=10)

        # Scan-Details
        self.scan_details_frame = tk.Frame(
            self.last_scan_frame,
            bg=Styles.COLORS["surface"]
        )
        self.scan_details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Platzhalter für Scan-Details
        self.no_scan_label = tk.Label(
            self.scan_details_frame,
            text="Noch kein Scan durchgeführt",
            font=Styles.get_font("normal", "medium"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["surface"]
        )
        self.no_scan_label.pack(pady=20)

        # Statistik
        self.stats_frame = tk.LabelFrame(
            parent,
            text="Statistik",
            font=Styles.get_font("bold", "medium"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["background"],
            relief=tk.GROOVE,
            borderwidth=2
        )
        self.stats_frame.pack(fill=tk.X, pady=10)

        stats_content = tk.Frame(self.stats_frame, bg=Styles.COLORS["surface"])
        stats_content.pack(fill=tk.X, padx=10, pady=10)

        # Scan-Zähler
        self.scan_count_label = tk.Label(
            stats_content,
            text="Scans heute: 0",
            font=Styles.get_font("normal", "medium"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["surface"]
        )
        self.scan_count_label.pack(anchor=tk.W, pady=2)

        self.success_count_label = tk.Label(
            stats_content,
            text="Erfolgreich: 0",
            font=Styles.get_font("normal", "medium"),
            fg=Styles.COLORS["success"],
            bg=Styles.COLORS["surface"]
        )
        self.success_count_label.pack(anchor=tk.W, pady=2)

        self.error_count_label = tk.Label(
            stats_content,
            text="Fehler: 0",
            font=Styles.get_font("normal", "medium"),
            fg=Styles.COLORS["error"],
            bg=Styles.COLORS["surface"]
        )
        self.error_count_label.pack(anchor=tk.W, pady=2)

        # Hilfe
        help_frame = tk.Frame(parent, bg=Styles.COLORS["background"])
        help_frame.pack(fill=tk.X, pady=20)

        help_text = """So scannen Sie QR-Codes:
1. Kamera aktivieren
2. QR-Code vor die Kamera halten
3. Automatische Erkennung abwarten
4. Ton bestätigt erfolgreichen Scan"""

        help_label = tk.Label(
            help_frame,
            text=help_text,
            font=Styles.get_font("normal", "small"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["background"],
            justify=tk.LEFT
        )
        help_label.pack()

    def _refresh_camera_list(self):
        """Aktualisiert die Liste verfügbarer Kameras"""
        cameras = self.camera_handler.get_available_cameras()

        self.camera_combo['values'] = [f"Kamera {i}" for i in cameras]

        if cameras:
            # Standard-Kamera auswählen
            default_index = CAMERA_SETTINGS.get("default_index", 0)
            if default_index in cameras:
                self.camera_combo.current(cameras.index(default_index))
            else:
                self.camera_combo.current(0)
        else:
            self.camera_combo['values'] = ["Keine Kamera gefunden"]
            self.camera_button.configure(state=tk.DISABLED)

    def _on_camera_changed(self, event):
        """Wird aufgerufen wenn eine andere Kamera ausgewählt wird"""
        if self.camera_active:
            # Kamera neu starten mit neuer Auswahl
            self.stop_camera()
            self.after(100, self.start_camera)

    def toggle_camera(self):
        """Schaltet die Kamera ein/aus"""
        if self.camera_active:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        """Startet die Kamera"""
        if self.camera_active:
            return

        # Kamera-Index ermitteln
        selection = self.camera_combo.current()
        if selection < 0:
            logger.error("Keine Kamera ausgewählt")
            return

        camera_index = int(self.camera_combo.get().split(" ")[1])

        logger.info(f"Starte Kamera {camera_index}")

        # Kamera öffnen
        if not self.camera_handler.open_camera(camera_index):
            self.camera_status_label.configure(
                text=ScannerMessages.ERROR_CAMERA,
                fg=Styles.COLORS["error"]
            )
            return

        self.camera_active = True
        self.is_scanning = True

        # UI aktualisieren
        self.camera_button.configure(
            text="⏹ Kamera stoppen",
            bg_color=Styles.COLORS["secondary"]
        )
        self.camera_status_label.configure(
            text=ScannerMessages.SCANNING,
            fg=Styles.COLORS["info"]
        )

        # Kamera-Thread starten
        self.camera_thread = threading.Thread(
            target=self._camera_loop,
            daemon=True
        )
        self.camera_thread.start()

    def stop_camera(self):
        """Stoppt die Kamera"""
        if not self.camera_active:
            return

        logger.info("Stoppe Kamera")

        self.camera_active = False
        self.is_scanning = False

        # Auf Thread warten
        if self.camera_thread:
            self.camera_thread.join(timeout=2.0)

        # Kamera schließen
        self.camera_handler.release()

        # UI zurücksetzen
        self.camera_button.configure(
            text="📷 Kamera starten",
            bg_color=Styles.COLORS["primary"]
        )
        self.camera_status_label.configure(
            text=ScannerMessages.READY,
            fg=Styles.COLORS["text_secondary"]
        )
        self.camera_view.clear()

    def _camera_loop(self):
        """Kamera-Loop in separatem Thread"""
        frame_count = 0

        while self.camera_active:
            try:
                # Frame lesen
                frame = self.camera_handler.read_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue

                # Frame anzeigen
                self.after(0, self._update_camera_view, frame)

                # QR-Code scannen (nicht bei jedem Frame)
                if self.is_scanning and frame_count % 3 == 0:
                    current_time = time.time()

                    # Cooldown prüfen
                    if current_time - self.last_scan_time > QR_DETECTION_COOLDOWN / 1000:
                        # Nach QR-Codes suchen
                        qr_codes = self.qr_scanner.scan_frame(frame)

                        if qr_codes:
                            # Ersten QR-Code verarbeiten
                            self._process_qr_code(qr_codes[0])
                            self.last_scan_time = current_time

                frame_count += 1

                # Frame-Rate begrenzen
                time.sleep(1.0 / CAMERA_SETTINGS["fps"])

            except Exception as e:
                logger.error(f"Fehler in Kamera-Loop: {e}")
                time.sleep(0.1)

    def _update_camera_view(self, frame):
        """Aktualisiert die Kamera-Ansicht"""
        try:
            # Frame in RGB konvertieren
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # In PIL Image konvertieren
            image = Image.fromarray(frame_rgb)

            # An Widget-Größe anpassen
            image = image.resize(
                (self.camera_view.width, self.camera_view.height),
                Image.Resampling.LANCZOS
            )

            # In PhotoImage konvertieren
            photo = ImageTk.PhotoImage(image)

            # Anzeigen
            self.camera_view.update_image(photo)

        except Exception as e:
            logger.error(f"Fehler beim Update der Kamera-Ansicht: {e}")

    def _process_qr_code(self, qr_data: Dict[str, Any]):
        """Verarbeitet einen erkannten QR-Code"""
        logger.info(f"QR-Code erkannt: {qr_data}")

        # Audio-Feedback
        if AUDIO_SETTINGS["enabled"]:
            self.audio_player.play_sound("scan_success")

        # UI-Update im Haupt-Thread
        self.after(0, self._update_scan_info, qr_data)

        # Callback aufrufen
        if self.on_scan_complete:
            self.after(0, lambda: self.on_scan_complete(qr_data))

        # Event auslösen
        event_manager.emit(Events.SCAN_COMPLETE, qr_data)

    def _update_scan_info(self, qr_data: Dict[str, Any]):
        """Aktualisiert die Scan-Informationen"""
        # Platzhalter entfernen
        if self.no_scan_label.winfo_exists():
            self.no_scan_label.destroy()

        # Alte Details entfernen
        for widget in self.scan_details_frame.winfo_children():
            if widget != self.no_scan_label:
                widget.destroy()

        # Neue Details anzeigen
        details = [
            ("Zeitstempel:", datetime.now().strftime("%H:%M:%S")),
            ("Auftragsnummer:", qr_data.get("auftrags_nr", "N/A")),
            ("Paketnummer:", qr_data.get("paket_nr", "N/A")),
            ("Kunde:", qr_data.get("kunden_name", "N/A")),
        ]

        for label, value in details:
            row_frame = tk.Frame(
                self.scan_details_frame,
                bg=Styles.COLORS["surface"]
            )
            row_frame.pack(fill=tk.X, pady=2)

            label_widget = tk.Label(
                row_frame,
                text=label,
                font=Styles.get_font("bold", "small"),
                fg=Styles.COLORS["text_secondary"],
                bg=Styles.COLORS["surface"],
                width=15,
                anchor=tk.W
            )
            label_widget.pack(side=tk.LEFT)

            value_widget = tk.Label(
                row_frame,
                text=value,
                font=Styles.get_font("normal", "small"),
                fg=Styles.COLORS["text_primary"],
                bg=Styles.COLORS["surface"],
                anchor=tk.W
            )
            value_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Raw-Daten (gekürzt)
        raw_data = qr_data.get("raw_data", "")
        if len(raw_data) > 50:
            raw_data = raw_data[:50] + "..."

        raw_frame = tk.Frame(
            self.scan_details_frame,
            bg=Styles.COLORS["surface"]
        )
        raw_frame.pack(fill=tk.X, pady=(10, 0))

        raw_label = tk.Label(
            raw_frame,
            text="Rohdaten:",
            font=Styles.get_font("bold", "small"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["surface"]
        )
        raw_label.pack(anchor=tk.W)

        raw_text = tk.Text(
            raw_frame,
            height=3,
            font=Styles.get_font("normal", "small"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["background"],
            wrap=tk.WORD
        )
        raw_text.pack(fill=tk.X, pady=5)
        raw_text.insert("1.0", raw_data)
        raw_text.configure(state=tk.DISABLED)

    def update_statistics(self, total: int, success: int, error: int):
        """Aktualisiert die Statistik-Anzeige"""
        self.scan_count_label.configure(text=f"Scans heute: {total}")
        self.success_count_label.configure(text=f"Erfolgreich: {success}")
        self.error_count_label.configure(text=f"Fehler: {error}")

    def cleanup(self):
        """Aufräumen beim Beenden"""
        logger.info("Scanner-Screen wird aufgeräumt")

        # Kamera stoppen
        self.stop_camera()

        # Scanner schließen
        if self.qr_scanner:
            self.qr_scanner.close()