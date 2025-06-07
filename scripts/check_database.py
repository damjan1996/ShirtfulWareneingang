import pyodbc
import pandas as pd
import sys
from datetime import datetime


class DatabaseStructureAnalyzer:
    def __init__(self):
        # Datenbankverbindungsparameter
        self.server = '116.202.224.248'
        self.username = 'sa'
        self.password = 'YJ5C19QZ7ZUW!'
        self.connection = None
        self.current_database = None
        self.report_content = []  # Für Export-Funktion

    def _print_and_collect(self, text):
        """Hilfsmethode: Text sowohl anzeigen als auch für Export sammeln"""
        print(text)
        # Emojis für Textdatei entfernen
        clean_text = text.replace('📊', '').replace('📁', '').replace('📋', '').replace('📂', '').replace('🗄️', '').replace(
            '🏗️', '').replace('📦', '').replace('💾', '').replace('🔤', '').replace('🔍', '').replace('🔗', '').replace('📇',
                                                                                                                   '').replace(
            '👁️', '').replace('⚙️', '').replace('🔢', '').replace('✅', '').replace('❌', '').replace('⚠️', '').replace(
            '🔑', '').replace('ƒ', 'f')
        self.report_content.append(clean_text.strip())

    def connect(self, database=None):
        """Verbindung zur Datenbank herstellen"""

        connection_attempts = [
            # Option 1: ODBC Driver 18
            (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                    f"SERVER={self.server};"
                    + (f"DATABASE={database};" if database else "")
                    + f"UID={self.username};"
                      f"PWD={self.password};"
                      f"TrustServerCertificate=yes;"
                      f"Encrypt=no;"
            ),

            # Option 2: ODBC Driver 17
            (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={self.server};"
                    + (f"DATABASE={database};" if database else "")
                    + f"UID={self.username};"
                      f"PWD={self.password};"
                      f"TrustServerCertificate=yes;"
            ),

            # Option 3: Legacy SQL Server
            (
                    f"DRIVER={{SQL Server}};"
                    f"SERVER={self.server};"
                    + (f"DATABASE={database};" if database else "")
                    + f"UID={self.username};"
                      f"PWD={self.password};"
            )
        ]

        connection_desc = f" zu Datenbank '{database}'" if database else " zum Server"
        print(f"🔄 Stelle Verbindung{connection_desc} her...")

        for i, conn_str in enumerate(connection_attempts, 1):
            try:
                self.connection = pyodbc.connect(conn_str)
                self.current_database = database
                print(f"✅ Verbindung erfolgreich!")
                return True

            except pyodbc.Error as e:
                if i == len(connection_attempts):
                    print(f"❌ Verbindung fehlgeschlagen: {str(e)[:100]}...")
                continue

        return False

    def get_all_databases(self):
        """Alle Datenbanken auf dem Server auflisten"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           SELECT name, database_id
                           FROM sys.databases
                           WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb')
                             AND state = 0 -- nur online Datenbanken
                           ORDER BY name
                           """)

            databases = cursor.fetchall()
            print(f"\n🗄️  Verfügbare Datenbanken ({len(databases)}):")
            print("=" * 60)

            database_list = []
            for i, db in enumerate(databases, 1):
                database_name = db[0]
                database_list.append(database_name)
                print(f"  {i:2d}. 📁 {database_name}")

            return database_list

        except pyodbc.Error as e:
            print(f"❌ Fehler beim Abrufen der Datenbanken: {e}")
            return []

    def analyze_database_structure(self, database_name):
        """Komplette Struktur-Analyse einer Datenbank"""

        # Report-Content sammeln für Export
        self.report_content = []
        self.report_content.append(f"=" * 80)
        self.report_content.append(f"📊 STRUKTUR-ANALYSE: {database_name}")
        self.report_content.append(f"Erstellt am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.report_content.append("=" * 80)

        try:
            # Zu der Datenbank wechseln
            cursor = self.connection.cursor()
            cursor.execute(f"USE [{database_name}]")
            self.current_database = database_name

            print(f"\n" + "=" * 80)
            print(f"📊 STRUKTUR-ANALYSE: {database_name}")
            print("=" * 80)

            # 1. Datenbank-Informationen
            self._show_database_info(database_name)

            # 2. Schema-Übersicht
            self._show_schemas()

            # 3. Tabellen-Übersicht
            tables = self._get_all_tables_detailed()

            # 4. Detaillierte Tabellen-Struktur
            self._show_detailed_table_structures(tables)

            # 5. Beziehungen/Foreign Keys
            self._show_relationships()

            # 6. Indizes
            self._show_indexes()

            # 7. Views
            self._show_views()

            # 8. Stored Procedures
            self._show_stored_procedures()

            # 9. Funktionen
            self._show_functions()

            return True

        except Exception as e:
            error_msg = f"❌ Fehler bei der Struktur-Analyse: {e}"
            print(error_msg)
            self.report_content.append(error_msg)
            return False

    def _show_database_info(self, database_name):
        """Grundlegende Datenbank-Informationen"""
        try:
            cursor = self.connection.cursor()

            self._print_and_collect(f"\n📂 DATENBANK-INFORMATIONEN:")
            self._print_and_collect("-" * 50)

            # Größe und Dateien
            cursor.execute("""
                           SELECT name          AS FileName,
                                  physical_name AS FilePath, size * 8.0 / 1024 AS SizeMB, type_desc AS FileType
                           FROM sys.database_files
                           """)

            files = cursor.fetchall()

            total_size = 0
            for file in files:
                file_name, file_path, size_mb, file_type = file
                total_size += size_mb
                self._print_and_collect(f"  📄 {file_name} ({file_type})")
                self._print_and_collect(f"      Pfad: {file_path}")
                self._print_and_collect(f"      Größe: {size_mb:.1f} MB")

            self._print_and_collect(f"\n  💾 Gesamtgröße: {total_size:.1f} MB")

            # Kollation
            cursor.execute("SELECT DATABASEPROPERTYEX(DB_NAME(), 'Collation') AS Collation")
            collation = cursor.fetchone()[0]
            self._print_and_collect(f"  🔤 Kollation: {collation}")

        except Exception as e:
            error_msg = f"⚠️  Datenbank-Info nicht verfügbar: {e}"
            self._print_and_collect(error_msg)

    def _show_schemas(self):
        """Schema-Übersicht"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           SELECT s.name        AS SchemaName,
                                  COUNT(t.name) AS TableCount
                           FROM sys.schemas s
                                    LEFT JOIN sys.tables t ON s.schema_id = t.schema_id
                           WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
                           GROUP BY s.name
                           ORDER BY s.name
                           """)

            schemas = cursor.fetchall()

            print(f"\n🏗️  SCHEMAS:")
            print("-" * 50)
            for schema_name, table_count in schemas:
                print(f"  📦 {schema_name} ({table_count} Tabellen)")

        except Exception as e:
            print(f"⚠️  Schema-Info nicht verfügbar: {e}")

    def _get_all_tables_detailed(self):
        """Detaillierte Tabellen-Information"""
        try:
            cursor = self.connection.cursor()

            # Einfache, universell kompatible Abfrage
            cursor.execute("""
                           SELECT s.name AS SchemaName,
                                  t.name AS TableName,
                                  t.object_id
                           FROM sys.tables t
                                    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                           ORDER BY s.name, t.name
                           """)

            basic_tables = cursor.fetchall()

            self._print_and_collect(f"\n📋 TABELLEN-ÜBERSICHT ({len(basic_tables)} Tabellen):")
            self._print_and_collect("=" * 80)
            self._print_and_collect(f"{'Schema':<15} {'Tabelle':<35} {'Object ID':<12} {'Zeilen':<10}")
            self._print_and_collect("-" * 80)

            table_list = []
            total_rows = 0

            for schema, table, obj_id in basic_tables:
                # Zeilenzahl separat abfragen (sicherer)
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{table}]")
                    row_count = cursor.fetchone()[0]
                    rows_display = f"{row_count:,}"
                    total_rows += row_count
                except Exception:
                    row_count = 0
                    rows_display = "N/A"

                table_list.append({
                    'schema': schema,
                    'table': table,
                    'object_id': obj_id,
                    'rows': row_count,
                    'size_mb': 0  # Größe wird nicht abgefragt (um Kompatibilität zu gewährleisten)
                })

                self._print_and_collect(f"{schema:<15} {table:<35} {obj_id:<12} {rows_display:<10}")

            self._print_and_collect("-" * 80)
            self._print_and_collect(f"{'GESAMT':<15} {len(basic_tables)} Tabellen{'':<20} {total_rows:,} Zeilen")
            self._print_and_collect("=" * 80)

            return table_list

        except Exception as e:
            error_msg = f"❌ Fehler bei erweiteter Tabellen-Übersicht: {e}"
            self._print_and_collect(error_msg)

            # Noch einfacherer Fallback
            try:
                self._print_and_collect("\n📋 TABELLEN-ÜBERSICHT (Basis-Modus):")
                self._print_and_collect("=" * 60)

                cursor.execute("""
                               SELECT s.name, t.name, t.object_id
                               FROM sys.tables t,
                                    sys.schemas s
                               WHERE t.schema_id = s.schema_id
                               ORDER BY s.name, t.name
                               """)

                simple_tables = cursor.fetchall()
                table_list = []

                for schema, table, obj_id in simple_tables:
                    table_list.append({
                        'schema': schema,
                        'table': table,
                        'object_id': obj_id,
                        'rows': 0,
                        'size_mb': 0
                    })
                    self._print_and_collect(f"  📊 {schema}.{table} (ID: {obj_id})")

                self._print_and_collect(f"\n✅ {len(simple_tables)} Tabellen gefunden")
                return table_list

            except Exception as e2:
                error_msg2 = f"❌ Kritischer Fehler bei Tabellen-Abfrage: {e2}"
                self._print_and_collect(error_msg2)
                return []

    def _show_detailed_table_structures(self, tables):
        """Detaillierte Struktur jeder Tabelle"""

        if not tables:
            return

        self._print_and_collect(f"\n🔍 DETAILLIERTE TABELLEN-STRUKTUREN:")
        self._print_and_collect("=" * 80)

        for i, table_info in enumerate(tables, 1):
            schema = table_info['schema']
            table = table_info['table']
            full_table_name = f"{schema}.{table}"

            self._print_and_collect(f"\n📊 [{i}/{len(tables)}] {full_table_name}")
            self._print_and_collect("-" * 60)

            try:
                cursor = self.connection.cursor()

                # Spalten-Information
                cursor.execute(f"""
                    SELECT 
                        c.COLUMN_NAME,
                        c.DATA_TYPE,
                        c.CHARACTER_MAXIMUM_LENGTH,
                        c.NUMERIC_PRECISION,
                        c.NUMERIC_SCALE,
                        c.IS_NULLABLE,
                        c.COLUMN_DEFAULT,
                        CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'PK' ELSE '' END AS IsPrimaryKey
                    FROM INFORMATION_SCHEMA.COLUMNS c
                    LEFT JOIN (
                        SELECT ku.COLUMN_NAME
                        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                            ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                        WHERE tc.TABLE_NAME = '{table}' 
                        AND tc.TABLE_SCHEMA = '{schema}'
                        AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                    ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
                    WHERE c.TABLE_NAME = '{table}' 
                    AND c.TABLE_SCHEMA = '{schema}'
                    ORDER BY c.ORDINAL_POSITION
                """)

                columns = cursor.fetchall()

                self._print_and_collect(f"  📋 Spalten ({len(columns)}):")
                self._print_and_collect(f"  {'Spalte':<25} {'Typ':<20} {'Größe':<8} {'NULL':<5} {'PK':<3} {'Default'}")
                self._print_and_collect(f"  {'-' * 25} {'-' * 20} {'-' * 8} {'-' * 5} {'-' * 3} {'-' * 15}")

                for col in columns:
                    col_name, data_type, max_length, precision, scale, nullable, default, is_pk = col

                    # Typ mit Größe formatieren
                    if max_length:
                        type_display = f"{data_type}({max_length})"
                    elif precision and scale:
                        type_display = f"{data_type}({precision},{scale})"
                    elif precision:
                        type_display = f"{data_type}({precision})"
                    else:
                        type_display = data_type

                    size_display = str(max_length) if max_length else ""
                    nullable_display = "JA" if nullable == "YES" else "NEIN"
                    pk_display = "✓" if is_pk else ""
                    default_display = str(default)[:15] if default else ""

                    self._print_and_collect(
                        f"  {col_name:<25} {type_display:<20} {size_display:<8} {nullable_display:<5} {pk_display:<3} {default_display}")

                # Zeilen und Größe
                self._print_and_collect(f"\n  📊 Zeilen: {table_info['rows']:,}")
                self._print_and_collect(f"  💾 Größe: {table_info['size_mb']:.2f} MB")

            except Exception as e:
                error_msg = f"  ❌ Fehler bei {full_table_name}: {e}"
                self._print_and_collect(error_msg)

    def _show_schemas(self):
        """Schema-Übersicht"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           SELECT s.name        AS SchemaName,
                                  COUNT(t.name) AS TableCount
                           FROM sys.schemas s
                                    LEFT JOIN sys.tables t ON s.schema_id = t.schema_id
                           WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
                           GROUP BY s.name
                           ORDER BY s.name
                           """)

            schemas = cursor.fetchall()

            self._print_and_collect(f"\n🏗️  SCHEMAS:")
            self._print_and_collect("-" * 50)
            for schema_name, table_count in schemas:
                self._print_and_collect(f"  📦 {schema_name} ({table_count} Tabellen)")

        except Exception as e:
            error_msg = f"⚠️  Schema-Info nicht verfügbar: {e}"
            self._print_and_collect(error_msg)

    def _show_relationships(self):
        """Foreign Key Beziehungen"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           SELECT fk.name                           AS ForeignKeyName,
                                  tp.name                           AS ParentTable,
                                  cp.name                           AS ParentColumn,
                                  tr.name                           AS ReferencedTable,
                                  cr.name                           AS ReferencedColumn,
                                  fk.delete_referential_action_desc AS DeleteAction,
                                  fk.update_referential_action_desc AS UpdateAction
                           FROM sys.foreign_keys fk
                                    INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
                                    INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
                                    INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
                                    INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND
                                                                 fkc.parent_column_id = cp.column_id
                                    INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND
                                                                 fkc.referenced_column_id = cr.column_id
                           ORDER BY tp.name, fk.name
                           """)

            relationships = cursor.fetchall()

            if relationships:
                self._print_and_collect(f"\n🔗 FOREIGN KEY BEZIEHUNGEN ({len(relationships)}):")
                self._print_and_collect("-" * 80)

                for rel in relationships:
                    fk_name, parent_table, parent_col, ref_table, ref_col, delete_action, update_action = rel
                    self._print_and_collect(f"  🔑 {fk_name}")
                    self._print_and_collect(f"      {parent_table}.{parent_col} → {ref_table}.{ref_col}")
                    self._print_and_collect(f"      Delete: {delete_action}, Update: {update_action}")
                    self._print_and_collect("")
            else:
                self._print_and_collect(f"\n🔗 FOREIGN KEY BEZIEHUNGEN: Keine gefunden")

        except Exception as e:
            error_msg = f"⚠️  Beziehungen nicht verfügbar: {e}"
            self._print_and_collect(error_msg)

    def _show_indexes(self):
        """Index-Übersicht"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           SELECT t.name                   AS TableName,
                                  i.name                   AS IndexName,
                                  i.type_desc              AS IndexType,
                                  i.is_unique              AS IsUnique,
                                  STRING_AGG(c.name, ', ') AS Columns
                           FROM sys.indexes i
                                    INNER JOIN sys.tables t ON i.object_id = t.object_id
                                    INNER JOIN sys.index_columns ic
                                               ON i.object_id = ic.object_id AND i.index_id = ic.index_id
                                    INNER JOIN sys.columns c
                                               ON ic.object_id = c.object_id AND ic.column_id = c.column_id
                           WHERE i.name IS NOT NULL
                           GROUP BY t.name, i.name, i.type_desc, i.is_unique
                           ORDER BY t.name, i.name
                           """)

            indexes = cursor.fetchall()

            if indexes:
                self._print_and_collect(f"\n📇 INDIZES ({len(indexes)}):")
                self._print_and_collect("-" * 80)

                current_table = ""
                for idx in indexes:
                    table_name, index_name, index_type, is_unique, columns = idx

                    if table_name != current_table:
                        if current_table:
                            self._print_and_collect("")
                        self._print_and_collect(f"  📊 {table_name}:")
                        current_table = table_name

                    unique_marker = " (UNIQUE)" if is_unique else ""
                    self._print_and_collect(f"    🔍 {index_name} ({index_type}){unique_marker}")
                    self._print_and_collect(f"        Spalten: {columns}")
            else:
                self._print_and_collect(f"\n📇 INDIZES: Keine gefunden")

        except Exception as e:
            error_msg = f"⚠️  Index-Info nicht verfügbar: {e}"
            self._print_and_collect(error_msg)

    def _show_views(self):
        """Views anzeigen"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           SELECT s.name AS SchemaName,
                                  v.name AS ViewName
                           FROM sys.views v
                                    INNER JOIN sys.schemas s ON v.schema_id = s.schema_id
                           ORDER BY s.name, v.name
                           """)

            views = cursor.fetchall()

            if views:
                self._print_and_collect(f"\n👁️  VIEWS ({len(views)}):")
                self._print_and_collect("-" * 50)

                for schema, view in views:
                    self._print_and_collect(f"  📄 {schema}.{view}")
            else:
                self._print_and_collect(f"\n👁️  VIEWS: Keine gefunden")

        except Exception as e:
            error_msg = f"⚠️  View-Info nicht verfügbar: {e}"
            self._print_and_collect(error_msg)

    def _show_stored_procedures(self):
        """Stored Procedures anzeigen"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           SELECT s.name        AS SchemaName,
                                  p.name        AS ProcedureName,
                                  p.create_date AS CreateDate,
                                  p.modify_date AS ModifyDate
                           FROM sys.procedures p
                                    INNER JOIN sys.schemas s ON p.schema_id = s.schema_id
                           ORDER BY s.name, p.name
                           """)

            procedures = cursor.fetchall()

            if procedures:
                self._print_and_collect(f"\n⚙️  STORED PROCEDURES ({len(procedures)}):")
                self._print_and_collect("-" * 60)

                for schema, proc, create_date, modify_date in procedures:
                    self._print_and_collect(f"  🔧 {schema}.{proc}")
                    self._print_and_collect(f"      Erstellt: {create_date}, Geändert: {modify_date}")
            else:
                self._print_and_collect(f"\n⚙️  STORED PROCEDURES: Keine gefunden")

        except Exception as e:
            error_msg = f"⚠️  Procedure-Info nicht verfügbar: {e}"
            self._print_and_collect(error_msg)

    def _show_functions(self):
        """Funktionen anzeigen"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           SELECT s.name      AS SchemaName,
                                  o.name      AS FunctionName,
                                  o.type_desc AS FunctionType
                           FROM sys.objects o
                                    INNER JOIN sys.schemas s ON o.schema_id = s.schema_id
                           WHERE o.type IN ('FN', 'IF', 'TF') -- Scalar, Inline Table-valued, Table-valued
                           ORDER BY s.name, o.name
                           """)

            functions = cursor.fetchall()

            if functions:
                self._print_and_collect(f"\n🔢 FUNKTIONEN ({len(functions)}):")
                self._print_and_collect("-" * 60)

                for schema, func, func_type in functions:
                    self._print_and_collect(f"  f {schema}.{func} ({func_type})")
            else:
                self._print_and_collect(f"\n🔢 FUNKTIONEN: Keine gefunden")

        except Exception as e:
            error_msg = f"⚠️  Funktions-Info nicht verfügbar: {e}"
            self._print_and_collect(error_msg)

    def export_structure_report(self, database_name):
        """Struktur-Report als Datei exportieren"""
        try:
            import os

            # Export-Verzeichnis erstellen
            export_dir = "database_reports"
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)

            # Dateiname generieren
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{export_dir}/database_structure_{database_name}_{timestamp}.txt"

            # Report-Inhalt in Datei schreiben
            with open(filename, 'w', encoding='utf-8') as f:
                # Header
                f.write("=" * 80 + "\n")
                f.write(f"DATENBANK-STRUKTUR-REPORT: {database_name}\n")
                f.write(f"Erstellt am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Server: {self.server}\n")
                f.write("=" * 80 + "\n\n")

                # Gesammelten Content schreiben
                for line in self.report_content:
                    f.write(line + "\n")

                # Footer
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"Report Ende - Generiert von Database Structure Analyzer\n")
                f.write(f"Datei: {filename}\n")
                f.write("=" * 80 + "\n")

            # Dateigröße ermitteln
            file_size = os.path.getsize(filename)
            size_kb = file_size / 1024

            print(f"\n💾 Struktur-Report erfolgreich exportiert!")
            print(f"   📁 Datei: {filename}")
            print(f"   📊 Größe: {size_kb:.1f} KB")
            print(f"   📋 Zeilen: {len(self.report_content)}")
            print(f"   ⏰ Zeit: {datetime.now().strftime('%H:%M:%S')}")

            return filename

        except Exception as e:
            print(f"❌ Fehler beim Export: {e}")
            return None

    def close(self):
        """Datenbankverbindung schließen"""
        if self.connection:
            self.connection.close()
            print("🔒 Datenbankverbindung geschlossen")


