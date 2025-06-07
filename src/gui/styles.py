#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale Style-Definitionen für die GUI
Definiert Farben, Schriftarten und Theme-Einstellungen
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Tuple, Optional

from config.constants import Colors, Fonts
from config.settings import GUI_SETTINGS

logger = logging.getLogger(__name__)


class Styles:
    """Zentrale Style-Definitionen"""

    # ==========================================================================
    # Farben
    # ==========================================================================

    COLORS = {
        # Primary Colors
        "primary": Colors.PRIMARY,
        "primary_dark": Colors.PRIMARY_DARK,
        "primary_light": Colors.PRIMARY_LIGHT,

        # Secondary Colors
        "secondary": Colors.SECONDARY,
        "secondary_dark": Colors.SECONDARY_DARK,
        "secondary_light": Colors.SECONDARY_LIGHT,

        # Status Colors
        "success": Colors.SUCCESS,
        "error": Colors.ERROR,
        "warning": Colors.WARNING,
        "info": Colors.INFO,

        # Neutral Colors
        "background": Colors.BACKGROUND,
        "surface": Colors.SURFACE,
        "text_primary": Colors.TEXT_PRIMARY,
        "text_secondary": Colors.TEXT_SECONDARY,
        "text_disabled": Colors.TEXT_DISABLED,
        "border": Colors.BORDER,

        # Dark Mode Colors
        "dark_background": Colors.DARK_BACKGROUND,
        "dark_surface": Colors.DARK_SURFACE,
        "dark_text": Colors.DARK_TEXT,

        # Special Colors
        "hover": "#E3F2FD",  # Light blue hover
        "pressed": "#BBDEFB",  # Pressed state
        "disabled": "#F5F5F5",  # Disabled background
        "focus": "#2196F3",  # Focus border
        "selection": "#B3E5FC",  # Text selection
    }

    # ==========================================================================
    # Schriftarten
    # ==========================================================================

    FONTS = {
        "family": Fonts.FAMILY,
        "sizes": {
            "small": Fonts.SIZE_SMALL,
            "normal": Fonts.SIZE_NORMAL,
            "medium": Fonts.SIZE_MEDIUM,
            "large": Fonts.SIZE_LARGE,
            "xlarge": Fonts.SIZE_XLARGE,
            "xxlarge": Fonts.SIZE_XXLARGE,
            "title": Fonts.SIZE_TITLE,
        }
    }

    # ==========================================================================
    # Widget-Styles
    # ==========================================================================

    WIDGET_STYLES = {
        "button": {
            "relief": tk.FLAT,
            "cursor": "hand2",
            "borderwidth": 0,
            "highlightthickness": 0,
            "padx": 20,
            "pady": 10,
            "activebackground": COLORS["primary_dark"],
            "activeforeground": "white",
        },

        "entry": {
            "relief": tk.FLAT,
            "borderwidth": 2,
            "highlightthickness": 1,
            "insertwidth": 2,
            "selectbackground": COLORS["selection"],
            "selectforeground": COLORS["text_primary"],
        },

        "label": {
            "borderwidth": 0,
            "highlightthickness": 0,
        },

        "frame": {
            "borderwidth": 0,
            "highlightthickness": 0,
        },

        "listbox": {
            "relief": tk.FLAT,
            "borderwidth": 1,
            "highlightthickness": 0,
            "selectbackground": COLORS["selection"],
            "selectforeground": COLORS["text_primary"],
            "activestyle": "none",
        },

        "text": {
            "relief": tk.FLAT,
            "borderwidth": 1,
            "highlightthickness": 0,
            "wrap": tk.WORD,
            "padx": 10,
            "pady": 10,
            "insertwidth": 2,
            "selectbackground": COLORS["selection"],
            "selectforeground": COLORS["text_primary"],
        },

        "scrollbar": {
            "width": 12,
            "elementborderwidth": 0,
            "arrowsize": 12,
        }
    }

    # ==========================================================================
    # Theme-Definitionen
    # ==========================================================================

    THEMES = {
        "light": {
            "bg": COLORS["background"],
            "fg": COLORS["text_primary"],
            "select_bg": COLORS["selection"],
            "select_fg": COLORS["text_primary"],
            "insert": COLORS["text_primary"],
            "highlight": COLORS["focus"],
        },

        "dark": {
            "bg": COLORS["dark_background"],
            "fg": COLORS["dark_text"],
            "select_bg": "#37474F",
            "select_fg": COLORS["dark_text"],
            "insert": COLORS["dark_text"],
            "highlight": COLORS["primary_light"],
        }
    }

    # ==========================================================================
    # Helper-Methoden
    # ==========================================================================

    @classmethod
    def get_font(cls, style: str = "normal", size: str = "normal") -> Tuple[str, int, str]:
        """
        Gibt eine Schriftart-Definition zurück

        Args:
            style: Stil ("normal", "bold", "italic", "title")
            size: Größe ("small", "normal", "medium", "large", "xlarge", "title")

        Returns:
            Tuple: (Familie, Größe, Stil)
        """
        family = cls.FONTS["family"]
        font_size = cls.FONTS["sizes"].get(size, cls.FONTS["sizes"]["normal"])

        if style == "bold":
            return (family, font_size, "bold")
        elif style == "italic":
            return (family, font_size, "italic")
        elif style == "bold_italic":
            return (family, font_size, "bold italic")
        elif style == "title":
            return (family, cls.FONTS["sizes"]["title"], "bold")
        else:
            return (family, font_size, "normal")

    @classmethod
    def get_color(cls, color_name: str, theme: str = None) -> str:
        """
        Gibt eine Farbe zurück

        Args:
            color_name: Name der Farbe
            theme: Theme-Name (optional)

        Returns:
            Hex-Farbcode
        """
        if theme and theme in cls.THEMES:
            theme_colors = cls.THEMES[theme]
            if color_name in theme_colors:
                return theme_colors[color_name]

        return cls.COLORS.get(color_name, "#000000")

    @classmethod
    def apply_style(cls, widget: tk.Widget, style_type: str = None):
        """
        Wendet einen Style auf ein Widget an

        Args:
            widget: Das zu stylende Widget
            style_type: Style-Typ (optional)
        """
        widget_class = widget.winfo_class()

        # Standard-Style für Widget-Typ
        if widget_class == "Button":
            style_dict = cls.WIDGET_STYLES.get("button", {})
        elif widget_class == "Entry":
            style_dict = cls.WIDGET_STYLES.get("entry", {})
        elif widget_class == "Label":
            style_dict = cls.WIDGET_STYLES.get("label", {})
        elif widget_class == "Frame" or widget_class == "Toplevel":
            style_dict = cls.WIDGET_STYLES.get("frame", {})
        elif widget_class == "Listbox":
            style_dict = cls.WIDGET_STYLES.get("listbox", {})
        elif widget_class == "Text":
            style_dict = cls.WIDGET_STYLES.get("text", {})
        else:
            style_dict = {}

        # Style anwenden
        for key, value in style_dict.items():
            try:
                widget.configure(**{key: value})
            except tk.TclError:
                # Option nicht verfügbar für dieses Widget
                pass


