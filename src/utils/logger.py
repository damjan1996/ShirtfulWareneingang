#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging-Konfiguration und -Utilities
====================================

Zentrales Logging-System für die Wareneingang-Anwendung.
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from typing import Optional

from .helpers import ensure_directory, get_app_data_dir


class ColoredFormatter(logging.Formatter):
    """
    Formatter mit Farb-Unterstützung für Konsolen-Output
    """

    # ANSI Color Codes
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Grün
        'WARNING': '\033[33m',  # Gelb
        'ERROR': '\033[31m',  # Rot
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'  # Reset
    }

    def format(self, record):
        # Farbe basierend auf Level
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        # Modul-Namen kürzen
        record.name = record.name.split('.')[-1]

        return super().format(record)


def setup_logger(
        name: str = "Wareneingang",
        log_level: str = "INFO",
        log_to_file: bool = True,
        log_dir: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        console_output: bool = True,
        colored_output: bool = True
) -> logging.Logger:
    """
    Konfiguriert das Logging-System

    Args:
        name: Name des Root-Loggers
        log_level: Logging-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: In Datei loggen
        log_dir: Verzeichnis für Log-Dateien
        max_file_size: Maximale Größe einer Log-Datei
        backup_count: Anzahl Backup-Dateien
        console_output: Konsolen-Ausgabe aktivieren
        colored_output: Farbige Konsolen-Ausgabe

    Returns:
        Konfigurierter Logger
    """
    # Root-Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Bestehende Handler entfernen
    root_logger.handlers.clear()

    # Format definieren
    log_format = '%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Konsolen-Handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        if colored_output and sys.stdout.isatty():
            formatter = ColoredFormatter(log_format, date_format)
        else:
            formatter = logging.Formatter(log_format, date_format)

        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Datei-Handler
    if log_to_file:
        if log_dir is None:
            log_dir = os.path.join(get_app_data_dir(), 'logs')

        ensure_directory(log_dir)

        # Log-Dateiname mit Datum
        log_filename = f"{name.lower()}_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = os.path.join(log_dir, log_filename)

        # Rotating File Handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )

        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Error-Log (separate Datei für Fehler)
        error_log_path = os.path.join(log_dir, f"{name.lower()}_errors.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )

        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

    # Spezifische Logger konfigurieren
    app_logger = logging.getLogger(name)

    # Externe Bibliotheken auf WARNING setzen
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('cv2').setLevel(logging.WARNING)
    logging.getLogger('pyzbar').setLevel(logging.WARNING)

    app_logger.info(f"Logging-System initialisiert (Level: {log_level})")
    if log_to_file:
        app_logger.info(f"Log-Verzeichnis: {log_dir}")

    return app_logger


def get_logger(name: str) -> logging.Logger:
    """
    Gibt einen Logger für ein spezifisches Modul zurück

    Args:
        name: Name des Moduls

    Returns:
        Logger-Instanz
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context-Manager für temporäre Logging-Einstellungen
    """

    def __init__(self, logger: logging.Logger, level: str):
        """
        Initialisiert den Log-Context

        Args:
            logger: Der zu modifizierende Logger
            level: Temporärer Log-Level
        """
        self.logger = logger
        self.new_level = getattr(logging, level.upper())
        self.old_level = None

    def __enter__(self):
        """Context-Manager Entry"""
        self.old_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context-Manager Exit"""
        self.logger.setLevel(self.old_level)
        return False


def log_exception(logger: logging.Logger, message: str = "Unbehandelte Ausnahme"):
    """
    Loggt eine Exception mit Traceback

    Args:
        logger: Der zu verwendende Logger
        message: Zusätzliche Nachricht
    """
    import traceback
    logger.error(f"{message}:\n{traceback.format_exc()}")


def log_function_call(logger: logging.Logger):
    """
    Decorator zum Loggen von Funktionsaufrufen

    Args:
        logger: Der zu verwendende Logger
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Aufruf: {func_name}(args={args}, kwargs={kwargs})")

            try:
                result = func(*args, **kwargs)
                logger.debug(f"Ergebnis: {func_name} -> {result}")
                return result
            except Exception as e:
                logger.error(f"Fehler in {func_name}: {e}")
                raise

        return wrapper

    return decorator


def get_log_files(log_dir: Optional[str] = None) -> list:
    """
    Gibt eine Liste aller Log-Dateien zurück

    Args:
        log_dir: Log-Verzeichnis

    Returns:
        Liste mit Log-Dateipfaden
    """
    if log_dir is None:
        log_dir = os.path.join(get_app_data_dir(), 'logs')

    if not os.path.exists(log_dir):
        return []

    log_files = []
    for filename in os.listdir(log_dir):
        if filename.endswith('.log'):
            log_files.append(os.path.join(log_dir, filename))

    return sorted(log_files, reverse=True)


def clean_old_logs(log_dir: Optional[str] = None, days_to_keep: int = 30):
    """
    Löscht alte Log-Dateien

    Args:
        log_dir: Log-Verzeichnis
        days_to_keep: Anzahl Tage, die Logs behalten werden
    """
    if log_dir is None:
        log_dir = os.path.join(get_app_data_dir(), 'logs')

    if not os.path.exists(log_dir):
        return

    cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
    deleted_count = 0

    for filename in os.listdir(log_dir):
        if filename.endswith('.log'):
            file_path = os.path.join(log_dir, filename)

            try:
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Fehler beim Löschen von {file_path}: {e}")

    if deleted_count > 0:
        logger = get_logger(__name__)
        logger.info(f"{deleted_count} alte Log-Dateien gelöscht")


# Test-Funktion
if __name__ == "__main__":
    # Logger einrichten
    logger = setup_logger("TestLogger", "DEBUG")

    print("📝 Logger Test")
    print("=" * 50)

    # Verschiedene Log-Level testen
    logger.debug("Dies ist eine Debug-Nachricht")
    logger.info("Dies ist eine Info-Nachricht")
    logger.warning("Dies ist eine Warnung")
    logger.error("Dies ist ein Fehler")
    logger.critical("Dies ist kritisch!")

    # Context-Manager testen
    print("\n🔧 Context-Manager Test:")
    with LogContext(logger, "ERROR"):
        logger.debug("Diese Debug-Nachricht wird nicht angezeigt")
        logger.error("Diese Fehler-Nachricht wird angezeigt")

    logger.debug("Debug-Nachrichten sind wieder aktiv")


    # Decorator testen
    @log_function_call(logger)
    def test_function(x, y):
        return x + y


    print("\n🎯 Decorator Test:")
    result = test_function(5, 3)
    print(f"Ergebnis: {result}")

    # Log-Dateien anzeigen
    print("\n📁 Log-Dateien:")
    for log_file in get_log_files()[:5]:  # Nur erste 5
        print(f"  - {os.path.basename(log_file)}")

    print("\n✅ Logger Test abgeschlossen")