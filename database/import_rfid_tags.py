#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import der RFID-Tags aus authorized_tags.json in die Datenbank
Minimale Version
"""

import json
import pyodbc
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connection import get_connection
from config import AUTHORIZED_TAGS_FILE


def load_authorized_tags():
    """RFID-Tags aus JSON-Datei laden"""
    try:
        with open(AUTHORIZED_TAGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Fehler beim Laden der Datei: {e}")
        return None


def import_tags():
    """Importiert die Tags in die Datenbank"""
    tags = load_authorized_tags()
    if not tags:
        return

    print(f"\n📋 Gefundene Tags: {len(tags)}")

    conn = get_connection()
    cursor = conn.cursor()
    imported = 0
    skipped = 0

    for tag_id, tag_info in tags.items():
        try:
            # Tag-ID von Hex zu Decimal konvertieren
            epc_decimal = int(tag_id, 16)

            # Prüfen ob Tag bereits existiert
            cursor.execute("SELECT ID FROM dbo.ScannBenutzer WHERE EPC = ?", epc_decimal)
            if cursor.fetchone():
                print(f"⏭️  Tag {tag_id} bereits vorhanden")
                skipped += 1
                continue

            # Daten vorbereiten
            name = tag_info.get('name', 'Unbekannt')
            name_parts = name.split(' ', 1)
            vorname = name_parts[0] if len(name_parts) > 0 else name
            nachname = name_parts[1] if len(name_parts) > 1 else ''
            benutzer_name = name.replace(' ', '_').lower()

            # Insert
            cursor.execute("""
                           INSERT INTO dbo.ScannBenutzer
                           (Vorname, Nachname, Benutzer, BenutzerName, BenutzerPasswort,
                            Email, EPC, xStatus, xDatum, xDatumINT, xBenutzer)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                           """, (
                               vorname, nachname, benutzer_name, name, 'rfid',
                               f'{benutzer_name}@shirtful.com', epc_decimal, 0,
                               datetime.now(), int(datetime.now().strftime('%Y%m%d%H%M%S')),
                               'RFIDImport'
                           ))

            print(f"✅ Tag {tag_id} importiert: {name}")
            imported += 1

        except Exception as e:
            print(f"❌ Fehler beim Import von Tag {tag_id}: {e}")

    conn.commit()
    conn.close()

    print(f"\n📊 Import abgeschlossen:")
    print(f"   ✅ Importiert: {imported}")
    print(f"   ⏭️  Übersprungen: {skipped}")


if __name__ == "__main__":
    print("🔷 RFID-Tag Import")
    print("=" * 40)
    import_tags()