# ==============================================================================
# Theme-Management
# ==============================================================================

def apply_theme(root: tk.Tk, theme_name: str = None):
    """
    Wendet ein Theme auf die gesamte Anwendung an

    Args:
        root: Root-Window
        theme_name: Theme-Name (default aus Settings)
    """
    if theme_name is None:
        theme_name = GUI_SETTINGS.get("theme", {}).get("mode", "light")

    logger.info(f"Wende Theme an: {theme_name}")

    # Theme-Farben
    theme = Styles.THEMES.get(theme_name, Styles.THEMES["light"])

    # Root-Window konfigurieren
    root.configure(bg=theme["bg"])

    # Option-Database für neue Widgets setzen
    root.option_add("*background", theme["bg"])
    root.option_add("*Background", theme["bg"])
    root.option_add("*foreground", theme["fg"])
    root.option_add("*Foreground", theme["fg"])
    root.option_add("*selectBackground", theme["select_bg"])
    root.option_add("*selectForeground", theme["select_fg"])
    root.option_add("*insertBackground", theme["insert"])
    root.option_add("*highlightColor", theme["highlight"])
    root.option_add("*highlightBackground", theme["bg"])

    # Font-Optionen
    root.option_add("*Font", Styles.get_font("normal", "normal"))

    # Widget-spezifische Optionen
    root.option_add("*Button.relief", "flat")
    root.option_add("*Button.borderWidth", 0)
    root.option_add("*Button.highlightThickness", 0)
    root.option_add("*Button.cursor", "hand2")

    root.option_add("*Entry.relief", "flat")
    root.option_add("*Entry.borderWidth", 2)
    root.option_add("*Entry.highlightThickness", 1)

    root.option_add("*Text.relief", "flat")
    root.option_add("*Text.borderWidth", 1)
    root.option_add("*Text.highlightThickness", 0)

    root.option_add("*Listbox.relief", "flat")
    root.option_add("*Listbox.borderWidth", 1)
    root.option_add("*Listbox.highlightThickness", 0)

    # TTK-Styles konfigurieren
    configure_ttk_styles(root, theme_name)