def main():
    analyzer = DatabaseStructureAnalyzer()

    # Verbindung zum Server herstellen
    if not analyzer.connect():
        return

    try:
        print("\n" + "=" * 70)
        print("🔍 DATENBANK-STRUKTUR-ANALYSATOR")
        print("=" * 70)

        while True:
            # Alle Datenbanken anzeigen
            databases = analyzer.get_all_databases()

            if not databases:
                print("❌ Keine Datenbanken gefunden!")
                break

            print(f"\n" + "-" * 60)
            print("📋 OPTIONEN:")
            print("1️⃣  Datenbank auswählen und analysieren")
            print("2️⃣  Datenbanken neu laden")
            print("3️⃣  Beenden")
            print("-" * 60)

            choice = input("\nWählen Sie eine Option (1-3): ").strip()

            if choice == "1":
                try:
                    db_num = int(input(f"\nDatenbank auswählen (1-{len(databases)}): ")) - 1
                    if 0 <= db_num < len(databases):
                        selected_db = databases[db_num]

                        print(f"\n🔍 Analysiere Struktur von: {selected_db}")
                        print("⏱️  Dies kann einen Moment dauern...")

                        if analyzer.analyze_database_structure(selected_db):
                            print(f"\n✅ Struktur-Analyse von {selected_db} abgeschlossen!")

                            export_choice = input("\nStruktur-Report als Datei exportieren? (j/n): ").lower()
                            if export_choice == 'j':
                                analyzer.export_structure_report(selected_db)

                        input("\n📋 Drücken Sie Enter um fortzufahren...")
                    else:
                        print("❌ Ungültige Auswahl!")

                except ValueError:
                    print("❌ Bitte eine gültige Zahl eingeben!")

            elif choice == "2":
                print("🔄 Lade Datenbanken neu...")
                continue

            elif choice == "3":
                break

            else:
                print("❌ Ungültige Option! Bitte wählen Sie 1-3.")

    except KeyboardInterrupt:
        print("\n\n⏹️  Programm unterbrochen")

    finally:
        analyzer.close()


if __name__ == "__main__":
    print("🔍 Prüfe System-Voraussetzungen...")

    try:
        import pyodbc
        import pandas

        print("✅ Alle Python-Pakete installiert!")
    except ImportError as e:
        print("❌ Fehlende Pakete installieren:")
        print("   pip install pyodbc pandas")
        sys.exit(1)

    print("-" * 60)
    main()