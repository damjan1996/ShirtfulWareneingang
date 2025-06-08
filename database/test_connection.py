#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test der Datenbankverbindung
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connection import get_connection, test_connection
from config import DB_CONFIG


def main():
    """Teste Datenbankverbindung"""
    print("🔍 Teste Datenbankverbindung...")
    print(f"   Server: {DB_CONFIG['server']}")
    print(f"   Datenbank: {DB_CONFIG['database']}")
    print(f"   Benutzer: {DB_CONFIG['user']}")
    print("-" * 40)

    if test_connection():
        print("✅ Verbindung erfolgreich!")

        # Teste Abfrage
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Teste ScannBenutzer Tabelle
            cursor.execute("SELECT COUNT(*) FROM dbo.ScannBenutzer")
            count = cursor.fetchone()[0]
            print(f"📊 ScannBenutzer: {count} Einträge")

            # Teste Sessions Tabelle
            cursor.execute("SELECT COUNT(*) FROM dbo.Sessions")
            count = cursor.fetchone()[0]
            print(f"📊 Sessions: {count} Einträge")

            # Teste QrScans Tabelle
            cursor.execute("SELECT COUNT(*) FROM dbo.QrScans")
            count = cursor.fetchone()[0]
            print(f"📊 QrScans: {count} Einträge")

            conn.close()

        except Exception as e:
            print(f"❌ Fehler bei Abfrage: {e}")
    else:
        print("❌ Verbindung fehlgeschlagen!")


if __name__ == "__main__":
    main()