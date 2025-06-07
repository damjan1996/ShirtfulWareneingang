#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import der RFID-Tags aus authorized_tags.json in die Datenbank
"""

import json
import pyodbc
from datetime import datetime
import sys


class RFIDTagImporter:
    def __init__(self):
        # Datenbankverbindungsparameter
        self.server = '116.202.224.248'
        self.username = 'sa'
        self.password = 'YJ5C19QZ7ZUW!'
        self.database = 'RdScanner'  # Datenbankname
        self.connection = None

    def connect(self):
        """Verbindung zur Datenbank herstellen"""
        connection_attempts = [
            (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                f"TrustServerCertificate=yes;"
                f"Encrypt=no;"
            ),
            (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                f"TrustServerCertificate=yes;"
            ),
            (
                f"DRIVER={{SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )
        ]

        print(f"🔄 Stelle Verbindung zur Datenbank '{self.database}' her...")

        for i, conn_str in enumerate(connection_attempts, 1):
            try:
                self.connection = pyodbc.connect(conn_str)
                print(f"✅ Verbindung erfolgreich!")
                return True
            except pyodbc.Error as e:
                if i == len(connection_attempts):
                    print(f"❌ Verbindung fehlgeschlagen: {str(e)[:100]}...")
                continue

        return False

    def load_authorized_tags(self, filename='authorized_tags.json'):
        """RFID-Tags aus JSON-Datei laden"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Fehler beim Laden der Datei: {e}")
            return None

    def check_table_structure(self):
        """Überprüft die Struktur der ScannBenutzer-Tabelle"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           SELECT c.COLUMN_NAME,
                                  c.DATA_TYPE,
                                  c.IS_NULLABLE,
                                  c.COLUMN_DEFAULT,
                                  COLUMNPROPERTY(OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME), c.COLUMN_NAME,
                                                 'IsIdentity') as IsIdentity
                           FROM INFORMATION_SCHEMA.COLUMNS c
                           WHERE c.TABLE_NAME = 'ScannBenutzer'
                             AND c.TABLE_SCHEMA = 'dbo'
                           ORDER BY c.ORDINAL_POSITION
                           """)

            columns = cursor.fetchall()

            print("\n📋 Struktur der ScannBenutzer-Tabelle:")
            print("-" * 80)
            print(f"{'Spalte':<20} {'Typ':<15} {'NULL':<6} {'Identity':<10} {'Default'}")
            print("-" * 80)

            for col in columns:
                col_name, data_type, nullable, default, is_identity = col
                identity_str = "JA" if is_identity == 1 else "NEIN"
                null_str = "JA" if nullable == "YES" else "NEIN"
                default_str = str(default) if default else "-"

                print(f"{col_name:<20} {data_type:<15} {null_str:<6} {identity_str:<10} {default_str}")

        except Exception as e:
            print(f"❌ Fehler beim Prüfen der Tabellenstruktur: {e}")

    def check_existing_tag(self, tag_id):
        """Prüft, ob ein Tag bereits in der Datenbank existiert"""
        try:
            cursor = self.connection.cursor()
            # EPC ist decimal in der Datenbank, daher müssen wir den Hex-String konvertieren
            epc_decimal = int(tag_id, 16)
            cursor.execute("SELECT ID, BenutzerName FROM dbo.ScannBenutzer WHERE EPC = ?", epc_decimal)
            result = cursor.fetchone()
            return result is not None, result
        except Exception as e:
            print(f"❌ Fehler beim Prüfen des Tags {tag_id}: {e}")
            return False, None

    def import_tags(self):
        """Importiert die Tags in die Datenbank"""
        tags = self.load_authorized_tags()
        if not tags:
            return

        print(f"\n📋 Gefundene Tags: {len(tags)}")
        print("-" * 60)

        cursor = self.connection.cursor()
        imported = 0
        skipped = 0
        errors = 0

        for tag_id, tag_info in tags.items():
            try:
                # Prüfen ob Tag bereits existiert
                exists, existing = self.check_existing_tag(tag_id)
                if exists:
                    print(f"⏭️  Tag {tag_id} bereits vorhanden (Benutzer: {existing[1]})")
                    skipped += 1
                    continue

                # Tag-ID von Hex zu Decimal konvertieren
                epc_decimal = int(tag_id, 16)

                # Daten vorbereiten
                name = tag_info.get('name', 'Unbekannt')
                access_level = tag_info.get('access_level', 'user')

                # Namen aufteilen (falls möglich)
                name_parts = name.split(' ', 1)
                vorname = name_parts[0] if len(name_parts) > 0 else name
                nachname = name_parts[1] if len(name_parts) > 1 else ''

                # Benutzername generieren
                benutzer_name = name.replace(' ', '_').lower()

                # Aktuelles Datum
                current_date = datetime.now()
                date_int = int(current_date.strftime('%Y%m%d%H%M%S'))

                # SQL Insert - OHNE ID, da es eine IDENTITY-Spalte ist
                insert_query = """
                               INSERT INTO dbo.ScannBenutzer
                               (Vorname, Nachname, Benutzer, BenutzerName, BenutzerPasswort,
                                Email, EPC, xStatus, xDatum, xDatumINT, xBenutzer)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                               """

                cursor.execute(insert_query, (
                    vorname,
                    nachname,
                    benutzer_name,  # Benutzer
                    name,  # BenutzerName (Anzeigename)
                    'rfid',  # BenutzerPasswort (Standard)
                    f'{benutzer_name}@shirtful.com',  # Email (Platzhalter)
                    epc_decimal,  # EPC als Decimal
                    0,  # xStatus (aktiv)
                    current_date,  # xDatum
                    date_int,  # xDatumINT
                    'RFIDImport'  # xBenutzer
                ))

                print(f"✅ Tag {tag_id} importiert: {name}")
                imported += 1

            except Exception as e:
                print(f"❌ Fehler beim Import von Tag {tag_id}: {e}")
                errors += 1

        # Änderungen committen
        try:
            self.connection.commit()
            print("\n" + "=" * 60)
            print(f"📊 Import abgeschlossen:")
            print(f"   ✅ Importiert: {imported}")
            print(f"   ⏭️  Übersprungen: {skipped}")
            print(f"   ❌ Fehler: {errors}")
        except Exception as e:
            print(f"❌ Fehler beim Commit: {e}")
            self.connection.rollback()

    def list_current_users(self):
        """Listet alle aktuellen Benutzer mit RFID-Tags auf"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           SELECT ID,
                                  Vorname,
                                  Nachname,
                                  BenutzerName,
                                  CAST(EPC AS BIGINT) as EPC_Decimal
                           FROM dbo.ScannBenutzer
                           WHERE EPC IS NOT NULL
                           ORDER BY ID
                           """)

            users = cursor.fetchall()

            print("\n📋 Aktuelle Benutzer mit RFID-Tags:")
            print("-" * 80)
            print(f"{'ID':<5} {'Name':<30} {'EPC (Hex)':<15} {'EPC (Decimal)':<20}")
            print("-" * 80)

            for user in users:
                id, vorname, nachname, benutzer_name, epc_dec = user
                full_name = f"{vorname or ''} {nachname or ''}".strip() or benutzer_name
                # Decimal zu Hex konvertieren
                epc_hex = format(int(epc_dec), 'X') if epc_dec else 'N/A'
                print(f"{id:<5} {full_name:<30} {epc_hex:<15} {epc_dec:<20}")

            print(f"\n📊 Gesamt: {len(users)} Benutzer mit RFID-Tags")

        except Exception as e:
            print(f"❌ Fehler beim Abrufen der Benutzer: {e}")

    def close(self):
        """Datenbankverbindung schließen"""
        if self.connection:
            self.connection.close()
            print("\n🔒 Datenbankverbindung geschlossen")


