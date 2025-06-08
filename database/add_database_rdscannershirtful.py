#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbank-Setup für RdScanner
Erstellt alle notwendigen Tabellen
"""

import pyodbc
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG


def create_database_structure():
    """Erstellt die Datenbankstruktur"""

    # Verbindung ohne Datenbank-Angabe für CREATE DATABASE
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={DB_CONFIG['server']};"
        f"UID={DB_CONFIG['user']};"
        f"PWD={DB_CONFIG['password']};"
        f"TrustServerCertificate=yes;"
        f"Encrypt=no;"
    )

    try:
        print("🔄 Stelle Verbindung zum Server her...")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        conn.autocommit = True

        # Datenbank erstellen falls nicht vorhanden
        print(f"📦 Erstelle Datenbank '{DB_CONFIG['database']}' falls nicht vorhanden...")
        cursor.execute(f"""
            IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{DB_CONFIG['database']}')
            CREATE DATABASE [{DB_CONFIG['database']}]
        """)

        # Zur Datenbank wechseln
        cursor.execute(f"USE [{DB_CONFIG['database']}]")

        # Tabellen erstellen
        print("📋 Erstelle Tabellen...")

        # ScannBenutzer
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ScannBenutzer')
            CREATE TABLE dbo.ScannBenutzer (
                ID decimal(18,0) IDENTITY(1,1) NOT NULL PRIMARY KEY,
                Vorname varchar(255) NULL,
                Nachname varchar(255) NULL,
                Benutzer varchar(255) NULL,
                BenutzerName varchar(255) NULL,
                BenutzerPasswort varchar(255) NULL,
                Email varchar(255) NULL,
                EPC decimal(38,0) NULL,
                xStatus int NULL DEFAULT 0,
                xDatum datetime NULL DEFAULT GETDATE(),
                xDatumINT decimal(18,0) NULL,
                xBenutzer varchar(255) NULL,
                xVersion timestamp NOT NULL
            )
        """)
        print("   ✅ ScannBenutzer erstellt")

        # Sessions
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Sessions')
            CREATE TABLE dbo.Sessions (
                ID bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
                UserID decimal(18,0) NOT NULL,
                StartTS datetime2 NOT NULL DEFAULT SYSDATETIME(),
                EndTS datetime2 NULL,
                DurationSec AS DATEDIFF(SECOND, StartTS, ISNULL(EndTS, SYSDATETIME())),
                Active bit NOT NULL DEFAULT 1
            )
        """)
        print("   ✅ Sessions erstellt")

        # QrScans
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'QrScans')
            CREATE TABLE dbo.QrScans (
                ID bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
                SessionID bigint NOT NULL,
                RawPayload nvarchar(MAX) NOT NULL,
                PayloadJson AS (
                    CASE 
                        WHEN ISJSON(RawPayload) = 1 THEN RawPayload
                        ELSE NULL
                    END
                ),
                CapturedTS datetime2 NOT NULL DEFAULT SYSDATETIME(),
                Valid bit NOT NULL DEFAULT 1
            )
        """)
        print("   ✅ QrScans erstellt")

        # ScannTyp (optional)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ScannTyp')
            CREATE TABLE dbo.ScannTyp (
                ID decimal(18,0) IDENTITY(1,1) NOT NULL PRIMARY KEY,
                Bezeichnung varchar(255) NULL,
                xStatus int NULL DEFAULT 0,
                xDatum datetime NULL DEFAULT GETDATE(),
                xDatumINT decimal(18,0) NULL,
                xBenutzer varchar(255) NULL,
                xVersion timestamp NOT NULL
            )
        """)
        print("   ✅ ScannTyp erstellt")

        # ScannKopf (optional)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ScannKopf')
            CREATE TABLE dbo.ScannKopf (
                ID decimal(18,0) IDENTITY(1,1) NOT NULL PRIMARY KEY,
                TagesDatum date NULL DEFAULT CAST(GETDATE() AS DATE),
                TagesDatumINT int NULL,
                Datum datetime NULL DEFAULT GETDATE(),
                DatumINT decimal(18,0) NULL,
                EPC decimal(38,0) NULL,
                Arbeitsplatz varchar(255) NULL,
                ScannTyp_ID decimal(18,0) NULL,
                xStatus int NULL DEFAULT 0,
                xDatum datetime NULL DEFAULT GETDATE(),
                xDatumINT decimal(18,0) NULL,
                xBenutzer varchar(255) NULL,
                xVersion timestamp NOT NULL
            )
        """)
        print("   ✅ ScannKopf erstellt")

        # ScannPosition (optional)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ScannPosition')
            CREATE TABLE dbo.ScannPosition (
                ID decimal(18,0) IDENTITY(1,1) NOT NULL PRIMARY KEY,
                ScannKopf_ID decimal(18,0) NOT NULL,
                TagesDatum date NULL DEFAULT CAST(GETDATE() AS DATE),
                TagesDatumINT int NULL,
                Datum datetime NULL DEFAULT GETDATE(),
                DatumINT decimal(18,0) NULL,
                Kunde varchar(255) NULL,
                Auftragsnummer varchar(255) NULL,
                Paketnummer varchar(255) NULL,
                Zusatzinformtion varchar(255) NULL,
                xStatus int NULL DEFAULT 0,
                xDatum datetime NULL DEFAULT GETDATE(),
                xDatumINT decimal(18,0) NULL,
                xBenutzer varchar(255) NULL,
                xVersion timestamp NOT NULL
            )
        """)
        print("   ✅ ScannPosition erstellt")

        # Indizes erstellen
        print("\n🔍 Erstelle Indizes...")

        # Unique Index für aktive Sessions
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'UQ_Sessions_ActiveUser')
            CREATE UNIQUE INDEX UQ_Sessions_ActiveUser 
            ON dbo.Sessions(UserID) 
            WHERE Active = 1
        """)
        print("   ✅ Unique Index für aktive Sessions")

        # Index für EPC
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_ScannBenutzer_EPC')
            CREATE INDEX IX_ScannBenutzer_EPC 
            ON dbo.ScannBenutzer(EPC)
        """)
        print("   ✅ Index für EPC")

        # Foreign Keys
        print("\n🔗 Erstelle Foreign Keys...")

        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_Sessions_Users')
            ALTER TABLE dbo.Sessions
            ADD CONSTRAINT FK_Sessions_Users 
            FOREIGN KEY (UserID) REFERENCES dbo.ScannBenutzer(ID)
        """)

        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_QrScans_Sessions')
            ALTER TABLE dbo.QrScans
            ADD CONSTRAINT FK_QrScans_Sessions 
            FOREIGN KEY (SessionID) REFERENCES dbo.Sessions(ID)
        """)
        print("   ✅ Foreign Keys erstellt")

        print("\n✅ Datenbankstruktur erfolgreich erstellt!")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        return False


def main():
    """Hauptfunktion"""
    print("🔷 RdScanner Datenbank-Setup")
    print("=" * 50)
    print(f"Server: {DB_CONFIG['server']}")
    print(f"Datenbank: {DB_CONFIG['database']}")
    print("=" * 50)

    if create_database_structure():
        print("\n🎉 Setup abgeschlossen!")
        print("\nNächste Schritte:")
        print("1. RFID-Tags importieren: python database/import_rfid_tags.py")
        print("2. Anwendung starten: python app.py")
    else:
        print("\n❌ Setup fehlgeschlagen!")
        sys.exit(1)


if __name__ == "__main__":
    main()