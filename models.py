#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbank Models
Minimale Version mit direkten SQL-Abfragen
"""

from datetime import datetime
from connection import execute_query, execute_scalar
from utils import get_logger

logger = get_logger('Models')


class User:
    """ScannBenutzer Model"""

    @staticmethod
    def get_by_epc(tag_id):
        """Benutzer anhand RFID-Tag (hex) finden"""
        try:
            # Hex zu Decimal konvertieren
            epc_decimal = int(tag_id, 16)

            query = """
                    SELECT ID, Vorname, Nachname, BenutzerName, Email, EPC
                    FROM dbo.ScannBenutzer
                    WHERE EPC = ? \
                      AND xStatus = 0 \
                    """

            result = execute_query(query, (epc_decimal,), fetch_one=True)

            if result:
                return {
                    'ID': result[0],
                    'Vorname': result[1],
                    'Nachname': result[2],
                    'BenutzerName': result[3],
                    'Email': result[4],
                    'EPC': result[5]
                }
            return None

        except Exception as e:
            logger.error(f"Fehler bei get_by_epc: {e}")
            return None

    @staticmethod
    def get_all_active():
        """Alle aktiven Benutzer abrufen"""
        query = """
                SELECT ID, Vorname, Nachname, BenutzerName, Email, EPC
                FROM dbo.ScannBenutzer
                WHERE xStatus = 0
                ORDER BY BenutzerName \
                """

        results = execute_query(query, fetch_all=True)
        users = []

        for row in results:
            users.append({
                'ID': row[0],
                'Vorname': row[1],
                'Nachname': row[2],
                'BenutzerName': row[3],
                'Email': row[4],
                'EPC': row[5]
            })

        return users


class Session:
    """Sessions Model"""

    @staticmethod
    def create(user_id):
        """Neue Session erstellen"""
        try:
            # Erst prüfen ob bereits aktive Session
            check_query = """
                          SELECT ID \
                          FROM dbo.Sessions
                          WHERE UserID = ? \
                            AND Active = 1 \
                          """

            existing = execute_query(check_query, (user_id,), fetch_one=True)
            if existing:
                # Alte Session beenden
                Session.end(existing[0])

            # Neue Session erstellen
            insert_query = """
                           INSERT INTO dbo.Sessions (UserID, StartTS, Active)
                               OUTPUT INSERTED.ID, INSERTED.StartTS
                           VALUES (?, SYSDATETIME(), 1) \
                           """

            result = execute_query(insert_query, (user_id,), fetch_one=True)

            if result:
                return {
                    'ID': result[0],
                    'UserID': user_id,
                    'StartTS': result[1],
                    'Active': True
                }
            return None

        except Exception as e:
            logger.error(f"Fehler bei Session.create: {e}")
            return None

    @staticmethod
    def end(session_id):
        """Session beenden"""
        try:
            query = """
                    UPDATE dbo.Sessions
                    SET EndTS  = SYSDATETIME(), \
                        Active = 0
                    WHERE ID = ? \
                      AND Active = 1 \
                    """

            rows = execute_query(query, (session_id,))
            return rows > 0

        except Exception as e:
            logger.error(f"Fehler bei Session.end: {e}")
            return False

    @staticmethod
    def get_active():
        """Alle aktiven Sessions abrufen"""
        query = """
                SELECT s.ID, s.UserID, s.StartTS, u.BenutzerName
                FROM dbo.Sessions s
                         INNER JOIN dbo.ScannBenutzer u ON s.UserID = u.ID
                WHERE s.Active = 1
                ORDER BY s.StartTS DESC \
                """

        results = execute_query(query, fetch_all=True)
        sessions = []

        for row in results:
            sessions.append({
                'ID': row[0],
                'UserID': row[1],
                'StartTS': row[2],
                'BenutzerName': row[3]
            })

        return sessions


class QrScan:
    """QrScans Model"""

    @staticmethod
    def create(session_id, payload):
        """Neuen QR-Scan speichern"""
        try:
            query = """
                    INSERT INTO dbo.QrScans (SessionID, RawPayload, Valid)
                        OUTPUT INSERTED.ID, INSERTED.CapturedTS
                    VALUES (?, ?, 1) \
                    """

            result = execute_query(query, (session_id, payload), fetch_one=True)

            if result:
                return {
                    'ID': result[0],
                    'SessionID': session_id,
                    'RawPayload': payload,
                    'CapturedTS': result[1]
                }
            return None

        except Exception as e:
            logger.error(f"Fehler bei QrScan.create: {e}")
            return None

    @staticmethod
    def get_by_session(session_id, limit=100):
        """Scans einer Session abrufen"""
        query = """
                SELECT TOP(?) ID, RawPayload, PayloadJson, CapturedTS, Valid
                FROM dbo.QrScans
                WHERE SessionID = ?
                ORDER BY CapturedTS DESC \
                """

        results = execute_query(query, (limit, session_id), fetch_all=True)
        scans = []

        for row in results:
            scans.append({
                'ID': row[0],
                'RawPayload': row[1],
                'PayloadJson': row[2],
                'CapturedTS': row[3],
                'Valid': row[4]
            })

        return scans

    @staticmethod
    def count_by_session(session_id):
        """Anzahl Scans einer Session"""
        query = "SELECT COUNT(*) FROM dbo.QrScans WHERE SessionID = ?"
        return execute_scalar(query, (session_id,)) or 0


# Optional: Erweiterte Models für ScannKopf/ScannPosition
class ScannKopf:
    """ScannKopf Model (optional)"""

    @staticmethod
    def create(epc, scann_typ_id=1, arbeitsplatz="Wareneingang"):
        """ScannKopf erstellen"""
        try:
            # EPC als decimal
            epc_decimal = int(epc, 16) if isinstance(epc, str) else epc

            query = """
                    INSERT INTO dbo.ScannKopf
                        (EPC, ScannTyp_ID, Arbeitsplatz, TagesDatumINT, DatumINT, xBenutzer)
                        OUTPUT INSERTED.ID
                    VALUES (?, ?, ?, ?, ?, 'System') \
                    """

            now = datetime.now()
            date_int = int(now.strftime('%Y%m%d'))
            datetime_int = int(now.strftime('%Y%m%d%H%M%S'))

            result = execute_query(
                query,
                (epc_decimal, scann_typ_id, arbeitsplatz, date_int, datetime_int),
                fetch_one=True
            )

            return result[0] if result else None

        except Exception as e:
            logger.error(f"Fehler bei ScannKopf.create: {e}")
            return None


class ScannPosition:
    """ScannPosition Model (optional)"""

    @staticmethod
    def create(scann_kopf_id, kunde, auftrag, paket=None, zusatz=None):
        """ScannPosition erstellen"""
        try:
            query = """
                    INSERT INTO dbo.ScannPosition
                    (ScannKopf_ID, Kunde, Auftragsnummer, Paketnummer, Zusatzinformtion,
                     TagesDatumINT, DatumINT, xBenutzer)
                        OUTPUT INSERTED.ID
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'System') \
                    """

            now = datetime.now()
            date_int = int(now.strftime('%Y%m%d'))
            datetime_int = int(now.strftime('%Y%m%d%H%M%S'))

            result = execute_query(
                query,
                (scann_kopf_id, kunde, auftrag, paket, zusatz, date_int, datetime_int),
                fetch_one=True
            )

            return result[0] if result else None

        except Exception as e:
            logger.error(f"Fehler bei ScannPosition.create: {e}")
            return None