def main():
    importer = RFIDTagImporter()

    if not importer.connect():
        print("❌ Konnte keine Verbindung zur Datenbank herstellen!")
        return

    try:
        print("\n🔷 RFID-Tag Import Tool")
        print("=" * 60)

        while True:
            print("\n📋 Optionen:")
            print("1. Tags aus authorized_tags.json importieren")
            print("2. Aktuelle Benutzer anzeigen")
            print("3. Einzelnen Tag manuell hinzufügen")
            print("4. Tabellenstruktur prüfen")
            print("5. Beenden")

            choice = input("\nWählen Sie eine Option (1-5): ").strip()

            if choice == "1":
                importer.import_tags()
            elif choice == "2":
                importer.list_current_users()
            elif choice == "3":
                # Manueller Tag-Import
                print("\n📝 Neuen RFID-Tag hinzufügen:")
                tag_hex = input("Tag-ID (Hex): ").strip().upper()
                vorname = input("Vorname: ").strip()
                nachname = input("Nachname: ").strip()

                if tag_hex and (vorname or nachname):
                    try:
                        cursor = importer.connection.cursor()
                        epc_decimal = int(tag_hex, 16)
                        benutzer_name = f"{vorname}_{nachname}".lower().replace(' ', '_')
                        current_date = datetime.now()
                        date_int = int(current_date.strftime('%Y%m%d%H%M%S'))

                        insert_query = """
                                       INSERT INTO dbo.ScannBenutzer
                                       (Vorname, Nachname, Benutzer, BenutzerName, BenutzerPasswort,
                                        Email, EPC, xStatus, xDatum, xDatumINT, xBenutzer)
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                                       """

                        cursor.execute(insert_query, (
                            vorname,
                            nachname,
                            benutzer_name,
                            f"{vorname} {nachname}",
                            'rfid',
                            f'{benutzer_name}@shirtful.com',
                            epc_decimal,
                            0,
                            current_date,
                            date_int,
                            'RFIDImport'
                        ))

                        importer.connection.commit()
                        print(f"✅ Tag {tag_hex} erfolgreich hinzugefügt!")

                    except Exception as e:
                        print(f"❌ Fehler beim Hinzufügen: {e}")
                        importer.connection.rollback()
                else:
                    print("❌ Ungültige Eingabe!")

            elif choice == "4":
                importer.check_table_structure()
            elif choice == "5":
                break
            else:
                print("❌ Ungültige Auswahl!")

    except KeyboardInterrupt:
        print("\n\n⏹️ Programm unterbrochen")
    finally:
        importer.close()


if __name__ == "__main__":
    main()