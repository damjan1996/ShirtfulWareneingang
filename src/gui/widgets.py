#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wiederverwendbare GUI-Widgets für die Wareneingang-Anwendung
Enthält spezielle Widgets für Touch-Interface und Scanner-Funktionen
"""

import tkinter as tk
from tkinter import ttk, Canvas
import math
import time
from typing import Optional, Callable, List, Dict, Any, Tuple
from datetime import datetime
from PIL import Image, ImageDraw, ImageTk
import threading

from config.constants import Colors, ButtonSizes
from .styles import Styles


# ==============================================================================
# BigButton - Touch-freundlicher Button
# ==============================================================================

class BigButton(tk.Button):
    """
    Großer, touch-freundlicher Button mit Hover-Effekten
    """

    def __init__(self, parent, text: str = "", command: Callable = None,
                 bg_color: str = None, hover_color: str = None,
                 text_color: str = "white", disabled_color: str = None,
                 height: int = ButtonSizes.HEIGHT_LARGE,
                 width: int = None, font_size: int = 20, **kwargs):
        """
        Initialisiert den BigButton

        Args:
            parent: Eltern-Widget
            text: Button-Text
            command: Callback-Funktion
            bg_color: Hintergrundfarbe
            hover_color: Hover-Farbe
            text_color: Textfarbe
            disabled_color: Farbe im deaktivierten Zustand
            height: Button-Höhe in Pixeln
            width: Button-Breite (optional)
            font_size: Schriftgröße
            **kwargs: Weitere Button-Argumente
        """
        # Standard-Farben
        self.bg_color = bg_color or Styles.COLORS["primary"]
        self.hover_color = hover_color or Styles.COLORS["primary_dark"]
        self.text_color = text_color
        self.disabled_color = disabled_color or Styles.COLORS["disabled"]
        self.original_bg = self.bg_color

        # Button erstellen
        super().__init__(
            parent,
            text=text,
            command=command,
            font=("Arial", font_size, "bold"),
            bg=self.bg_color,
            fg=self.text_color,
            activebackground=self.hover_color,
            activeforeground=self.text_color,
            relief=tk.FLAT,
            cursor="hand2",
            borderwidth=0,
            highlightthickness=0,
            padx=30,
            pady=15,
            **kwargs
        )

        # Größe setzen
        if width:
            self.configure(width=width)
        if height:
            self.configure(height=int(height / 20))  # Ungefähre Umrechnung

        # Event-Bindings für Hover-Effekt
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, event):
        """Mouse-Enter Event"""
        if self["state"] != tk.DISABLED:
            self.configure(bg=self.hover_color)

    def _on_leave(self, event):
        """Mouse-Leave Event"""
        if self["state"] != tk.DISABLED:
            self.configure(bg=self.original_bg)

    def _on_press(self, event):
        """Button-Press Event"""
        if self["state"] != tk.DISABLED:
            self.configure(relief=tk.SUNKEN)

    def _on_release(self, event):
        """Button-Release Event"""
        if self["state"] != tk.DISABLED:
            self.configure(relief=tk.FLAT)

    def configure(self, **kwargs):
        """Überschriebene configure-Methode für Farbverwaltung"""
        if "bg" in kwargs or "background" in kwargs:
            self.original_bg = kwargs.get("bg", kwargs.get("background", self.original_bg))

        if "bg_color" in kwargs:
            self.bg_color = kwargs.pop("bg_color")
            self.original_bg = self.bg_color
            kwargs["bg"] = self.bg_color

        if "state" in kwargs and kwargs["state"] == tk.DISABLED:
            kwargs["bg"] = self.disabled_color
            kwargs["cursor"] = "arrow"
        elif "state" in kwargs and kwargs["state"] == tk.NORMAL:
            kwargs["bg"] = self.original_bg
            kwargs["cursor"] = "hand2"

        super().configure(**kwargs)


# ==============================================================================
# RFIDIndicator - Animierter RFID-Status-Indikator
# ==============================================================================

class RFIDIndicator(tk.Frame):
    """
    Animierter Indikator für RFID-Scan-Status
    Zeigt verschiedene Zustände mit Animationen
    """

    def __init__(self, parent, size: int = 150, **kwargs):
        """
        Initialisiert den RFID-Indikator

        Args:
            parent: Eltern-Widget
            size: Größe des Indikators in Pixeln
            **kwargs: Weitere Frame-Argumente
        """
        super().__init__(parent, **kwargs)

        self.size = size
        self.state = "idle"  # idle, scanning, processing, success, error, warning
        self.animation_angle = 0
        self.animation_running = False

        # Canvas für Animation
        self.canvas = Canvas(
            self,
            width=size,
            height=size,
            highlightthickness=0,
            bg=kwargs.get("bg", Styles.COLORS["background"])
        )
        self.canvas.pack()

        # RFID-Icon in der Mitte
        self._draw_rfid_icon()

        # Animation starten
        self._animate()

    def _draw_rfid_icon(self):
        """Zeichnet das RFID-Icon"""
        cx, cy = self.size // 2, self.size // 2

        # Icon-Text (RFID-Symbol)
        self.icon_text = self.canvas.create_text(
            cx, cy,
            text="📡",
            font=("Arial", int(self.size * 0.3)),
            fill=Styles.COLORS["text_secondary"]
        )

    def _draw_circle(self, radius: int, color: str, width: int = 3,
                     start_angle: int = 0, extent: int = 360):
        """Zeichnet einen Kreis oder Kreisbogen"""
        cx, cy = self.size // 2, self.size // 2

        return self.canvas.create_arc(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            start=start_angle,
            extent=extent,
            outline=color,
            width=width,
            style="arc"
        )

    def set_scanning(self, scanning: bool = True):
        """Setzt den Scanning-Status"""
        self.state = "scanning" if scanning else "idle"
        self.animation_running = scanning
        self._update_display()

    def set_processing(self):
        """Setzt den Processing-Status"""
        self.state = "processing"
        self.animation_running = True
        self._update_display()

    def set_success(self):
        """Setzt den Success-Status"""
        self.state = "success"
        self.animation_running = False
        self._update_display()

        # Nach 2 Sekunden zurücksetzen
        self.after(2000, self.reset)

    def set_error(self):
        """Setzt den Error-Status"""
        self.state = "error"
        self.animation_running = False
        self._update_display()

        # Nach 3 Sekunden zurücksetzen
        self.after(3000, self.reset)

    def set_warning(self):
        """Setzt den Warning-Status"""
        self.state = "warning"
        self.animation_running = False
        self._update_display()

        # Nach 2 Sekunden zurücksetzen
        self.after(2000, self.reset)

    def reset(self):
        """Setzt den Indikator zurück"""
        self.state = "idle"
        self.animation_running = False
        self._update_display()

    def _update_display(self):
        """Aktualisiert die Anzeige basierend auf dem Status"""
        # Alle Kreise löschen
        self.canvas.delete("circle")

        # Farben basierend auf Status
        colors = {
            "idle": Styles.COLORS["text_secondary"],
            "scanning": Styles.COLORS["info"],
            "processing": Styles.COLORS["warning"],
            "success": Styles.COLORS["success"],
            "error": Styles.COLORS["error"],
            "warning": Styles.COLORS["warning"]
        }

        color = colors.get(self.state, Styles.COLORS["text_secondary"])

        # Icon-Farbe ändern
        self.canvas.itemconfig(self.icon_text, fill=color)

        # Status-spezifische Kreise
        if self.state == "scanning":
            # Animierte Scan-Wellen
            for i in range(3):
                radius = int(self.size * 0.3) + i * 15
                self._draw_circle(radius, color, 2, tags="circle")

        elif self.state == "processing":
            # Rotierender Kreis
            self._draw_circle(
                int(self.size * 0.4), color, 4,
                self.animation_angle, 270, tags="circle"
            )

        elif self.state in ["success", "error", "warning"]:
            # Statischer Kreis
            self._draw_circle(int(self.size * 0.4), color, 4, tags="circle")

    def _animate(self):
        """Animation-Loop"""
        if self.animation_running:
            if self.state == "scanning":
                # Wellen-Animation
                self.animation_angle = (self.animation_angle + 5) % 360

            elif self.state == "processing":
                # Rotation
                self.animation_angle = (self.animation_angle + 10) % 360

            self._update_display()

        # Nächster Frame
        self.after(50, self._animate)


# ==============================================================================
# CameraView - Kamera-Vorschau Widget
# ==============================================================================

class CameraView(tk.Frame):
    """
    Widget zur Anzeige der Kamera-Vorschau
    """

    def __init__(self, parent, width: int = 640, height: int = 480, **kwargs):
        """
        Initialisiert die Kamera-Ansicht

        Args:
            parent: Eltern-Widget
            width: Breite in Pixeln
            height: Höhe in Pixeln
            **kwargs: Weitere Frame-Argumente
        """
        super().__init__(parent, **kwargs)

        self.width = width
        self.height = height
        self.current_image = None

        # Canvas für Bild
        self.canvas = Canvas(
            self,
            width=width,
            height=height,
            highlightthickness=0,
            bg=kwargs.get("bg", "#000000")
        )
        self.canvas.pack()

        # Platzhalter-Text
        self.placeholder_text = self.canvas.create_text(
            width // 2, height // 2,
            text="Kamera nicht aktiv",
            font=("Arial", 24),
            fill="#666666"
        )

        # Bild-Element
        self.image_id = None

    def update_image(self, photo_image: ImageTk.PhotoImage):
        """
        Aktualisiert das angezeigte Bild

        Args:
            photo_image: PhotoImage-Objekt
        """
        # Altes Bild entfernen
        if self.image_id:
            self.canvas.delete(self.image_id)

        # Platzhalter entfernen
        if self.placeholder_text:
            self.canvas.delete(self.placeholder_text)
            self.placeholder_text = None

        # Neues Bild anzeigen
        self.current_image = photo_image
        self.image_id = self.canvas.create_image(
            0, 0,
            anchor=tk.NW,
            image=photo_image
        )

    def clear(self):
        """Löscht die Anzeige"""
        if self.image_id:
            self.canvas.delete(self.image_id)
            self.image_id = None

        self.current_image = None

        # Platzhalter wieder anzeigen
        if not self.placeholder_text:
            self.placeholder_text = self.canvas.create_text(
                self.width // 2, self.height // 2,
                text="Kamera nicht aktiv",
                font=("Arial", 24),
                fill="#666666"
            )

    def draw_overlay(self, overlays: List[Dict[str, Any]]):
        """
        Zeichnet Overlays (z.B. erkannte QR-Codes)

        Args:
            overlays: Liste von Overlay-Definitionen
        """
        # Alle Overlays löschen
        self.canvas.delete("overlay")

        for overlay in overlays:
            if overlay["type"] == "rectangle":
                self.canvas.create_rectangle(
                    overlay["x1"], overlay["y1"],
                    overlay["x2"], overlay["y2"],
                    outline=overlay.get("color", "#00FF00"),
                    width=overlay.get("width", 2),
                    tags="overlay"
                )
            elif overlay["type"] == "text":
                self.canvas.create_text(
                    overlay["x"], overlay["y"],
                    text=overlay["text"],
                    font=overlay.get("font", ("Arial", 12)),
                    fill=overlay.get("color", "#00FF00"),
                    anchor=overlay.get("anchor", tk.NW),
                    tags="overlay"
                )


# ==============================================================================
# StatusBar - Statusleiste mit mehreren Bereichen
# ==============================================================================

class StatusBar(tk.Frame):
    """
    Mehrteilige Statusleiste
    """

    def __init__(self, parent, **kwargs):
        """
        Initialisiert die Statusleiste

        Args:
            parent: Eltern-Widget
            **kwargs: Weitere Frame-Argumente
        """
        kwargs.setdefault("relief", tk.SUNKEN)
        kwargs.setdefault("borderwidth", 1)
        kwargs.setdefault("height", 25)
        super().__init__(parent, **kwargs)

        self.pack_propagate(False)

        # Hauptstatus links
        self.status_label = tk.Label(
            self,
            text="Bereit",
            anchor=tk.W,
            font=("Arial", 10),
            padx=5
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Zusätzliche Bereiche
        self.sections = {}

    def set_status(self, text: str, status_type: str = "info"):
        """
        Setzt den Hauptstatus

        Args:
            text: Statustext
            status_type: Typ ("info", "success", "warning", "error")
        """
        color_map = {
            "info": Styles.COLORS["text_secondary"],
            "success": Styles.COLORS["success"],
            "warning": Styles.COLORS["warning"],
            "error": Styles.COLORS["error"]
        }

        self.status_label.configure(
            text=text,
            fg=color_map.get(status_type, Styles.COLORS["text_secondary"])
        )

    def add_section(self, name: str, text: str = "", width: int = None):
        """
        Fügt einen Bereich hinzu

        Args:
            name: Name des Bereichs
            text: Anzuzeigender Text
            width: Breite des Bereichs
        """
        # Separator
        separator = tk.Frame(self, width=2, bg=Styles.COLORS["border"])
        separator.pack(side=tk.RIGHT, fill=tk.Y, padx=2)

        # Label
        label = tk.Label(
            self,
            text=text,
            anchor=tk.W,
            font=("Arial", 10),
            padx=5
        )

        if width:
            label.configure(width=width)

        label.pack(side=tk.RIGHT)

        self.sections[name] = {
            "label": label,
            "separator": separator
        }

    def update_section(self, name: str, text: str):
        """Aktualisiert einen Bereich"""
        if name in self.sections:
            self.sections[name]["label"].configure(text=text)

    def remove_section(self, name: str):
        """Entfernt einen Bereich"""
        if name in self.sections:
            self.sections[name]["label"].destroy()
            self.sections[name]["separator"].destroy()
            del self.sections[name]


# ==============================================================================
# ScanResultList - Liste für Scan-Ergebnisse
# ==============================================================================

class ScanResultList(tk.Frame):
    """
    Scrollbare Liste für Scan-Ergebnisse
    """

    def __init__(self, parent, height: int = 10,
                 on_select: Callable = None, **kwargs):
        """
        Initialisiert die Scan-Liste

        Args:
            parent: Eltern-Widget
            height: Anzahl sichtbarer Zeilen
            on_select: Callback bei Auswahl
            **kwargs: Weitere Frame-Argumente
        """
        super().__init__(parent, **kwargs)

        self.on_select = on_select
        self.scans = []
        self.selected_index = None

        # Scrollbar
        scrollbar = ttk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox
        self.listbox = tk.Listbox(
            self,
            height=height,
            font=("Arial", 11),
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set,
            activestyle="none",
            bg=Styles.COLORS["surface"],
            fg=Styles.COLORS["text_primary"],
            selectbackground=Styles.COLORS["selection"],
            selectforeground=Styles.COLORS["text_primary"],
            borderwidth=0,
            highlightthickness=0
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.configure(command=self.listbox.yview)

        # Events
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Double-Button-1>", self._on_double_click)

    def add_scan(self, scan_data: Dict[str, Any]):
        """
        Fügt einen Scan zur Liste hinzu

        Args:
            scan_data: Scan-Daten
        """
        # Daten speichern
        self.scans.append(scan_data)

        # Formatieren
        timestamp = scan_data.get("timestamp", datetime.now())
        paket_nr = scan_data.get("paketnummer", "N/A")
        status_icon = "✅" if scan_data.get("status") == "success" else "❌"

        display_text = f"{status_icon} {timestamp.strftime('%H:%M:%S')} - {paket_nr}"

        # Zur Listbox hinzufügen
        self.listbox.insert(0, display_text)  # Neueste oben

        # Farbe setzen
        if scan_data.get("status") != "success":
            self.listbox.itemconfig(0, fg=Styles.COLORS["error"])

        # Zur neuesten springen
        self.listbox.see(0)

    def get_selected(self) -> Optional[Dict[str, Any]]:
        """Gibt die ausgewählten Scan-Daten zurück"""
        if self.selected_index is not None:
            # Index umkehren (neueste oben)
            data_index = len(self.scans) - 1 - self.selected_index
            if 0 <= data_index < len(self.scans):
                return self.scans[data_index]
        return None

    def get_last_scan(self) -> Optional[Dict[str, Any]]:
        """Gibt den letzten Scan zurück"""
        return self.scans[-1] if self.scans else None

    def remove_last(self):
        """Entfernt den letzten Scan"""
        if self.scans:
            self.scans.pop()
            self.listbox.delete(0)

    def clear(self):
        """Löscht alle Einträge"""
        self.scans.clear()
        self.listbox.delete(0, tk.END)
        self.selected_index = None

    def _on_select(self, event):
        """Wird bei Auswahl aufgerufen"""
        selection = self.listbox.curselection()
        if selection:
            self.selected_index = selection[0]

            if self.on_select:
                scan_data = self.get_selected()
                if scan_data:
                    self.on_select(scan_data)

    def _on_double_click(self, event):
        """Wird bei Doppelklick aufgerufen"""
        self._on_select(event)


# ==============================================================================
# UserTab - Tab für Multi-User Interface
# ==============================================================================

class UserTab(tk.Frame):
    """
    Tab-Widget für einen Benutzer
    """

    def __init__(self, parent, user_name: str,
                 on_close: Callable = None, **kwargs):
        """
        Initialisiert den User-Tab

        Args:
            parent: Eltern-Widget
            user_name: Benutzername
            on_close: Callback beim Schließen
            **kwargs: Weitere Frame-Argumente
        """
        super().__init__(parent, **kwargs)

        self.user_name = user_name
        self.on_close = on_close

        # Tab-Header
        self.header = tk.Frame(self, bg=Styles.COLORS["primary"], height=40)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)

        # Benutzername
        self.name_label = tk.Label(
            self.header,
            text=user_name,
            font=("Arial", 14, "bold"),
            fg="white",
            bg=Styles.COLORS["primary"]
        )
        self.name_label.pack(side=tk.LEFT, padx=10)

        # Close-Button
        if on_close:
            self.close_button = tk.Button(
                self.header,
                text="✕",
                font=("Arial", 12),
                fg="white",
                bg=Styles.COLORS["primary"],
                activebackground=Styles.COLORS["primary_dark"],
                activeforeground="white",
                relief=tk.FLAT,
                cursor="hand2",
                command=on_close
            )
            self.close_button.pack(side=tk.RIGHT, padx=5)

        # Content-Bereich
        self.content = tk.Frame(self, bg=Styles.COLORS["background"])
        self.content.pack(fill=tk.BOTH, expand=True)

    def set_active(self, active: bool = True):
        """Setzt den aktiven Status"""
        if active:
            self.header.configure(bg=Styles.COLORS["primary"])
            self.name_label.configure(bg=Styles.COLORS["primary"])
            if hasattr(self, "close_button"):
                self.close_button.configure(bg=Styles.COLORS["primary"])
        else:
            self.header.configure(bg=Styles.COLORS["surface"])
            self.name_label.configure(bg=Styles.COLORS["surface"], fg=Styles.COLORS["text_primary"])
            if hasattr(self, "close_button"):
                self.close_button.configure(bg=Styles.COLORS["surface"], fg=Styles.COLORS["text_primary"])


# ==============================================================================
# MessageDialog - Benutzerdefinierte Nachrichten-Dialoge
# ==============================================================================

class MessageDialog(tk.Toplevel):
    """
    Benutzerdefinierter Nachrichten-Dialog
    """

    def __init__(self, parent, title: str = "Nachricht",
                 message: str = "", message_type: str = "info",
                 buttons: List[str] = None, **kwargs):
        """
        Initialisiert den Dialog

        Args:
            parent: Eltern-Widget
            title: Dialog-Titel
            message: Nachrichtentext
            message_type: Typ ("info", "warning", "error", "question")
            buttons: Liste der Button-Texte
            **kwargs: Weitere Toplevel-Argumente
        """
        super().__init__(parent, **kwargs)

        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.result = None

        # Standard-Buttons
        if buttons is None:
            if message_type == "question":
                buttons = ["Ja", "Nein"]
            else:
                buttons = ["OK"]

        # Icon basierend auf Typ
        icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "question": "❓"
        }

        # Hauptframe
        main_frame = tk.Frame(self, bg=Styles.COLORS["background"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Icon und Nachricht
        msg_frame = tk.Frame(main_frame, bg=Styles.COLORS["background"])
        msg_frame.pack(fill=tk.BOTH, expand=True)

        # Icon
        icon_label = tk.Label(
            msg_frame,
            text=icons.get(message_type, "ℹ️"),
            font=("Arial", 48),
            bg=Styles.COLORS["background"]
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 20))

        # Nachricht
        msg_label = tk.Label(
            msg_frame,
            text=message,
            font=("Arial", 14),
            bg=Styles.COLORS["background"],
            fg=Styles.COLORS["text_primary"],
            wraplength=400,
            justify=tk.LEFT
        )
        msg_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Button-Frame
        button_frame = tk.Frame(main_frame, bg=Styles.COLORS["background"])
        button_frame.pack(fill=tk.X, pady=(20, 0))

        # Buttons erstellen
        for i, button_text in enumerate(buttons):
            btn = BigButton(
                button_frame,
                text=button_text,
                command=lambda idx=i: self._on_button_click(idx),
                bg_color=Styles.COLORS["primary"] if i == 0 else Styles.COLORS["surface"],
                text_color="white" if i == 0 else Styles.COLORS["text_primary"],
                height=50,
                font_size=14
            )
            btn.pack(side=tk.RIGHT, padx=(10, 0) if i > 0 else 0)

        # Dialog zentrieren
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # ESC zum Schließen
        self.bind("<Escape>", lambda e: self._on_button_click(-1))

    def _on_button_click(self, index: int):
        """Button-Click Handler"""
        self.result = index
        self.destroy()

    def show(self) -> int:
        """Zeigt den Dialog und wartet auf Antwort"""
        self.wait_window()
        return self.result if self.result is not None else -1


# ==============================================================================
# ProgressDialog - Fortschritts-Dialog
# ==============================================================================

class ProgressDialog(tk.Toplevel):
    """
    Dialog mit Fortschrittsanzeige
    """

    def __init__(self, parent, title: str = "Bitte warten...",
                 message: str = "Vorgang wird ausgeführt...",
                 show_cancel: bool = False, **kwargs):
        """
        Initialisiert den Fortschritts-Dialog

        Args:
            parent: Eltern-Widget
            title: Dialog-Titel
            message: Nachrichtentext
            show_cancel: Abbrechen-Button anzeigen
            **kwargs: Weitere Toplevel-Argumente
        """
        super().__init__(parent, **kwargs)

        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.cancelled = False

        # Hauptframe
        main_frame = tk.Frame(self, bg=Styles.COLORS["background"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Nachricht
        self.message_label = tk.Label(
            main_frame,
            text=message,
            font=("Arial", 14),
            bg=Styles.COLORS["background"],
            fg=Styles.COLORS["text_primary"]
        )
        self.message_label.pack(pady=(0, 20))

        # Fortschrittsbalken
        self.progress = ttk.Progressbar(
            main_frame,
            length=300,
            mode="indeterminate"
        )
        self.progress.pack(pady=10)
        self.progress.start(10)

        # Prozent-Anzeige
        self.percent_label = tk.Label(
            main_frame,
            text="",
            font=("Arial", 12),
            bg=Styles.COLORS["background"],
            fg=Styles.COLORS["text_secondary"]
        )
        self.percent_label.pack()

        # Abbrechen-Button
        if show_cancel:
            self.cancel_button = BigButton(
                main_frame,
                text="Abbrechen",
                command=self._on_cancel,
                bg_color=Styles.COLORS["surface"],
                text_color=Styles.COLORS["text_primary"],
                height=40,
                font_size=12
            )
            self.cancel_button.pack(pady=(20, 0))

        # Dialog zentrieren
        self.update_idletasks()
        width = 400
        height = 200 if show_cancel else 150
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Schließen verhindern
        self.protocol("WM_DELETE_WINDOW", lambda: None)

    def _on_cancel(self):
        """Abbrechen-Handler"""
        self.cancelled = True

    def update_progress(self, value: int = None, message: str = None):
        """
        Aktualisiert den Fortschritt

        Args:
            value: Fortschritt in Prozent (0-100), None für unbestimmt
            message: Neue Nachricht
        """
        if message:
            self.message_label.configure(text=message)

        if value is not None:
            # Bestimmter Modus
            self.progress.configure(mode="determinate", value=value)
            self.percent_label.configure(text=f"{value}%")
        else:
            # Unbestimmter Modus
            self.progress.configure(mode="indeterminate")
            self.progress.start(10)
            self.percent_label.configure(text="")

    def close(self):
        """Schließt den Dialog"""
        self.progress.stop()
        self.destroy()