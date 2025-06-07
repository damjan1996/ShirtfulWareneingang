#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL Query Definitionen für die Wareneingang-Anwendung
Zentrale Verwaltung aller SQL-Queries
"""

from typing import Dict, Any, Optional
from datetime import datetime


# ==============================================================================
# Query Klasse
# ==============================================================================

class Queries:
    """
    Zentrale Sammlung aller SQL-Queries
    Organisiert nach Funktionsbereichen
    """

    # ==========================================================================
    # Benutzer-Queries (ScannBenutzer)
    # ==========================================================================

    class Users:
        """Queries für Benutzerverwaltung"""

        # Benutzer nach EPC (RFID-Tag) suchen
        GET_BY_EPC = """
                     SELECT ID, \
                            Vorname, \
                            Nachname, \
                            Benutzer, \
                            BenutzerName, \
                            Email, \
                            EPC, \
                            xStatus, \
                            xDatum
                     FROM dbo.ScannBenutzer
                     WHERE EPC = ?
                       AND xStatus = 0 -- Nur aktive Benutzer \
                     """

        # Benutzer nach ID abrufen
        GET_BY_ID = """
                    SELECT ID, \
                           Vorname, \
                           Nachname, \
                           Benutzer, \
                           BenutzerName, \
                           Email, \
                           EPC, \
                           xStatus, \
                           xDatum
                    FROM dbo.ScannBenutzer
                    WHERE ID = ? \
                    """

        # Alle aktiven Benutzer abrufen
        GET_ALL_ACTIVE = """
                         SELECT ID, \
                                Vorname, \
                                Nachname, \
                                BenutzerName, \
                                Email, \
                                EPC, \
                                xDatum
                         FROM dbo.ScannBenutzer
                         WHERE xStatus = 0
                         ORDER BY BenutzerName \
                         """

        # Benutzer erstellen
        CREATE = """
                 INSERT INTO dbo.ScannBenutzer
                 (Vorname, Nachname, Benutzer, BenutzerName, BenutzerPasswort,
                  Email, EPC, xStatus, xDatum, xDatumINT, xBenutzer)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                 """

        # Benutzer aktualisieren
        UPDATE = """
                 UPDATE dbo.ScannBenutzer
                 SET Vorname   = ?,
                     Nachname  = ?,
                     Email     = ?,
                     xDatum    = GETDATE(),
                     xDatumINT = ?,
                     xBenutzer = ?
                 WHERE ID = ? \
                 """

        # Benutzer deaktivieren (Soft Delete)
        DEACTIVATE = """
                     UPDATE dbo.ScannBenutzer
                     SET xStatus   = 1,
                         xDatum    = GETDATE(),
                         xDatumINT = ?,
                         xBenutzer = ?
                     WHERE ID = ? \
                     """

        # Benutzer nach EPC prüfen
        CHECK_EPC_EXISTS = """
                           SELECT COUNT(*)
                           FROM dbo.ScannBenutzer
                           WHERE EPC = ? \
                           """

        # Letzte Aktivität aktualisieren
        UPDATE_LAST_ACTIVITY = """
                               UPDATE dbo.ScannBenutzer
                               SET xDatum = GETDATE()
                               WHERE ID = ? \
                               """

    # ==========================================================================
    # Scan-Kopf Queries (ScannKopf)
    # ==========================================================================

    class ScanHead:
        """Queries für Scan-Kopfdaten"""

        # Neuen Scan-Kopf erstellen
        CREATE = """
                 INSERT INTO dbo.ScannKopf
                 (TagesDatum, TagesDatumINT, Datum, DatumINT, EPC,
                  Arbeitsplatz, ScannTyp_ID, xStatus, xDatum, xDatumINT, xBenutzer)
                     OUTPUT INSERTED.ID
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                 """

        # Scan-Kopf nach ID abrufen
        GET_BY_ID = """
                    SELECT sk.ID, \
                           sk.TagesDatum, \
                           sk.Datum, \
                           sk.EPC, \
                           sk.Arbeitsplatz, \
                           sk.ScannTyp_ID, \
                           st.Bezeichnung as ScannTyp, \
                           sk.xStatus
                    FROM dbo.ScannKopf sk
                             INNER JOIN dbo.ScannTyp st ON sk.ScannTyp_ID = st.ID
                    WHERE sk.ID = ? \
                    """

        # Aktive Scan-Session für Benutzer
        GET_ACTIVE_SESSION = """
                             SELECT TOP 1
                sk.ID, sk.Datum,
                                    sk.Arbeitsplatz,
                                    st.Bezeichnung as ScannTyp
                             FROM dbo.ScannKopf sk
                                      INNER JOIN dbo.ScannTyp st ON sk.ScannTyp_ID = st.ID
                             WHERE sk.EPC = ?
                               AND sk.xStatus = 0
                               AND sk.TagesDatum = CAST(GETDATE() AS DATE)
                             ORDER BY sk.Datum DESC \
                             """

        # Scan-Sessions eines Tages
        GET_BY_DATE = """
                      SELECT sk.ID, \
                             sk.EPC, \
                             sb.BenutzerName, \
                             sk.Datum, \
                             sk.Arbeitsplatz, \
                             st.Bezeichnung as ScannTyp, \
                             COUNT(sp.ID)   as AnzahlScans
                      FROM dbo.ScannKopf sk
                               INNER JOIN dbo.ScannBenutzer sb ON sk.EPC = sb.EPC
                               INNER JOIN dbo.ScannTyp st ON sk.ScannTyp_ID = st.ID
                               LEFT JOIN dbo.ScannPosition sp ON sk.ID = sp.ScannKopf_ID
                      WHERE sk.TagesDatum = ?
                      GROUP BY sk.ID, sk.EPC, sb.BenutzerName, sk.Datum,
                               sk.Arbeitsplatz, st.Bezeichnung
                      ORDER BY sk.Datum DESC \
                      """

        # Session beenden
        CLOSE_SESSION = """
                        UPDATE dbo.ScannKopf
                        SET xStatus = 1,
                            xDatum  = GETDATE()
                        WHERE ID = ? \
                        """

        # Statistik für einen Tag
        GET_DAILY_STATS = """
                          SELECT st.Bezeichnung         as ScannTyp, \
                                 COUNT(DISTINCT sk.ID)  as AnzahlSessions, \
                                 COUNT(DISTINCT sk.EPC) as AnzahlBenutzer, \
                                 COUNT(sp.ID)           as AnzahlScans
                          FROM dbo.ScannKopf sk
                                   INNER JOIN dbo.ScannTyp st ON sk.ScannTyp_ID = st.ID
                                   LEFT JOIN dbo.ScannPosition sp ON sk.ID = sp.ScannKopf_ID
                          WHERE sk.TagesDatum = ?
                          GROUP BY st.Bezeichnung, st.ID
                          ORDER BY st.ID \
                          """

    # ==========================================================================
    # Scan-Position Queries (ScannPosition)
    # ==========================================================================

    class ScanPosition:
        """Queries für Scan-Positionen"""

        # Neue Scan-Position erstellen
        CREATE = """
                 INSERT INTO dbo.ScannPosition
                 (ScannKopf_ID, TagesDatum, TagesDatumINT, Datum, DatumINT,
                  Kunde, Auftragsnummer, Paketnummer, Zusatzinformtion,
                  xStatus, xDatum, xDatumINT, xBenutzer)
                     OUTPUT INSERTED.ID
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                 """

        # Positionen eines Scan-Kopfes
        GET_BY_SCAN_HEAD = """
                           SELECT ID, \
                                  Datum, \
                                  Kunde, \
                                  Auftragsnummer, \
                                  Paketnummer, \
                                  Zusatzinformtion
                           FROM dbo.ScannPosition
                           WHERE ScannKopf_ID = ?
                           ORDER BY Datum DESC \
                           """

        # Position nach ID
        GET_BY_ID = """
                    SELECT ID, \
                           ScannKopf_ID, \
                           Datum, \
                           Kunde, \
                           Auftragsnummer, \
                           Paketnummer, \
                           Zusatzinformtion, \
                           xStatus
                    FROM dbo.ScannPosition
                    WHERE ID = ? \
                    """

        # Prüfen ob Paket heute bereits gescannt
        CHECK_DUPLICATE = """
                          SELECT TOP 1
                sp.ID, sp.Datum,
                                 sk.Arbeitsplatz,
                                 sb.BenutzerName
                          FROM dbo.ScannPosition sp
                                   INNER JOIN dbo.ScannKopf sk ON sp.ScannKopf_ID = sk.ID
                                   INNER JOIN dbo.ScannBenutzer sb ON sk.EPC = sb.EPC
                          WHERE sp.Paketnummer = ?
                            AND sp.TagesDatum = CAST(GETDATE() AS DATE)
                            AND sk.ScannTyp_ID = ?
                          ORDER BY sp.Datum DESC \
                          """

        # Position löschen (Soft Delete)
        DELETE = """
                 UPDATE dbo.ScannPosition
                 SET xStatus   = 2,
                     xDatum    = GETDATE(),
                     xBenutzer = ?
                 WHERE ID = ? \
                 """

        # Anzahl Scans heute
        COUNT_TODAY = """
                      SELECT COUNT(*)
                      FROM dbo.ScannPosition sp
                               INNER JOIN dbo.ScannKopf sk ON sp.ScannKopf_ID = sk.ID
                      WHERE sk.EPC = ?
                        AND sp.TagesDatum = CAST(GETDATE() AS DATE) \
                      """

        # Letzte Scans eines Benutzers
        GET_RECENT_BY_USER = """
                             SELECT TOP 10
                sp.ID, sp.Datum,
                                    sp.Kunde,
                                    sp.Auftragsnummer,
                                    sp.Paketnummer,
                                    st.Bezeichnung as ScannTyp
                             FROM dbo.ScannPosition sp
                                      INNER JOIN dbo.ScannKopf sk ON sp.ScannKopf_ID = sk.ID
                                      INNER JOIN dbo.ScannTyp st ON sk.ScannTyp_ID = st.ID
                             WHERE sk.EPC = ?
                             ORDER BY sp.Datum DESC \
                             """

    # ==========================================================================
    # Scan-Typ Queries (ScannTyp)
    # ==========================================================================

    class ScanType:
        """Queries für Scan-Typen"""

        # Alle aktiven Scan-Typen
        GET_ALL_ACTIVE = """
                         SELECT ID, \
                                Bezeichnung
                         FROM dbo.ScannTyp
                         WHERE xStatus = 0
                         ORDER BY ID \
                         """

        # Scan-Typ nach ID
        GET_BY_ID = """
                    SELECT ID, \
                           Bezeichnung
                    FROM dbo.ScannTyp
                    WHERE ID = ? \
                    """

        # Scan-Typ nach Bezeichnung
        GET_BY_NAME = """
                      SELECT ID, \
                             Bezeichnung
                      FROM dbo.ScannTyp
                      WHERE Bezeichnung = ?
                        AND xStatus = 0 \
                      """

    # ==========================================================================
    # Zeiterfassungs-Queries
    # ==========================================================================

    class TimeTracking:
        """Queries für Zeiterfassung"""

        # Arbeitsbeginn erfassen
        CLOCK_IN = """
                   INSERT INTO dbo.Zeiterfassung
                       (BenutzerID, EPC, Datum, EinUhrzeit, xStatus)
                   VALUES (?, ?, GETDATE(), GETDATE(), 0) \
                   """

        # Arbeitsende erfassen
        CLOCK_OUT = """
                    UPDATE dbo.Zeiterfassung
                    SET AusUhrzeit = GETDATE(),
                        xStatus    = 1
                    WHERE BenutzerID = ?
                      AND CAST(Datum AS DATE) = CAST(GETDATE() AS DATE)
                      AND AusUhrzeit IS NULL \
                    """

        # Aktuelle Arbeitszeit heute
        GET_TODAY_WORKTIME = """
                             SELECT EinUhrzeit, \
                                    AusUhrzeit, \
                                    DATEDIFF(MINUTE, EinUhrzeit, ISNULL(AusUhrzeit, GETDATE())) as MinutenGearbeitet
                             FROM dbo.Zeiterfassung
                             WHERE BenutzerID = ?
                               AND CAST(Datum AS DATE) = CAST(GETDATE() AS DATE) \
                             """

        # Prüfen ob bereits eingestempelt
        CHECK_CLOCKED_IN = """
                           SELECT COUNT(*)
                           FROM dbo.Zeiterfassung
                           WHERE BenutzerID = ?
                             AND CAST(Datum AS DATE) = CAST(GETDATE() AS DATE)
                             AND AusUhrzeit IS NULL \
                           """

    # ==========================================================================
    # Statistik-Queries
    # ==========================================================================

    class Statistics:
        """Queries für Statistiken und Reports"""

        # Tagesübersicht
        DAILY_OVERVIEW = """
                         SELECT COUNT(DISTINCT sk.EPC) as AnzahlBenutzer, \
                                COUNT(DISTINCT sk.ID)  as AnzahlSessions, \
                                COUNT(sp.ID)           as AnzahlScans, \
                                MIN(sk.Datum)          as ErsterScan, \
                                MAX(sk.Datum)          as LetzterScan
                         FROM dbo.ScannKopf sk
                                  LEFT JOIN dbo.ScannPosition sp ON sk.ID = sp.ScannKopf_ID
                         WHERE sk.TagesDatum = ? \
                         """

        # Benutzer-Leistung
        USER_PERFORMANCE = """
                           SELECT sb.BenutzerName, \
                                  COUNT(DISTINCT sk.ID)                     as AnzahlSessions, \
                                  COUNT(sp.ID)                              as AnzahlScans, \
                                  AVG(DATEDIFF(SECOND, sk.Datum, sp.Datum)) as DurchschnittlicheScanzeit
                           FROM dbo.ScannKopf sk
                                    INNER JOIN dbo.ScannBenutzer sb ON sk.EPC = sb.EPC
                                    LEFT JOIN dbo.ScannPosition sp ON sk.ID = sp.ScannKopf_ID
                           WHERE sk.TagesDatum BETWEEN ? AND ?
                           GROUP BY sb.BenutzerName, sb.ID
                           ORDER BY COUNT(sp.ID) DESC \
                           """

        # Stundenverteilung
        HOURLY_DISTRIBUTION = """
                              SELECT DATEPART(HOUR, sp.Datum) as Stunde, \
                                     COUNT(*)                 as AnzahlScans
                              FROM dbo.ScannPosition sp
                              WHERE sp.TagesDatum = ?
                              GROUP BY DATEPART(HOUR, sp.Datum)
                              ORDER BY Stunde \
                              """

        # Top-Kunden
        TOP_CUSTOMERS = """
                        SELECT TOP 10
                Kunde, COUNT(*) as AnzahlPakete,
                               COUNT(DISTINCT Auftragsnummer) as AnzahlAuftraege
                        FROM dbo.ScannPosition
                        WHERE TagesDatum BETWEEN ? AND ?
                          AND Kunde IS NOT NULL
                        GROUP BY Kunde
                        ORDER BY COUNT(*) DESC \
                        """

    # ==========================================================================
    # System-Queries
    # ==========================================================================

    class System:
        """System- und Wartungs-Queries"""

        # Datenbank-Version prüfen
        CHECK_VERSION = """
            SELECT @@VERSION AS Version
        """

        # Verbindung testen
        TEST_CONNECTION = """
            SELECT 1 AS Connected
        """

        # Tabellengrößen
        TABLE_SIZES = """
                      SELECT t.name                        AS TableName, \
                             SUM(p.rows)                   AS RowCount, \
                             SUM(a.total_pages) * 8 / 1024 AS TotalSpaceMB
                      FROM sys.tables t
                               INNER JOIN sys.indexes i ON t.object_id = i.object_id
                               INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                               INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                      WHERE t.is_ms_shipped = 0
                      GROUP BY t.name
                      ORDER BY SUM(a.total_pages) DESC \
                      """

        # Alte Daten bereinigen
        CLEANUP_OLD_DATA = """
                           DELETE \
                           FROM dbo.ScannPosition
                           WHERE TagesDatum < DATEADD(DAY, ?, GETDATE())
                             AND xStatus = 2 \
                           """


# ==============================================================================
# Query Builder Hilfsfunktionen
# ==============================================================================

class QueryHelper:
    """Hilfsfunktionen für dynamische Queries"""

    @staticmethod
    def build_insert_query(table: str, data: Dict[str, Any],
                           output_column: str = None) -> tuple:
        """
        Baut eine INSERT Query mit Parametern

        Args:
            table: Tabellenname
            data: Dictionary mit Spalten und Werten
            output_column: Optional - OUTPUT Spalte (z.B. "ID")

        Returns:
            tuple: (query, parameters)
        """
        columns = list(data.keys())
        placeholders = ["?" for _ in columns]

        query = f"INSERT INTO {table} ({', '.join(columns)}) "

        if output_column:
            query += f"OUTPUT INSERTED.{output_column} "

        query += f"VALUES ({', '.join(placeholders)})"

        return query, tuple(data.values())

    @staticmethod
    def build_update_query(table: str, data: Dict[str, Any],
                           where: Dict[str, Any]) -> tuple:
        """
        Baut eine UPDATE Query mit Parametern

        Args:
            table: Tabellenname
            data: Dictionary mit zu aktualisierenden Spalten
            where: Dictionary mit WHERE-Bedingungen

        Returns:
            tuple: (query, parameters)
        """
        set_parts = [f"{col} = ?" for col in data.keys()]
        where_parts = [f"{col} = ?" for col in where.keys()]

        query = f"UPDATE {table} SET {', '.join(set_parts)} "
        query += f"WHERE {' AND '.join(where_parts)}"

        params = list(data.values()) + list(where.values())

        return query, tuple(params)

    @staticmethod
    def build_select_query(table: str, columns: list = None,
                           where: Dict[str, Any] = None,
                           order_by: str = None,
                           limit: int = None) -> tuple:
        """
        Baut eine SELECT Query mit Parametern

        Args:
            table: Tabellenname
            columns: Liste der Spalten (None = *)
            where: Dictionary mit WHERE-Bedingungen
            order_by: ORDER BY Klausel
            limit: Anzahl Zeilen (TOP)

        Returns:
            tuple: (query, parameters)
        """
        col_str = ", ".join(columns) if columns else "*"

        query = "SELECT "
        if limit:
            query += f"TOP {limit} "

        query += f"{col_str} FROM {table}"

        params = []
        if where:
            where_parts = []
            for col, value in where.items():
                if value is None:
                    where_parts.append(f"{col} IS NULL")
                else:
                    where_parts.append(f"{col} = ?")
                    params.append(value)
            query += f" WHERE {' AND '.join(where_parts)}"

        if order_by:
            query += f" ORDER BY {order_by}"

        return query, tuple(params)

    @staticmethod
    def format_datetime_int(dt: datetime = None) -> int:
        """
        Formatiert DateTime als Integer (YYYYMMDDHHMMSS)

        Args:
            dt: DateTime (None = jetzt)

        Returns:
            int: Formatiertes Datum
        """
        if dt is None:
            dt = datetime.now()
        return int(dt.strftime("%Y%m%d%H%M%S"))