def configure_ttk_styles(root: tk.Tk, theme_name: str = "light"):
    """
    Konfiguriert TTK-Widget-Styles

    Args:
        root: Root-Window
        theme_name: Theme-Name
    """
    style = ttk.Style(root)

    # Theme-Farben
    theme = Styles.THEMES.get(theme_name, Styles.THEMES["light"])
    colors = Styles.COLORS

    # Style-Theme setzen
    style.theme_use("clam")  # Modern aussehender Theme

    # Allgemeine Einstellungen
    style.configure(".",
                    background=theme["bg"],
                    foreground=theme["fg"],
                    fieldbackground=colors["surface"],
                    bordercolor=colors["border"],
                    darkcolor=colors["border"],
                    lightcolor=theme["bg"],
                    insertcolor=theme["insert"],
                    borderwidth=1,
                    relief="flat"
                    )

    # Button
    style.configure("TButton",
                    padding=(20, 10),
                    relief="flat",
                    borderwidth=0,
                    font=Styles.get_font("normal", "medium")
                    )

    style.map("TButton",
              background=[
                  ("active", colors["primary_dark"]),
                  ("pressed", colors["primary_dark"]),
                  ("disabled", colors["disabled"]),
                  ("", colors["primary"])
              ],
              foreground=[
                  ("active", "white"),
                  ("pressed", "white"),
                  ("disabled", colors["text_disabled"]),
                  ("", "white")
              ]
              )

    # Entry
    style.configure("TEntry",
                    padding=10,
                    relief="flat",
                    borderwidth=2,
                    font=Styles.get_font("normal", "medium")
                    )

    style.map("TEntry",
              bordercolor=[
                  ("focus", colors["focus"]),
                  ("", colors["border"])
              ],
              lightcolor=[
                  ("focus", colors["focus"]),
                  ("", colors["border"])
              ]
              )

    # Combobox
    style.configure("TCombobox",
                    padding=10,
                    relief="flat",
                    borderwidth=2,
                    arrowsize=15,
                    font=Styles.get_font("normal", "medium")
                    )

    style.map("TCombobox",
              fieldbackground=[
                  ("readonly", colors["surface"]),
                  ("disabled", colors["disabled"]),
                  ("", "white")
              ],
              bordercolor=[
                  ("focus", colors["focus"]),
                  ("", colors["border"])
              ]
              )

    # Notebook (Tabs)
    style.configure("TNotebook",
                    background=theme["bg"],
                    borderwidth=0,
                    relief="flat"
                    )

    style.configure("TNotebook.Tab",
                    padding=[20, 10],
                    background=colors["surface"],
                    foreground=colors["text_primary"],
                    borderwidth=0,
                    font=Styles.get_font("normal", "medium")
                    )

    style.map("TNotebook.Tab",
              background=[
                  ("selected", colors["primary"]),
                  ("active", colors["hover"]),
                  ("", colors["surface"])
              ],
              foreground=[
                  ("selected", "white"),
                  ("active", colors["text_primary"]),
                  ("", colors["text_primary"])
              ]
              )

    # Progressbar
    style.configure("TProgressbar",
                    background=colors["primary"],
                    borderwidth=0,
                    relief="flat",
                    darkcolor=colors["primary_dark"],
                    lightcolor=colors["primary_light"]
                    )

    # Scrollbar
    style.configure("TScrollbar",
                    background=colors["surface"],
                    bordercolor=colors["border"],
                    arrowcolor=colors["text_secondary"],
                    width=12,
                    relief="flat"
                    )

    style.map("TScrollbar",
              background=[
                  ("active", colors["hover"]),
                  ("pressed", colors["pressed"]),
                  ("", colors["surface"])
              ]
              )

    # LabelFrame
    style.configure("TLabelframe",
                    background=theme["bg"],
                    foreground=theme["fg"],
                    bordercolor=colors["border"],
                    relief="flat",
                    borderwidth=2
                    )

    style.configure("TLabelframe.Label",
                    background=theme["bg"],
                    foreground=colors["text_primary"],
                    font=Styles.get_font("bold", "medium")
                    )


