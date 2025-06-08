#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR-Code Duplikat-Verhinderung für Wareneingang
Verhindert dass gleiche QR-Codes mehrfach erfasst werden
"""

import time
import os
from datetime import datetime, timedelta
from models import QrScan
from utils import get_logger

logger = get_logger('DuplicatePrevent')


class QRDuplicatePreventionManager:
    """Verhindert Duplikate von QR-Codes"""

    def __init__(self):
        # Cache für kürzlich gescannte Codes
        self.recent_scans = {}  # {qr_code: timestamp}
        self.session_scans = {}  # {session_id: {qr_code: timestamp}}

        # Konfiguration aus Umgebungsvariablen
        self.global_cooldown = int(os.getenv('QR_GLOBAL_COOLDOWN', '300'))  # 5 Minuten default
        self.session_cooldown = int(os.getenv('QR_SESSION_COOLDOWN', '3600'))  # 1 Stunde default
        self.duplicate_check_enabled = os.getenv('QR_DUPLICATE_CHECK', 'True').lower() == 'true'

        self.cleanup_interval = 600  # 10 Minuten zwischen Cleanups
        self.last_cleanup = time.time()

        logger.info(f"Duplikat-Verhinderung initialisiert:")
        logger.info(f"  Global Cooldown: {self.global_cooldown}s ({self.global_cooldown // 60}min)")
        logger.info(f"  Session Cooldown: {self.session_cooldown}s ({self.session_cooldown // 60}min)")
        logger.info(f"  Aktiviert: {self.duplicate_check_enabled}")

    def is_duplicate(self, qr_code, session_id=None):
        """
        Prüft ob QR-Code ein Duplikat ist

        Returns:
            dict mit 'is_duplicate', 'reason', 'last_scan_time'
        """
        # Wenn Duplikat-Check deaktiviert, nie als Duplikat markieren
        if not self.duplicate_check_enabled:
            return {
                'is_duplicate': False,
                'reason': 'disabled',
                'remaining_seconds': 0,
                'last_scan_time': None
            }

        current_time = time.time()

        # Cleanup alte Einträge
        self._cleanup_old_entries(current_time)

        # 1. Globaler Check - wurde dieser Code kürzlich gescannt?
        if qr_code in self.recent_scans:
            last_scan = self.recent_scans[qr_code]
            time_diff = current_time - last_scan

            if time_diff < self.global_cooldown:
                remaining = self.global_cooldown - time_diff
                return {
                    'is_duplicate': True,
                    'reason': 'global_cooldown',
                    'remaining_seconds': int(remaining),
                    'last_scan_time': datetime.fromtimestamp(last_scan)
                }

        # 2. Session-spezifischer Check
        if session_id:
            if session_id not in self.session_scans:
                self.session_scans[session_id] = {}

            session_codes = self.session_scans[session_id]

            if qr_code in session_codes:
                last_scan = session_codes[qr_code]
                time_diff = current_time - last_scan

                if time_diff < self.session_cooldown:
                    remaining = self.session_cooldown - time_diff
                    return {
                        'is_duplicate': True,
                        'reason': 'session_cooldown',
                        'remaining_seconds': int(remaining),
                        'last_scan_time': datetime.fromtimestamp(last_scan)
                    }

        # 3. Datenbank-Check - wurde dieser Code heute bereits in dieser Session gescannt?
        if session_id:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            try:
                from connection import execute_query

                query = """
                        SELECT TOP 1 CapturedTS
                        FROM dbo.QrScans
                        WHERE SessionID = ?
                          AND RawPayload = ?
                          AND CapturedTS >= ?
                        ORDER BY CapturedTS DESC \
                        """

                result = execute_query(query, (session_id, qr_code, today_start), fetch_one=True)

                if result:
                    last_db_scan = result[0]
                    return {
                        'is_duplicate': True,
                        'reason': 'database_duplicate',
                        'remaining_seconds': 0,
                        'last_scan_time': last_db_scan
                    }

            except Exception as e:
                logger.error(f"Fehler bei Datenbank-Duplikat-Check: {e}")

        # Kein Duplikat gefunden
        return {
            'is_duplicate': False,
            'reason': 'unique',
            'remaining_seconds': 0,
            'last_scan_time': None
        }

    def register_scan(self, qr_code, session_id=None):
        """Registriert einen neuen Scan"""
        if not self.duplicate_check_enabled:
            return

        current_time = time.time()

        # Global registrieren
        self.recent_scans[qr_code] = current_time

        # Session-spezifisch registrieren
        if session_id:
            if session_id not in self.session_scans:
                self.session_scans[session_id] = {}
            self.session_scans[session_id][qr_code] = current_time

        logger.debug(f"QR-Code registriert: {qr_code[:50]}... (Session: {session_id})")

    def _cleanup_old_entries(self, current_time):
        """Entfernt alte Einträge aus dem Cache"""
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        # Global cleanup
        expired_global = [
            code for code, timestamp in self.recent_scans.items()
            if current_time - timestamp > self.global_cooldown
        ]
        for code in expired_global:
            del self.recent_scans[code]

        # Session cleanup
        for session_id in list(self.session_scans.keys()):
            session_codes = self.session_scans[session_id]
            expired_session = [
                code for code, timestamp in session_codes.items()
                if current_time - timestamp > self.session_cooldown
            ]
            for code in expired_session:
                del session_codes[code]

            # Leere Sessions entfernen
            if not session_codes:
                del self.session_scans[session_id]

        self.last_cleanup = current_time

        if expired_global or any(self.session_scans.values()):
            logger.debug(f"Cleanup: {len(expired_global)} globale, Session-Caches: {len(self.session_scans)}")

    def get_stats(self):
        """Gibt Statistiken zurück"""
        total_global = len(self.recent_scans)
        total_sessions = len(self.session_scans)
        total_session_codes = sum(len(codes) for codes in self.session_scans.values())

        return {
            'global_codes': total_global,
            'active_sessions': total_sessions,
            'session_codes': total_session_codes,
            'global_cooldown_minutes': self.global_cooldown / 60,
            'session_cooldown_minutes': self.session_cooldown / 60,
            'enabled': self.duplicate_check_enabled
        }

    def clear_session(self, session_id):
        """Löscht alle Codes einer Session (bei Logout)"""
        if session_id in self.session_scans:
            count = len(self.session_scans[session_id])
            del self.session_scans[session_id]
            logger.info(f"Session {session_id} mit {count} Codes aus Duplikat-Cache entfernt")


# Globale Instanz
duplicate_manager = QRDuplicatePreventionManager()


def check_qr_duplicate(qr_code, session_id=None):
    """Vereinfachte Funktion zum Duplikat-Check"""
    return duplicate_manager.is_duplicate(qr_code, session_id)


def register_qr_scan(qr_code, session_id=None):
    """Vereinfachte Funktion zur Scan-Registrierung"""
    duplicate_manager.register_scan(qr_code, session_id)


def clear_session_duplicates(session_id):
    """Vereinfachte Funktion zum Session-Cleanup"""
    duplicate_manager.clear_session(session_id)


def get_duplicate_stats():
    """Vereinfachte Funktion für Statistiken"""
    return duplicate_manager.get_stats()