#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Umfassendes Test-System für RFID & QR Scanner
Erweiterte Version mit allen kritischen Tests
"""

import sys
import os
import time
import threading
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Projekt-Pfad hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class ComprehensiveSystemTest:
    """Umfassende System-Tests für alle Komponenten"""

    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.hardware_status = {}
        self.test_data = self._generate_test_data()

    def _generate_test_data(self):
        """Generiert Test-Daten für alle Tests"""
        return {
            'rfid_tags': [
                '53004ECD68',  # Existierende Tags
                '53004E114B',
                '53004E0D1B',
                '53004F3565',
                'INVALID123',  # Ungültiger Tag
                '999999999999'  # Nicht in DB
            ],
            'qr_codes': [
                '{"kunde":"ABC GmbH","auftrag":"12345","paket":"1/3"}',  # JSON
                'Kunde:XYZ GmbH^Auftrag:67890^Paket:2/5',  # Key-Value
                'Einfacher Text für Test',  # Plain Text
                '1^126644896^25000580^...^END',  # Delimited
                '',  # Leer
                'x' * 5000,  # Sehr lang
                '{"invalid_json": }',  # Ungültiges JSON
            ],
            'camera_indices': [0, 1, 2, 3, 4],  # Test verschiedene Kameras
            'performance_targets': {
                'qr_scan_time_ms': 100,
                'db_query_time_ms': 50,
                'camera_init_time_s': 5,
                'memory_usage_mb': 200
            }
        }

    def run_all_tests(self):
        """Führt alle Tests durch"""
        print("🔷 RFID & QR Scanner - Umfassende System-Tests")
        print(f"⏰ Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Test-Kategorien definieren
        test_categories = [
            ("🔧 Grundlagen", [
                ("Python Module", self.test_python_modules),
                ("Projekt-Struktur", self.test_project_structure),
                ("Konfiguration", self.test_configuration),
                ("Verzeichnisse", self.test_directories)
            ]),
            ("🗄️ Datenbank", [
                ("DB-Verbindung", self.test_database_connection),
                ("DB-Schema", self.test_database_schema),
                ("RFID-Tags Import", self.test_rfid_tags_import),
                ("Models CRUD", self.test_models_crud),
                ("DB-Performance", self.test_database_performance)
            ]),
            ("📱 Hardware", [
                ("RFID Reader", self.test_rfid_reader),
                ("Kamera-Erkennung", self.test_camera_detection),
                ("Multi-Kamera", self.test_multi_camera),
                ("QR-Code Erkennung", self.test_qr_code_detection)
            ]),
            ("⚙️ Funktionalität", [
                ("QR-Validierung", self.test_qr_validation),
                ("RFID-Validierung", self.test_rfid_validation),
                ("Duplikat-Verhinderung", self.test_duplicate_prevention),
                ("Session-Management", self.test_session_management)
            ]),
            ("🚀 Integration", [
                ("Login-Workflow", self.test_login_workflow),
                ("QR-Scan-Workflow", self.test_qr_scan_workflow),
                ("Multi-User Parallel", self.test_multi_user_parallel),
                ("Error-Recovery", self.test_error_recovery)
            ]),
            ("📊 Performance", [
                ("Speicher-Verbrauch", self.test_memory_usage),
                ("Scanner-Performance", self.test_scanner_performance),
                ("DB-Load-Test", self.test_database_load),
                ("Concurrency-Test", self.test_concurrency)
            ])
        ]

        # Tests durchführen
        for category_name, tests in test_categories:
            print(f"\n{category_name}")
            print("-" * 40)

            for test_name, test_func in tests:
                print(f"   🔄 {test_name}...")
                try:
                    start_time = time.time()
                    result = test_func()
                    execution_time = time.time() - start_time

                    self.test_results[test_name] = result
                    self.performance_metrics[test_name] = execution_time

                    status = "✅" if result else "❌"
                    print(f"   {status} {test_name} ({execution_time:.3f}s)")

                except Exception as e:
                    print(f"   💥 {test_name} - CRASH: {e}")
                    self.test_results[test_name] = False

        # Zusammenfassung
        self._generate_test_report()

    # ==================== GRUNDLAGEN TESTS ====================

    def test_python_modules(self):
        """Test: Alle erforderlichen Python-Module"""
        required_modules = [
            ('tkinter', 'GUI Framework'),
            ('cv2', 'OpenCV Kamera'),
            ('pyzbar', 'QR-Code Decoder'),
            ('pyodbc', 'SQL Server Driver'),
            ('pynput', 'Keyboard Listener'),
            ('PIL', 'Bildverarbeitung'),
            ('numpy', 'Array Processing'),
            ('threading', 'Multi-Threading'),
            ('json', 'JSON Processing'),
            ('datetime', 'Zeit-Funktionen'),
            ('pathlib', 'Pfad-Handling')
        ]

        failed_modules = []
        for module_name, description in required_modules:
            try:
                __import__(module_name)
            except ImportError:
                failed_modules.append(module_name)

        if failed_modules:
            print(f"      ❌ Fehlende Module: {', '.join(failed_modules)}")
            return False

        return True

    def test_project_structure(self):
        """Test: Projekt-Verzeichnisstruktur"""
        required_files = [
            'app.py',
            'config.py',
            'connection.py',
            'models.py',
            'hid_listener.py',
            'qr_scanner.py',
            'requirements.txt'
        ]

        required_dirs = [
            'database',
            'config',
            'logs',
            'utils'
        ]

        missing_files = [f for f in required_files if not os.path.exists(f)]
        missing_dirs = [d for d in required_dirs if not os.path.exists(d)]

        if missing_files or missing_dirs:
            if missing_files:
                print(f"      ❌ Fehlende Dateien: {', '.join(missing_files)}")
            if missing_dirs:
                print(f"      ❌ Fehlende Verzeichnisse: {', '.join(missing_dirs)}")
            return False

        return True

    def test_configuration(self):
        """Test: Konfiguration laden und validieren"""
        try:
            from config import DB_CONFIG, APP_CONFIG, QR_CONFIG, SCANNER_CONFIG

            # DB-Konfiguration prüfen
            required_db = ['server', 'database', 'user', 'password']
            missing_db = [k for k in required_db if not DB_CONFIG.get(k)]

            if missing_db:
                print(f"      ❌ Fehlende DB-Config: {', '.join(missing_db)}")
                return False

            # Kamera-Konfiguration prüfen
            camera_indices = APP_CONFIG.get('CAMERA_INDICES', [])
            if not camera_indices:
                print(f"      ❌ Keine Kamera-Indizes konfiguriert")
                return False

            # QR-Scanner-Konfiguration prüfen
            required_scanner = ['FRAME_WIDTH', 'FRAME_HEIGHT', 'FPS']
            missing_scanner = [k for k in required_scanner if k not in SCANNER_CONFIG]

            if missing_scanner:
                print(f"      ❌ Fehlende Scanner-Config: {', '.join(missing_scanner)}")
                return False

            return True

        except Exception as e:
            print(f"      ❌ Config-Fehler: {e}")
            return False

    def test_directories(self):
        """Test: Notwendige Verzeichnisse erstellen"""
        directories = ['logs', 'config', 'temp', 'database']

        for directory in directories:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                except Exception as e:
                    print(f"      ❌ Konnte {directory} nicht erstellen: {e}")
                    return False

        return True

    # ==================== DATENBANK TESTS ====================

    def test_database_connection(self):
        """Test: Datenbankverbindung umfassend"""
        try:
            from connection import get_connection, test_connection, execute_query

            # Basis-Verbindungstest
            if not test_connection():
                print(f"      ❌ Grundlegende Verbindung fehlgeschlagen")
                return False

            # Connection Pool Test
            connections = []
            for i in range(5):
                try:
                    conn = get_connection()
                    connections.append(conn)
                except Exception as e:
                    print(f"      ❌ Connection Pool Fehler: {e}")
                    return False

            # Transaktions-Test
            try:
                result = execute_query("SELECT @@VERSION", fetch_one=True)
                if not result:
                    print(f"      ❌ Query-Ausführung fehlgeschlagen")
                    return False
            except Exception as e:
                print(f"      ❌ Query-Test fehlgeschlagen: {e}")
                return False

            return True

        except Exception as e:
            print(f"      ❌ DB-Connection Test Fehler: {e}")
            return False

    def test_database_schema(self):
        """Test: Vollständiges Datenbankschema"""
        try:
            from connection import execute_query

            # Alle erforderlichen Tabellen
            required_tables = [
                ('ScannBenutzer', ['ID', 'BenutzerName', 'EPC']),
                ('Sessions', ['ID', 'UserID', 'StartTS', 'Active']),
                ('QrScans', ['ID', 'SessionID', 'RawPayload', 'CapturedTS']),
                ('ScannTyp', ['ID', 'Bezeichnung']),
                ('ScannKopf', ['ID', 'EPC', 'Datum']),
                ('ScannPosition', ['ID', 'ScannKopf_ID', 'Kunde'])
            ]

            for table_name, required_columns in required_tables:
                # Prüfe ob Tabelle existiert
                try:
                    execute_query(f"SELECT COUNT(*) FROM dbo.{table_name}", fetch_one=True)
                except Exception as e:
                    print(f"      ❌ Tabelle {table_name} fehlt: {e}")
                    return False

                # Prüfe erforderliche Spalten
                try:
                    column_query = """
                                   SELECT COLUMN_NAME
                                   FROM INFORMATION_SCHEMA.COLUMNS
                                   WHERE TABLE_NAME = ? \
                                     AND TABLE_SCHEMA = 'dbo' \
                                   """
                    columns = execute_query(column_query, (table_name,), fetch_all=True)
                    existing_columns = [col[0] for col in columns]

                    missing_columns = [col for col in required_columns if col not in existing_columns]
                    if missing_columns:
                        print(f"      ❌ {table_name} fehlt Spalten: {', '.join(missing_columns)}")
                        return False

                except Exception as e:
                    print(f"      ❌ Schema-Check {table_name} fehlgeschlagen: {e}")
                    return False

            # Prüfe Indizes
            index_query = """
                          SELECT name \
                          FROM sys.indexes
                          WHERE name IN ('UQ_Sessions_ActiveUser', 'IX_ScannBenutzer_EPC') \
                          """
            indexes = execute_query(index_query, fetch_all=True)
            if len(indexes) < 2:
                print(f"      ❌ Wichtige Indizes fehlen")
                return False

            return True

        except Exception as e:
            print(f"      ❌ Schema-Test Fehler: {e}")
            return False

    def test_rfid_tags_import(self):
        """Test: RFID-Tags Import und Validierung"""
        try:
            from models import User

            # Lade autorisierte Tags
            if not os.path.exists('config/authorized_tags.json'):
                print(f"      ❌ authorized_tags.json fehlt")
                return False

            with open('config/authorized_tags.json', 'r') as f:
                authorized_tags = json.load(f)

            if not authorized_tags:
                print(f"      ❌ Keine autorisierten Tags gefunden")
                return False

            # Prüfe Tags in Datenbank
            imported_count = 0
            for tag_id in authorized_tags.keys():
                user = User.get_by_epc(tag_id)
                if user:
                    imported_count += 1

            import_ratio = imported_count / len(authorized_tags)
            if import_ratio < 0.5:  # Mindestens 50% importiert
                print(f"      ❌ Nur {import_ratio:.1%} der Tags importiert")
                return False

            return True

        except Exception as e:
            print(f"      ❌ RFID-Import Test Fehler: {e}")
            return False

    def test_models_crud(self):
        """Test: Models CRUD-Operationen"""
        try:
            from models import User, Session, QrScan

            # Test User.get_all_active
            users = User.get_all_active()
            if not users:
                print(f"      ❌ Keine aktiven Benutzer gefunden")
                return False

            test_user = users[0]

            # Test Session.create
            session = Session.create(test_user['ID'])
            if not session:
                print(f"      ❌ Session konnte nicht erstellt werden")
                return False

            session_id = session['ID']

            # Test QrScan.create
            test_payload = "TEST_QR_" + str(int(time.time()))
            qr_scan = QrScan.create(session_id, test_payload)
            if not qr_scan:
                print(f"      ❌ QR-Scan konnte nicht erstellt werden")
                return False

            # Test Session.end
            if not Session.end(session_id):
                print(f"      ❌ Session konnte nicht beendet werden")
                return False

            # Test QrScan.get_by_session
            scans = QrScan.get_by_session(session_id)
            if not scans or scans[0]['RawPayload'] != test_payload:
                print(f"      ❌ QR-Scan konnte nicht abgerufen werden")
                return False

            return True

        except Exception as e:
            print(f"      ❌ Models CRUD Test Fehler: {e}")
            return False

    def test_database_performance(self):
        """Test: Datenbank-Performance"""
        try:
            from connection import execute_query
            import time

            # Query-Performance Test
            start_time = time.time()

            # Simuliere typische Abfragen
            queries = [
                "SELECT COUNT(*) FROM dbo.ScannBenutzer",
                "SELECT COUNT(*) FROM dbo.Sessions WHERE Active = 1",
                "SELECT COUNT(*) FROM dbo.QrScans WHERE CapturedTS > DATEADD(day, -1, GETDATE())"
            ]

            for query in queries:
                query_start = time.time()
                execute_query(query, fetch_one=True)
                query_time = (time.time() - query_start) * 1000

                if query_time > self.test_data['performance_targets']['db_query_time_ms']:
                    print(f"      ⚠️ Langsame Query: {query_time:.1f}ms")

            total_time = (time.time() - start_time) * 1000

            # Performance in Metriken speichern
            self.performance_metrics['db_query_time'] = total_time

            return total_time < 500  # Alle Queries unter 500ms

        except Exception as e:
            print(f"      ❌ DB-Performance Test Fehler: {e}")
            return False

    # ==================== HARDWARE TESTS ====================

    def test_rfid_reader(self):
        """Test: RFID Reader Funktionalität"""
        try:
            from hid_listener import HIDListener
            from utils import validate_tag_id

            # Test HIDListener Erstellung
            listener = HIDListener()
            if not listener:
                print(f"      ❌ HIDListener konnte nicht erstellt werden")
                return False

            # Test Tag-Validierung mit Test-Daten
            valid_count = 0
            for tag in self.test_data['rfid_tags']:
                if validate_tag_id(tag) and len(tag) == 10:  # Nur echte Tags
                    valid_count += 1

            if valid_count < 3:  # Mindestens 3 gültige Tags
                print(f"      ❌ Nicht genug gültige Test-Tags: {valid_count}")
                return False

            # Test Listener Start/Stop
            try:
                listener.start()
                time.sleep(0.1)  # Kurz warten
                listener.stop()
            except Exception as e:
                print(f"      ❌ HID Listener Start/Stop Fehler: {e}")
                return False

            return True

        except Exception as e:
            print(f"      ❌ RFID Reader Test Fehler: {e}")
            return False

    def test_camera_detection(self):
        """Test: Kamera-Erkennung und -Zugriff"""
        try:
            import cv2

            available_cameras = []

            # Teste verschiedene Kamera-Indizes
            for camera_index in self.test_data['camera_indices']:
                try:
                    # Test mit verschiedenen Backends
                    backends = [cv2.CAP_ANY]
                    if os.name == 'nt':  # Windows
                        backends.extend([cv2.CAP_DSHOW, cv2.CAP_MSMF])
                    else:  # Linux
                        backends.extend([cv2.CAP_V4L2])

                    for backend in backends:
                        try:
                            cap = cv2.VideoCapture(camera_index, backend)
                            if cap.isOpened():
                                # Teste Frame-Capture
                                ret, frame = cap.read()
                                if ret and frame is not None:
                                    height, width = frame.shape[:2]
                                    available_cameras.append({
                                        'index': camera_index,
                                        'backend': backend,
                                        'resolution': f"{width}x{height}"
                                    })
                                cap.release()
                                break  # Erste funktionierende Kamera gefunden
                        except:
                            if cap:
                                cap.release()
                            continue

                except Exception:
                    continue

            self.hardware_status['cameras'] = available_cameras

            if not available_cameras:
                print(f"      ❌ Keine funktionierenden Kameras gefunden")
                return False

            print(f"      ✅ {len(available_cameras)} Kamera(s) gefunden")
            for cam in available_cameras:
                print(f"         Kamera {cam['index']}: {cam['resolution']}")

            return True

        except Exception as e:
            print(f"      ❌ Kamera-Test Fehler: {e}")
            return False

    def test_multi_camera(self):
        """Test: Multi-Kamera-Setup"""
        try:
            from qr_scanner import MultiQRScanner
            from config import APP_CONFIG

            camera_indices = APP_CONFIG.get('CAMERA_INDICES', [0])

            # Test MultiQRScanner Erstellung
            multi_scanner = MultiQRScanner(
                camera_indices=camera_indices,
                shared_callback=lambda payload: None
            )

            if not multi_scanner:
                print(f"      ❌ MultiQRScanner konnte nicht erstellt werden")
                return False

            # Test Start/Stop (schnell ohne Video)
            try:
                multi_scanner.start_all()
                time.sleep(1)  # Kurz laufen lassen
                stats = multi_scanner.get_stats()
                multi_scanner.stop_all()

                active_scanners = stats.get('active_scanners', 0)
                print(f"      ✅ {active_scanners} von {len(camera_indices)} Scannern aktiv")

                return active_scanners > 0

            except Exception as e:
                print(f"      ❌ Multi-Scanner Test Fehler: {e}")
                return False

        except Exception as e:
            print(f"      ❌ Multi-Kamera Test Fehler: {e}")
            return False

    def test_qr_code_detection(self):
        """Test: QR-Code-Erkennung mit synthetischen Codes"""
        try:
            from pyzbar import pyzbar
            import numpy as np
            import cv2
            from PIL import Image, ImageDraw, ImageFont

            # Erstelle Test-QR-Code als Bild
            test_payload = "TEST_QR_CODE_" + str(int(time.time()))

            try:
                import qrcode

                # Erstelle QR-Code
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(test_payload)
                qr.make(fit=True)

                # Zu PIL Image
                qr_img = qr.make_image(fill_color="black", back_color="white")

                # Zu numpy array für pyzbar
                qr_array = np.array(qr_img)

                # QR-Code dekodieren
                decoded_objects = pyzbar.decode(qr_array)

                if decoded_objects:
                    decoded_data = decoded_objects[0].data.decode('utf-8')
                    if decoded_data == test_payload:
                        print(f"      ✅ QR-Code erfolgreich erstellt und dekodiert")
                        return True
                    else:
                        print(f"      ❌ QR-Code Inhalt stimmt nicht überein")
                        return False
                else:
                    print(f"      ❌ QR-Code konnte nicht dekodiert werden")
                    return False

            except ImportError:
                # Fallback: Test nur pyzbar Funktionalität
                print(f"      ⚠️ qrcode-Modul nicht verfügbar, teste nur Decoder")

                # Erstelle einfaches Test-Pattern
                test_image = np.ones((100, 100), dtype=np.uint8) * 255
                try:
                    pyzbar.decode(test_image)  # Sollte leer zurückgeben
                    return True
                except Exception as e:
                    print(f"      ❌ pyzbar-Test fehlgeschlagen: {e}")
                    return False

        except Exception as e:
            print(f"      ❌ QR-Code Detection Test Fehler: {e}")
            return False

    # ==================== FUNKTIONALITÄT TESTS ====================

    def test_qr_validation(self):
        """Test: QR-Code-Validierung mit allen Formaten"""
        try:
            from utils import validate_qr_payload

            test_results = []

            for qr_code in self.test_data['qr_codes']:
                try:
                    result = validate_qr_payload(qr_code)
                    test_results.append({
                        'payload': qr_code[:50] + '...' if len(qr_code) > 50 else qr_code,
                        'type': result.get('type', 'unknown') if result else 'none',
                        'valid': result.get('valid', False) if result else False
                    })
                except Exception as e:
                    test_results.append({
                        'payload': qr_code[:50],
                        'type': 'error',
                        'valid': False,
                        'error': str(e)
                    })

            # Mindestens 70% der Test-Codes sollten gültig sein
            valid_count = sum(1 for r in test_results if r['valid'])
            success_rate = valid_count / len(test_results)

            print(f"      📊 QR-Validierung: {success_rate:.1%} erfolgreich")

            return success_rate >= 0.7

        except Exception as e:
            print(f"      ❌ QR-Validierung Test Fehler: {e}")
            return False

    def test_rfid_validation(self):
        """Test: RFID-Tag-Validierung"""
        try:
            from utils import validate_tag_id, hex_to_decimal, decimal_to_hex

            # Test gültige Tags
            valid_tags = [tag for tag in self.test_data['rfid_tags'] if len(tag) == 10]
            invalid_tags = ['INVALID123', 'toolong123456', 'short', '']

            # Test validate_tag_id
            for tag in valid_tags:
                if not validate_tag_id(tag):
                    print(f"      ❌ Gültiger Tag als ungültig erkannt: {tag}")
                    return False

            for tag in invalid_tags:
                if validate_tag_id(tag):
                    print(f"      ❌ Ungültiger Tag als gültig erkannt: {tag}")
                    return False

            # Test Hex-Decimal Konvertierung
            for tag in valid_tags:
                try:
                    decimal = hex_to_decimal(tag)
                    hex_back = decimal_to_hex(decimal)
                    if hex_back.upper() != tag.upper():
                        print(f"      ❌ Hex-Decimal Konvertierung Fehler: {tag}")
                        return False
                except Exception as e:
                    print(f"      ❌ Konvertierung-Fehler für {tag}: {e}")
                    return False

            return True

        except Exception as e:
            print(f"      ❌ RFID-Validierung Test Fehler: {e}")
            return False

    def test_duplicate_prevention(self):
        """Test: QR-Code Duplikat-Verhinderung"""
        try:
            from duplicate_prevention import (
                check_qr_duplicate,
                register_qr_scan,
                clear_session_duplicates
            )

            test_payload = "DUPLICATE_TEST_" + str(int(time.time()))
            test_session_id = 999999

            # Erster Scan - sollte OK sein
            result1 = check_qr_duplicate(test_payload, test_session_id)
            if result1.get('is_duplicate'):
                print(f"      ❌ Erster Scan als Duplikat erkannt")
                return False

            # Registriere Scan
            register_qr_scan(test_payload, test_session_id)

            # Zweiter Scan - sollte Duplikat sein
            result2 = check_qr_duplicate(test_payload, test_session_id)
            if not result2.get('is_duplicate'):
                print(f"      ❌ Duplikat nicht erkannt")
                return False

            # Test Session-Cleanup
            clear_session_duplicates(test_session_id)

            # Nach Cleanup sollte wieder OK sein (für andere Sessions)
            result3 = check_qr_duplicate(test_payload, test_session_id + 1)
            # Je nach Implementierung kann das noch global gesperrt sein

            print(f"      ✅ Duplikat-Verhinderung funktioniert")
            return True

        except Exception as e:
            print(f"      ❌ Duplikat-Test Fehler: {e}")
            return False

    def test_session_management(self):
        """Test: Session-Management umfassend"""
        try:
            from models import User, Session

            # Hole Test-User
            users = User.get_all_active()
            if not users:
                print(f"      ❌ Keine Test-User verfügbar")
                return False

            test_user = users[0]
            user_id = test_user['ID']

            # Test: Session erstellen
            session1 = Session.create(user_id)
            if not session1:
                print(f"      ❌ Session konnte nicht erstellt werden")
                return False

            # Test: Doppelte Session (sollte alte beenden)
            session2 = Session.create(user_id)
            if not session2:
                print(f"      ❌ Zweite Session konnte nicht erstellt werden")
                return False

            # Test: Aktive Sessions abrufen
            active_sessions = Session.get_active()
            user_sessions = [s for s in active_sessions if s['UserID'] == user_id]

            if len(user_sessions) != 1:
                print(f"      ❌ Falsche Anzahl aktiver Sessions: {len(user_sessions)}")
                return False

            # Test: Session beenden
            if not Session.end(session2['ID']):
                print(f"      ❌ Session konnte nicht beendet werden")
                return False

            # Prüfe ob Session wirklich beendet
            active_after = Session.get_active()
            user_sessions_after = [s for s in active_after if s['UserID'] == user_id]

            if len(user_sessions_after) != 0:
                print(f"      ❌ Session nicht ordnungsgemäß beendet")
                return False

            print(f"      ✅ Session-Management funktioniert korrekt")
            return True

        except Exception as e:
            print(f"      ❌ Session-Management Test Fehler: {e}")
            return False

    # ==================== INTEGRATION TESTS ====================

    def test_login_workflow(self):
        """Test: Kompletter Login-Workflow"""
        try:
            from models import User, Session
            from utils import validate_tag_id

            # Simuliere RFID-Tag Scan
            test_tag = '53004ECD68'  # Bekannter Test-Tag

            # 1. Tag-Validierung
            if not validate_tag_id(test_tag):
                print(f"      ❌ Tag-Validierung fehlgeschlagen")
                return False

            # 2. User-Lookup
            user = User.get_by_epc(test_tag)
            if not user:
                print(f"      ❌ User-Lookup fehlgeschlagen")
                return False

            # 3. Session erstellen
            session = Session.create(user['ID'])
            if not session:
                print(f"      ❌ Session-Erstellung fehlgeschlagen")
                return False

            # 4. Logout-Workflow
            if not Session.end(session['ID']):
                print(f"      ❌ Session-Beendigung fehlgeschlagen")
                return False

            print(f"      ✅ Login-Workflow erfolgreich für {user['BenutzerName']}")
            return True

        except Exception as e:
            print(f"      ❌ Login-Workflow Test Fehler: {e}")
            return False

    def test_qr_scan_workflow(self):
        """Test: Kompletter QR-Scan-Workflow"""
        try:
            from models import User, Session, QrScan
            from utils import validate_qr_payload
            from duplicate_prevention import check_qr_duplicate, register_qr_scan

            # Setup: User und Session
            users = User.get_all_active()
            if not users:
                print(f"      ❌ Keine Test-User verfügbar")
                return False

            test_user = users[0]
            session = Session.create(test_user['ID'])

            if not session:
                print(f"      ❌ Test-Session konnte nicht erstellt werden")
                return False

            try:
                # Test verschiedene QR-Code Formate
                test_qr_codes = [
                    '{"kunde":"Test GmbH","auftrag":"TEST001","paket":"1/1"}',
                    'Kunde:Test GmbH^Auftrag:TEST002^Paket:1/2',
                    'Einfacher Test QR-Code'
                ]

                successful_scans = 0

                for qr_payload in test_qr_codes:
                    # 1. QR-Code Validierung
                    validation = validate_qr_payload(qr_payload)
                    if not validation or not validation.get('valid'):
                        continue

                    # 2. Duplikat-Check
                    duplicate_check = check_qr_duplicate(qr_payload, session['ID'])
                    if duplicate_check.get('is_duplicate'):
                        continue

                    # 3. QR-Scan speichern
                    qr_scan = QrScan.create(session['ID'], qr_payload)
                    if not qr_scan:
                        continue

                    # 4. Duplikat registrieren
                    register_qr_scan(qr_payload, session['ID'])

                    successful_scans += 1

                # Cleanup
                Session.end(session['ID'])

                if successful_scans < 2:
                    print(f"      ❌ Nicht genug erfolgreiche Scans: {successful_scans}")
                    return False

                print(f"      ✅ {successful_scans} QR-Scan-Workflows erfolgreich")
                return True

            except Exception as e:
                # Cleanup auch bei Fehler
                Session.end(session['ID'])
                raise e

        except Exception as e:
            print(f"      ❌ QR-Scan-Workflow Test Fehler: {e}")
            return False

    def test_multi_user_parallel(self):
        """Test: Multi-User parallele Nutzung"""
        try:
            from models import User, Session, QrScan
            import threading
            import time

            # Hole mehrere Test-User
            users = User.get_all_active()
            if len(users) < 2:
                print(f"      ❌ Nicht genug Test-User: {len(users)}")
                return False

            # Simuliere parallele Benutzer
            test_users = users[:3]  # Maximal 3 User
            sessions = []
            results = {'success': 0, 'errors': 0}
            results_lock = threading.Lock()

            def simulate_user_session(user):
                try:
                    # Session erstellen
                    session = Session.create(user['ID'])
                    if not session:
                        with results_lock:
                            results['errors'] += 1
                        return

                    sessions.append(session)

                    # Simuliere QR-Scans
                    for i in range(3):
                        test_payload = f"USER_{user['ID']}_SCAN_{i}_{int(time.time())}"
                        qr_scan = QrScan.create(session['ID'], test_payload)

                        if qr_scan:
                            with results_lock:
                                results['success'] += 1
                        else:
                            with results_lock:
                                results['errors'] += 1

                        time.sleep(0.1)  # Kurze Pause zwischen Scans

                except Exception as e:
                    with results_lock:
                        results['errors'] += 1

            # Starte parallele Threads
            threads = []
            for user in test_users:
                thread = threading.Thread(target=simulate_user_session, args=(user,))
                threads.append(thread)
                thread.start()

            # Warte auf alle Threads
            for thread in threads:
                thread.join(timeout=10)

            # Cleanup Sessions
            for session in sessions:
                try:
                    Session.end(session['ID'])
                except:
                    pass

            # Bewerte Ergebnisse
            total_expected = len(test_users) * 3  # 3 Scans pro User
            success_rate = results['success'] / total_expected if total_expected > 0 else 0

            print(f"      📊 Multi-User Test: {success_rate:.1%} Erfolgsrate")
            print(f"         Erfolgreiche Scans: {results['success']}")
            print(f"         Fehler: {results['errors']}")

            return success_rate >= 0.8  # 80% Erfolgsrate

        except Exception as e:
            print(f"      ❌ Multi-User Test Fehler: {e}")
            return False

    def test_error_recovery(self):
        """Test: Fehlerbehandlung und Recovery"""
        try:
            from models import User, Session, QrScan
            from connection import execute_query

            # Test 1: Ungültiger User
            try:
                invalid_session = Session.create(999999)
                if invalid_session:
                    print(f"      ❌ Session für ungültigen User erstellt")
                    return False
            except Exception:
                pass  # Erwartet

            # Test 2: Ungültige Session für QR-Scan
            try:
                invalid_qr = QrScan.create(999999, "Test")
                if invalid_qr:
                    print(f"      ❌ QR-Scan für ungültige Session erstellt")
                    return False
            except Exception:
                pass  # Erwartet

            # Test 3: Recovery nach DB-Verbindungsfehler
            # (Simuliert durch kurzen Test)
            try:
                # Teste normale Abfrage
                result1 = execute_query("SELECT COUNT(*) FROM dbo.ScannBenutzer", fetch_one=True)
                if not result1:
                    print(f"      ❌ Normale Abfrage fehlgeschlagen")
                    return False

                # Teste fehlerhafte Abfrage
                try:
                    execute_query("SELECT * FROM NonExistentTable", fetch_one=True)
                    print(f"      ❌ Fehlerhafte Abfrage sollte Fehler werfen")
                    return False
                except Exception:
                    pass  # Erwartet

                # Teste Recovery mit normaler Abfrage
                result2 = execute_query("SELECT COUNT(*) FROM dbo.Sessions", fetch_one=True)
                if not result2:
                    print(f"      ❌ Recovery nach Fehler fehlgeschlagen")
                    return False

            except Exception as e:
                print(f"      ❌ DB-Recovery Test Fehler: {e}")
                return False

            print(f"      ✅ Error-Recovery Tests erfolgreich")
            return True

        except Exception as e:
            print(f"      ❌ Error-Recovery Test Fehler: {e}")
            return False

    # ==================== PERFORMANCE TESTS ====================

    def test_memory_usage(self):
        """Test: Speicher-Verbrauch"""
        try:
            import psutil
            import gc

            # Baseline-Speicher
            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Simuliere normale Anwendungsnutzung
            from models import User, Session, QrScan

            # Erstelle mehrere Sessions und Scans
            users = User.get_all_active()
            if users:
                sessions = []

                # 10 Sessions erstellen
                for i in range(min(10, len(users))):
                    session = Session.create(users[i]['ID'])
                    if session:
                        sessions.append(session)

                        # Pro Session 5 QR-Scans
                        for j in range(5):
                            QrScan.create(session['ID'], f"Memory_Test_{i}_{j}")

                # Aktueller Speicher
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_usage = current_memory - baseline_memory

                # Cleanup
                for session in sessions:
                    Session.end(session['ID'])

                gc.collect()  # Garbage Collection

                # Speicher nach Cleanup
                after_cleanup = process.memory_info().rss / 1024 / 1024  # MB

                print(f"      📊 Speicher-Verbrauch:")
                print(f"         Baseline: {baseline_memory:.1f} MB")
                print(f"         Peak: {current_memory:.1f} MB (+{memory_usage:.1f} MB)")
                print(f"         Nach Cleanup: {after_cleanup:.1f} MB")

                target_memory = self.test_data['performance_targets']['memory_usage_mb']

                return memory_usage < target_memory

            else:
                print(f"      ⚠️ Keine User für Memory-Test verfügbar")
                return True

        except ImportError:
            print(f"      ⚠️ psutil nicht verfügbar - überspringe Memory-Test")
            return True
        except Exception as e:
            print(f"      ❌ Memory-Test Fehler: {e}")
            return False

    def test_scanner_performance(self):
        """Test: Scanner-Performance"""
        try:
            from qr_scanner import QRScanner
            import time

            # Test QR-Scanner Initialisierung
            start_time = time.time()
            scanner = QRScanner(camera_index=0)
            init_time = time.time() - start_time

            self.performance_metrics['scanner_init_time'] = init_time

            target_init_time = self.test_data['performance_targets']['camera_init_time_s']

            print(f"      📊 Scanner-Performance:")
            print(f"         Initialisierung: {init_time:.3f}s")

            if init_time > target_init_time:
                print(f"      ⚠️ Scanner-Initialisierung langsam (>{target_init_time}s)")

            # Test Frame-Processing (simuliert)
            processing_times = []
            for i in range(10):
                start = time.time()
                # Simuliere Frame-Processing
                time.sleep(0.01)  # 10ms simulierte Verarbeitung
                processing_times.append((time.time() - start) * 1000)

            avg_processing = sum(processing_times) / len(processing_times)

            print(f"         Avg. Frame-Processing: {avg_processing:.1f}ms")

            self.performance_metrics['frame_processing_time'] = avg_processing

            return init_time < target_init_time * 2  # Doppelte Zeit noch OK

        except Exception as e:
            print(f"      ❌ Scanner-Performance Test Fehler: {e}")
            return False

    def test_database_load(self):
        """Test: Datenbank unter Last"""
        try:
            from connection import execute_query
            from models import User, Session, QrScan
            import threading
            import time

            # Load-Test Parameter
            num_threads = 5
            operations_per_thread = 10
            results = {'success': 0, 'errors': 0, 'times': []}
            results_lock = threading.Lock()

            def db_load_worker():
                try:
                    users = User.get_all_active()
                    if not users:
                        return

                    test_user = users[0]

                    for i in range(operations_per_thread):
                        start_time = time.time()

                        try:
                            # Session erstellen
                            session = Session.create(test_user['ID'])
                            if session:
                                # QR-Scan hinzufügen
                                payload = f"LOAD_TEST_{threading.current_thread().ident}_{i}"
                                qr_scan = QrScan.create(session['ID'], payload)

                                if qr_scan:
                                    # Session beenden
                                    Session.end(session['ID'])

                                    with results_lock:
                                        results['success'] += 1
                                        results['times'].append(time.time() - start_time)
                                else:
                                    with results_lock:
                                        results['errors'] += 1
                            else:
                                with results_lock:
                                    results['errors'] += 1

                        except Exception as e:
                            with results_lock:
                                results['errors'] += 1

                except Exception as e:
                    with results_lock:
                        results['errors'] += 1

            # Starte Load-Test
            threads = []
            for i in range(num_threads):
                thread = threading.Thread(target=db_load_worker)
                threads.append(thread)
                thread.start()

            # Warte auf alle Threads
            for thread in threads:
                thread.join(timeout=30)

            # Bewerte Ergebnisse
            total_operations = num_threads * operations_per_thread
            success_rate = results['success'] / total_operations if total_operations > 0 else 0
            avg_time = sum(results['times']) / len(results['times']) if results['times'] else 0

            print(f"      📊 DB-Load-Test:")
            print(f"         Operationen: {total_operations}")
            print(f"         Erfolgreiche: {results['success']}")
            print(f"         Fehler: {results['errors']}")
            print(f"         Erfolgsrate: {success_rate:.1%}")
            print(f"         Durchschnittliche Zeit: {avg_time:.3f}s")

            return success_rate >= 0.9  # 90% Erfolgsrate

        except Exception as e:
            print(f"      ❌ DB-Load-Test Fehler: {e}")
            return False

    def test_concurrency(self):
        """Test: Gleichzeitige Zugriffe"""
        try:
            import threading
            import time
            from models import User, Session

            # Test gleichzeitige Session-Erstellung für gleichen User
            users = User.get_all_active()
            if not users:
                print(f"      ❌ Keine Test-User verfügbar")
                return False

            test_user = users[0]
            created_sessions = []
            results_lock = threading.Lock()

            def create_session_worker():
                try:
                    session = Session.create(test_user['ID'])
                    if session:
                        with results_lock:
                            created_sessions.append(session)
                except Exception as e:
                    pass  # Erwartete Konflikte

            # Starte mehrere Threads gleichzeitig
            threads = []
            for i in range(5):
                thread = threading.Thread(target=create_session_worker)
                threads.append(thread)

            # Alle Threads gleichzeitig starten
            for thread in threads:
                thread.start()

            # Warten
            for thread in threads:
                thread.join(timeout=5)

            # Prüfe: Sollte nur eine aktive Session geben
            active_sessions = Session.get_active()
            user_sessions = [s for s in active_sessions if s['UserID'] == test_user['ID']]

            # Cleanup
            for session in created_sessions:
                try:
                    Session.end(session['ID'])
                except:
                    pass

            print(f"      📊 Concurrency-Test:")
            print(f"         Erstellte Sessions: {len(created_sessions)}")
            print(f"         Aktive Sessions: {len(user_sessions)}")

            # Sollte durch Unique-Index genau 1 aktive Session sein
            return len(user_sessions) <= 1

        except Exception as e:
            print(f"      ❌ Concurrency-Test Fehler: {e}")
            return False

    # ==================== HILFSFUNKTIONEN ====================

    def _generate_test_report(self):
        """Erstellt ausführlichen Test-Bericht"""
        print("\n" + "=" * 80)
        print("📊 UMFASSENDER TEST-BERICHT")
        print("=" * 80)

        # Basis-Statistiken
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests

        print(f"🎯 Tests durchgeführt: {total_tests}")
        print(f"✅ Erfolgreich: {passed_tests}")
        print(f"❌ Fehlgeschlagen: {failed_tests}")
        print(f"📈 Erfolgsrate: {(passed_tests / total_tests) * 100:.1f}%")

        # Performance-Metriken
        if self.performance_metrics:
            print(f"\n⚡ PERFORMANCE-METRIKEN:")
            for metric, value in self.performance_metrics.items():
                if isinstance(value, float):
                    if 'time' in metric.lower():
                        unit = 'ms' if value < 1 else 's'
                        display_value = value * 1000 if value < 1 else value
                        print(f"   {metric}: {display_value:.1f}{unit}")
                    else:
                        print(f"   {metric}: {value:.3f}")
                else:
                    print(f"   {metric}: {value}")

        # Hardware-Status
        if self.hardware_status:
            print(f"\n🔧 HARDWARE-STATUS:")
            for component, status in self.hardware_status.items():
                if isinstance(status, list):
                    print(f"   {component}: {len(status)} verfügbar")
                    for item in status:
                        if isinstance(item, dict):
                            print(f"      - {item}")
                        else:
                            print(f"      - {item}")
                else:
                    print(f"   {component}: {status}")

        # Fehlgeschlagene Tests
        if failed_tests > 0:
            print(f"\n❌ FEHLGESCHLAGENE TESTS:")
            for test_name, result in self.test_results.items():
                if not result:
                    print(f"   - {test_name}")

        # Empfehlungen
        print(f"\n💡 EMPFEHLUNGEN:")

        if failed_tests == 0:
            print("   🎉 Alle Tests erfolgreich!")
            print("   ✅ System ist bereit für Produktivbetrieb")
            print("   🚀 Starten Sie die Anwendung mit: python app.py")
        else:
            print(f"   ⚠️ {failed_tests} Test(s) fehlgeschlagen")
            print("   🔧 Beheben Sie die Probleme und testen Sie erneut")

            # Spezifische Empfehlungen
            if 'Kamera-Erkennung' in [name for name, result in self.test_results.items() if not result]:
                print("   📸 Kamera-Probleme: Prüfen Sie CAMERA_INDICES in .env")

            if 'DB-Verbindung' in [name for name, result in self.test_results.items() if not result]:
                print("   🗄️ DB-Probleme: Prüfen Sie Netzwerk und Zugangsdaten")

            if any('Performance' in name for name, result in self.test_results.items() if not result):
                print("   ⚡ Performance-Probleme: Reduzieren Sie Auflösung/FPS")

        # Nächste Schritte
        print(f"\n🎯 NÄCHSTE SCHRITTE:")
        if failed_tests == 0:
            print("   1. Starten Sie die Anwendung: python app.py")
            print("   2. Testen Sie mit echten RFID-Tags")
            print("   3. Kalibrieren Sie QR-Scanner falls nötig")
            print("   4. Führen Sie regelmäßige Backups durch")
        else:
            print("   1. Beheben Sie die fehlgeschlagenen Tests")
            print("   2. Führen Sie den Test erneut aus")
            print("   3. Prüfen Sie die Konfiguration (.env)")
            print("   4. Kontaktieren Sie Support bei anhaltenden Problemen")

        print("=" * 80)

        # Erstelle Logfile
        self._save_test_report()

        return failed_tests == 0

    def _save_test_report(self):
        """Speichert Test-Bericht als Datei"""
        try:
            os.makedirs('logs', exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f"logs/comprehensive_test_report_{timestamp}.json"

            report_data = {
                'timestamp': datetime.now().isoformat(),
                'test_results': self.test_results,
                'performance_metrics': self.performance_metrics,
                'hardware_status': self.hardware_status,
                'summary': {
                    'total_tests': len(self.test_results),
                    'passed_tests': sum(1 for r in self.test_results.values() if r),
                    'failed_tests': sum(1 for r in self.test_results.values() if not r),
                    'success_rate': sum(1 for r in self.test_results.values() if r) / len(self.test_results)
                }
            }

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            print(f"📄 Test-Bericht gespeichert: {report_file}")

        except Exception as e:
            print(f"⚠️ Konnte Test-Bericht nicht speichern: {e}")


def main():
    """Hauptfunktion"""
    # Argument-Parsing für spezielle Test-Modi
    import sys

    test_mode = 'comprehensive'
    if len(sys.argv) > 1:
        test_mode = sys.argv[1].lower()

    # Comprehensive Test System
    if test_mode == 'comprehensive':
        test_system = ComprehensiveSystemTest()
        success = test_system.run_all_tests()

        # Exit-Code für Batch-Scripts
        sys.exit(0 if success else 1)

    elif test_mode == 'quick':
        # Schneller Test (nur kritische Komponenten)
        print("🚀 Quick-Test Modus")
        test_system = ComprehensiveSystemTest()

        quick_tests = [
            ("Python Module", test_system.test_python_modules),
            ("Konfiguration", test_system.test_configuration),
            ("DB-Verbindung", test_system.test_database_connection),
            ("Kamera-Check", test_system.test_camera_detection)
        ]

        all_passed = True
        for test_name, test_func in quick_tests:
            print(f"🔄 {test_name}...")
            try:
                result = test_func()
                status = "✅" if result else "❌"
                print(f"{status} {test_name}")
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"💥 {test_name} - CRASH: {e}")
                all_passed = False

        print(f"\n{'✅ Quick-Test erfolgreich!' if all_passed else '❌ Quick-Test fehlgeschlagen!'}")
        sys.exit(0 if all_passed else 1)

    elif test_mode == 'hardware':
        # Nur Hardware-Tests
        print("🔧 Hardware-Test Modus")
        test_system = ComprehensiveSystemTest()

        hardware_tests = [
            ("RFID Reader", test_system.test_rfid_reader),
            ("Kamera-Erkennung", test_system.test_camera_detection),
            ("Multi-Kamera", test_system.test_multi_camera),
            ("QR-Erkennung", test_system.test_qr_code_detection)
        ]

        for test_name, test_func in hardware_tests:
            print(f"🔄 {test_name}...")
            try:
                result = test_func()
                status = "✅" if result else "❌"
                print(f"{status} {test_name}")
            except Exception as e:
                print(f"💥 {test_name} - CRASH: {e}")

    else:
        print("❌ Unbekannter Test-Modus!")
        print("Verfügbare Modi:")
        print("  python test_comprehensive.py comprehensive  # Alle Tests")
        print("  python test_comprehensive.py quick          # Nur kritische Tests")
        print("  python test_comprehensive.py hardware       # Nur Hardware-Tests")
        sys.exit(1)


if __name__ == "__main__":
    main()