# ==============================================================================
# Style-Presets für häufige Anwendungsfälle
# ==============================================================================

class StylePresets:
    """Vordefinierte Styles für verschiedene Widget-Typen"""

    @staticmethod
    def primary_button(button: tk.Button):
        """Primary Button Style"""
        button.configure(
            bg=Styles.COLORS["primary"],
            fg="white",
            activebackground=Styles.COLORS["primary_dark"],
            activeforeground="white",
            font=Styles.get_font("normal", "medium"),
            **Styles.WIDGET_STYLES["button"]
        )

    @staticmethod
    def secondary_button(button: tk.Button):
        """Secondary Button Style"""
        button.configure(
            bg=Styles.COLORS["secondary"],
            fg="white",
            activebackground=Styles.COLORS["secondary_dark"],
            activeforeground="white",
            font=Styles.get_font("normal", "medium"),
            **Styles.WIDGET_STYLES["button"]
        )

    @staticmethod
    def danger_button(button: tk.Button):
        """Danger/Delete Button Style"""
        button.configure(
            bg=Styles.COLORS["error"],
            fg="white",
            activebackground="#D32F2F",
            activeforeground="white",
            font=Styles.get_font("normal", "medium"),
            **Styles.WIDGET_STYLES["button"]
        )

    @staticmethod
    def ghost_button(button: tk.Button):
        """Ghost Button Style (nur Border)"""
        button.configure(
            bg=Styles.COLORS["background"],
            fg=Styles.COLORS["primary"],
            activebackground=Styles.COLORS["hover"],
            activeforeground=Styles.COLORS["primary_dark"],
            font=Styles.get_font("normal", "medium"),
            relief=tk.FLAT,
            borderwidth=2,
            highlightthickness=0
        )

    @staticmethod
    def title_label(label: tk.Label):
        """Titel-Label Style"""
        label.configure(
            font=Styles.get_font("title"),
            fg=Styles.COLORS["text_primary"],
            bg=Styles.COLORS["background"]
        )

    @staticmethod
    def subtitle_label(label: tk.Label):
        """Untertitel-Label Style"""
        label.configure(
            font=Styles.get_font("normal", "large"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["background"]
        )

    @staticmethod
    def info_label(label: tk.Label):
        """Info-Label Style"""
        label.configure(
            font=Styles.get_font("normal", "small"),
            fg=Styles.COLORS["text_secondary"],
            bg=Styles.COLORS["background"]
        )

    @staticmethod
    def error_label(label: tk.Label):
        """Fehler-Label Style"""
        label.configure(
            font=Styles.get_font("normal", "medium"),
            fg=Styles.COLORS["error"],
            bg=Styles.COLORS["background"]
        )

    @staticmethod
    def success_label(label: tk.Label):
        """Erfolgs-Label Style"""
        label.configure(
            font=Styles.get_font("normal", "medium"),
            fg=Styles.COLORS["success"],
            bg=Styles.COLORS["background"]
        )