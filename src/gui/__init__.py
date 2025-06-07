#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Package für die Wareneingang-Anwendung

Dieses Package enthält alle GUI-Komponenten:
- Hauptfenster und Navigation
- Login-Screen für RFID-Authentifizierung
- Scanner-Interface für QR-Codes
- Benutzer-Panels für Multi-User-Support
- Wiederverwendbare Widgets
- Zentrale Style-Definitionen
"""

from typing import TYPE_CHECKING

# Versionsinformation
__version__ = "1.0.0"
__author__ = "Shirtful GmbH"

# Lazy imports für bessere Performance
if TYPE_CHECKING:
    from .main_window import MainWindow
    from .login_screen import LoginScreen
    from .scanner_screen import ScannerScreen
    from .user_panel import UserPanel
    from .widgets import *
    from .styles import Styles, apply_theme

# Package-Level Imports
__all__ = [
    # Hauptkomponenten
    "MainWindow",
    "LoginScreen",
    "ScannerScreen",
    "UserPanel",

    # Widgets
    "BigButton",
    "StatusBar",
    "UserTab",
    "ScanResultList",
    "RFIDIndicator",
    "CameraView",
    "MessageDialog",

    # Styles
    "Styles",
    "apply_theme",
    "get_color",
    "get_font",

    # Utilities
    "center_window",
    "show_message",
    "show_error",
    "show_warning",
    "show_info",
    "confirm_dialog",
]

# ==============================================================================
# GUI Utilities
# ==============================================================================

import tkinter as tk
from tkinter import messagebox
import logging

logger = logging.getLogger(__name__)


def center_window(window: tk.Toplevel, width: int = None, height: int = None):
    """
    Zentriert ein Fenster auf dem Bildschirm

    Args:
        window: Das zu zentrierende Fenster
        width: Fensterbreite (optional)
        height: Fensterhöhe (optional)
    """
    window.update_idletasks()

    # Aktuelle Größe verwenden wenn nicht angegeben
    if width is None:
        width = window.winfo_width()
    if height is None:
        height = window.winfo_height()

    # Bildschirmgröße ermitteln
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Position berechnen
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    # Fenster positionieren
    window.geometry(f"{width}x{height}+{x}+{y}")


def show_message(parent: tk.Widget, title: str, message: str,
                 message_type: str = "info") -> bool:
    """
    Zeigt eine Nachricht an

    Args:
        parent: Eltern-Widget
        title: Titel der Nachricht
        message: Nachrichtentext
        message_type: Typ ("info", "warning", "error", "question")

    Returns:
        bool: True bei OK/Ja, False bei Nein/Abbruch
    """
    try:
        if message_type == "info":
            messagebox.showinfo(title, message, parent=parent)
            return True
        elif message_type == "warning":
            messagebox.showwarning(title, message, parent=parent)
            return True
        elif message_type == "error":
            messagebox.showerror(title, message, parent=parent)
            return True
        elif message_type == "question":
            result = messagebox.askyesno(title, message, parent=parent)
            return result
        else:
            logger.warning(f"Unbekannter Nachrichtentyp: {message_type}")
            messagebox.showinfo(title, message, parent=parent)
            return True
    except Exception as e:
        logger.error(f"Fehler beim Anzeigen der Nachricht: {e}")
        return False


def show_error(parent: tk.Widget, message: str, title: str = "Fehler"):
    """Zeigt eine Fehlermeldung"""
    show_message(parent, title, message, "error")


def show_warning(parent: tk.Widget, message: str, title: str = "Warnung"):
    """Zeigt eine Warnung"""
    show_message(parent, title, message, "warning")


def show_info(parent: tk.Widget, message: str, title: str = "Information"):
    """Zeigt eine Information"""
    show_message(parent, title, message, "info")


def confirm_dialog(parent: tk.Widget, message: str,
                   title: str = "Bestätigung") -> bool:
    """
    Zeigt einen Bestätigungsdialog

    Returns:
        bool: True bei Ja, False bei Nein
    """
    return show_message(parent, title, message, "question")


# ==============================================================================
# Style Utilities
# ==============================================================================

def get_color(color_name: str) -> str:
    """
    Holt eine Farbe aus den Style-Definitionen

    Args:
        color_name: Name der Farbe

    Returns:
        str: Hex-Farbcode
    """
    from .styles import Styles
    return Styles.COLORS.get(color_name, "#000000")


def get_font(font_type: str = "normal", size: str = "medium") -> tuple:
    """
    Holt eine Schriftart-Definition

    Args:
        font_type: Typ ("normal", "bold", "title")
        size: Größe ("small", "medium", "large", "xlarge")

    Returns:
        tuple: (Familie, Größe, Stil)
    """
    from .styles import Styles
    return Styles.get_font(font_type, size)


# ==============================================================================
# Window Management
# ==============================================================================

_main_window = None


def get_main_window():
    """Gibt die Hauptfenster-Instanz zurück"""
    global _main_window
    return _main_window


def set_main_window(window):
    """Setzt die Hauptfenster-Instanz"""
    global _main_window
    _main_window = window


# ==============================================================================
# Initialisierung
# ==============================================================================

def initialize_gui():
    """
    Initialisiert das GUI-System
    Wird beim Start der Anwendung aufgerufen
    """
    logger.info("GUI-System wird initialisiert...")

    # Tkinter-Einstellungen
    try:
        import tkinter
        root = tkinter.Tk()
        root.withdraw()  # Verstecken für Tests

        # DPI-Awareness für Windows
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        # Tkinter-Version prüfen
        tk_version = root.tk.eval('info patchlevel')
        logger.info(f"Tkinter Version: {tk_version}")

        root.destroy()

    except Exception as e:
        logger.error(f"Fehler bei GUI-Initialisierung: {e}")
        raise


# ==============================================================================
# Event System
# ==============================================================================

class GUIEventManager:
    """Verwaltet GUI-Events zwischen Komponenten"""

    def __init__(self):
        self._listeners = {}

    def subscribe(self, event_name: str, callback):
        """Registriert einen Event-Listener"""
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback):
        """Entfernt einen Event-Listener"""
        if event_name in self._listeners:
            self._listeners[event_name].remove(callback)

    def emit(self, event_name: str, *args, **kwargs):
        """Löst ein Event aus"""
        if event_name in self._listeners:
            for callback in self._listeners[event_name]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Fehler in Event-Handler {event_name}: {e}")


# Globale Event-Manager-Instanz
event_manager = GUIEventManager()


# Events definieren
class Events:
    """GUI-Event-Konstanten"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    SCAN_COMPLETE = "scan_complete"
    RFID_DETECTED = "rfid_detected"
    SESSION_TIMEOUT = "session_timeout"
    TAB_CHANGED = "tab_changed"
    ERROR_OCCURRED = "error_occurred"