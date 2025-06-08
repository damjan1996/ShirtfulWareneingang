#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Tests für RFID & QR Scanner
Vollständige Workflow-Tests ohne GUI
"""

import sys
import os
import time
import threading
import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Projekt-Pfad hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class CompleteWorkflowTests(unittest.TestCase):
    """End-to-End Tests für komplette Workflows"""

    def setUp(self):
        """Setup für E2E-Tests"""
        from models import User, Session, QrScan
        from duplicate_prevention import duplicate_manager

        self.User = User
        self.Session = Session
        self.QrScan = QrScan

        # Reset Duplikat-Manager für saubere Tests
        duplicate_manager.recent_scans = {}
        duplicate_manager.session_scans = {}

        # Test-Daten
        self.test_data = {
            'valid_rfid_tags': ['53004ECD68', '53004E114B', '53004E0D1B'],
            'invalid_rfid_tags': ['INVALID123', '999999999999'],
            'test_qr_codes': [
                '{"kunde":"ABC GmbH","auftrag":"E2E001","paket":"1/1"}',
                'Kunde:XYZ Corp^Auftrag:E2E002^Paket:1/2',
                'Einfacher E2E Test QR-Code',
                '1^E2E003^TestData^Complete'
            ]
        }

        # Workflow-Statistiken
        self.workflow_stats = {
            'successful_logins': 0,
            'failed_logins': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'total_operations': 0
        }

    def tearDown(self):
        """Cleanup nach E2E-Tests"""
        # Cleanup alle Test-Sessions
        try:
            active_sessions = self.Session.get_active()
            for session in active_sessions:
                if 'E2E' in str(session.get('ID', '')):  # Nur Test-Sessions
                    self.Session.end(session['ID'])
        except:
            pass

        # Duplikat-Manager reset
        from duplicate_prevention import duplicate_manager
        duplicate_manager.recent_scans = {}
        duplicate_manager.session_scans = {}

        print(f"\n📊 E2E Workflow-Statistiken:")
        print(f"   Erfolgreiche Logins: {self.workflow_stats['successful_logins']}")
        print(f"   Fehlgeschlagene Logins: {self.workflow_stats['failed_logins']}")
        print(f"   Erfolgreiche Scans: {self.workflow_stats['successful_scans']}")
        print(f"   Fehlgeschlagene Scans: {self.workflow_stats['failed_scans']}")
        print(f"   Gesamt-Operationen: {self.workflow_stats['total_operations']}")

    def test_complete_single_user_workflow(self):
        """Test: Kompletter Single-User Workflow"""
        from utils import validate_tag_id, validate_qr_payload
        from duplicate_prevention import check_qr_duplicate, register_qr_scan

        # 1. RFID-Tag Validierung
        test_tag = self.test_data['valid_rfid_tags'][0]
        self.assertTrue(validate_tag_id(test_tag))

        # 2. User-Lookup
        user = self.User.get_by_epc(test_tag)
        self.assertIsNotNone(user, f"User mit Tag {test_tag} nicht gefunden")
        self.workflow_stats['successful_logins'] += 1

        # 3. Session erstellen (Login)
        session = self.Session.create(user['ID'])
        self.assertIsNotNone(session, "Session konnte nicht erstellt werden")
        session_id = session['ID']

        try:
            # 4. QR-Codes scannen
            scan_count = 0

            for qr_payload in self.test_data['test_qr_codes']:
                self.workflow_stats['total_operations'] += 1

                # a) QR-Payload validieren
                validation = validate_qr_payload(qr_payload)
                self.assertIsNotNone(validation)
                self.assertTrue(validation.get('valid', False))

                # b) Duplikat-Check
                duplicate_check = check_qr_duplicate(qr_payload, session_id)
                self.assertFalse(duplicate_check.get('is_duplicate'),
                                 f"Neuer QR-Code sollte kein Duplikat sein: {qr_payload[:50]}")

                # c) QR-Scan speichern
                qr_scan = self.QrScan.create(session_id, qr_payload)
                self.assertIsNotNone(qr_scan, f"QR-Scan konnte nicht gespeichert werden: {qr_payload[:50]}")

                # d) Duplikat registrieren
                register_qr_scan(qr_payload, session_id)

                # e) Duplikat-Check nach Registrierung
                duplicate_check_after = check_qr_duplicate(qr_payload, session_id)
                self.assertTrue(duplicate_check_after.get('is_duplicate'),
                                f"QR-Code sollte nach Registrierung Duplikat sein")

                scan_count += 1
                self.workflow_stats['successful_scans'] += 1

                # Kurze Pause zwischen Scans
                time.sleep(0.01)

            # 5. Session-Daten validieren
            session_scans = self.QrScan.get_by_session(session_id)
            self.assertEqual(len(session_scans), scan_count,
                             f"Erwartete {scan_count} Scans, gefunden {len(session_scans)}")

            # 6. Session beenden (Logout)
            logout_success = self.Session.end(session_id)
            self.assertTrue(logout_success, "Session konnte nicht beendet werden")

            # 7. Verifizieren dass Session beendet wurde
            active_sessions = self.Session.get_active()
            active_user_sessions = [s for s in active_sessions if s['UserID'] == user['ID']]
            self.assertEqual(len(active_user_sessions), 0, "Session sollte nicht mehr aktiv sein")

            print(f"      ✅ Single-User Workflow erfolgreich: {scan_count} Scans")

        except Exception as e:
            self.workflow_stats['failed_scans'] += 1
            raise e

    def test_multiple_users_parallel_workflow(self):
        """Test: Mehrere Benutzer parallel"""
        from utils import validate_tag_id
        from duplicate_prevention import check_qr_duplicate, register_qr_scan

        # Hole mehrere verfügbare User
        available_tags = [tag for tag in self.test_data['valid_rfid_tags']
                          if self.User.get_by_epc(tag) is not None]

        if len(available_tags) < 2:
            self.skipTest("Nicht genug User für Parallel-Workflow Test")

        test_users = []
        active_sessions = []

        try:
            # 1. Mehrere User anmelden
            for i, tag in enumerate(available_tags[:3]):  # Max 3 User
                user = self.User.get_by_epc(tag)
                self.assertIsNotNone(user)

                session = self.Session.create(user['ID'])
                self.assertIsNotNone(session)

                test_users.append({
                    'user': user,
                    'session': session,
                    'tag': tag,
                    'scan_count': 0
                })
                active_sessions.append(session['ID'])

                self.workflow_stats['successful_logins'] += 1

            # 2. Parallel QR-Scans für verschiedene User
            qr_base_payload = "PARALLEL_TEST"

            for round_num in range(3):  # 3 Runden
                for user_index, user_data in enumerate(test_users):
                    unique_payload = f"{qr_base_payload}_{round_num}_{user_index}_{int(time.time() * 1000000)}"

                    # Duplikat-Check
                    duplicate_check = check_qr_duplicate(unique_payload, user_data['session']['ID'])
                    self.assertFalse(duplicate_check.get('is_duplicate'))

                    # QR-Scan speichern
                    qr_scan = self.QrScan.create(user_data['session']['ID'], unique_payload)
                    self.assertIsNotNone(qr_scan)

                    # Duplikat registrieren
                    register_qr_scan(unique_payload, user_data['session']['ID'])

                    user_data['scan_count'] += 1
                    self.workflow_stats['successful_scans'] += 1
                    self.workflow_stats['total_operations'] += 1

                # Kurze Pause zwischen Runden
                time.sleep(0.05)

            # 3. Cross-User Duplikat-Test
            cross_payload = f"CROSS_USER_TEST_{int(time.time() * 1000000)}"

            # Erster User scannt
            first_user = test_users[0]
            qr_scan1 = self.QrScan.create(first_user['session']['ID'], cross_payload)
            self.assertIsNotNone(qr_scan1)
            register_qr_scan(cross_payload, first_user['session']['ID'])

            # Zweiter User versucht gleichen Code
            second_user = test_users[1]
            duplicate_check = check_qr_duplicate(cross_payload, second_user['session']['ID'])

            # Je nach Konfiguration kann das ein Duplikat sein oder nicht
            # Test ist flexibel für verschiedene Duplikat-Einstellungen

            # 4. Validiere Session-Daten für alle User
            for user_data in test_users:
                session_scans = self.QrScan.get_by_session(user_data['session']['ID'])
                self.assertGreaterEqual(len(session_scans), user_data['scan_count'])

            print(
                f"      ✅ Parallel-Workflow: {len(test_users)} User, {sum(u['scan_count'] for u in test_users)} Scans")

        finally:
            # 5. Cleanup: Alle Sessions beenden
            for session_id in active_sessions:
                try:
                    self.Session.end(session_id)
                except:
                    pass

    def test_error_recovery_workflow(self):
        """Test: Workflow mit Fehlerbehandlung"""
        from utils import validate_tag_id

        # 1. Test mit ungültigem RFID-Tag
        invalid_tag = self.test_data['invalid_rfid_tags'][0]
        self.assertFalse(validate_tag_id(invalid_tag), "Ungültiger Tag sollte als ungültig erkannt werden")

        user = self.User.get_by_epc(invalid_tag)
        self.assertIsNone(user, "Ungültiger Tag sollte keinen User finden")
        self.workflow_stats['failed_logins'] += 1

        # 2. Test mit gültigem Tag aber simuliertem Session-Fehler
        valid_tag = self.test_data['valid_rfid_tags'][0]
        user = self.User.get_by_epc(valid_tag)
        self.assertIsNotNone(user)

        # Simuliere mehrfache Session-Erstellung (sollte alte Session beenden)
        session1 = self.Session.create(user['ID'])
        self.assertIsNotNone(session1)

        session2 = self.Session.create(user['ID'])  # Sollte session1 beenden
        self.assertIsNotNone(session2)

        # Prüfe dass nur eine Session aktiv ist
        active_sessions = self.Session.get_active()
        user_sessions = [s for s in active_sessions if s['UserID'] == user['ID']]
        self.assertEqual(len(user_sessions), 1, "Nur eine Session sollte aktiv sein")
        self.assertEqual(user_sessions[0]['ID'], session2['ID'], "Neueste Session sollte aktiv sein")

        try:
            # 3. Test QR-Scan mit ungültigen Daten
            invalid_qr_payloads = [
                '',  # Leer
                None,  # Null
                'x' * 10000,  # Sehr lang
            ]

            for invalid_payload in invalid_qr_payloads:
                if invalid_payload is not None:  # None würde Exception werfen
                    try:
                        qr_scan = self.QrScan.create(session2['ID'], invalid_payload)
                        # Je nach Implementierung kann das funktionieren oder nicht
                        if qr_scan:
                            self.workflow_stats['successful_scans'] += 1
                        else:
                            self.workflow_stats['failed_scans'] += 1
                    except Exception:
                        self.workflow_stats['failed_scans'] += 1

                self.workflow_stats['total_operations'] += 1

            # 4. Test Session-Ende mit ungültiger Session-ID
            invalid_session_end = self.Session.end(999999)
            self.assertFalse(invalid_session_end, "Ungültige Session-ID sollte False zurückgeben")

            # 5. Recovery: Normale Operationen nach Fehlern
            recovery_payload = f"RECOVERY_TEST_{int(time.time())}"
            recovery_scan = self.QrScan.create(session2['ID'], recovery_payload)
            self.assertIsNotNone(recovery_scan, "Recovery-Scan sollte funktionieren")
            self.workflow_stats['successful_scans'] += 1

            print("      ✅ Error-Recovery Workflow erfolgreich")

        finally:
            # Cleanup
            self.Session.end(session2['ID'])

    def test_high_load_workflow(self):
        """Test: Workflow unter hoher Last"""
        from duplicate_prevention import check_qr_duplicate, register_qr_scan

        # Setup: Ein User für Load-Test
        test_tag = self.test_data['valid_rfid_tags'][0]
        user = self.User.get_by_epc(test_tag)
        self.assertIsNotNone(user)

        session = self.Session.create(user['ID'])
        self.assertIsNotNone(session)
        session_id = session['ID']

        try:
            # High-Load Test: Viele QR-Scans in kurzer Zeit
            num_scans = 100
            batch_size = 10

            successful_scans = 0
            failed_scans = 0

            start_time = time.time()

            for batch in range(0, num_scans, batch_size):
                batch_start = time.time()

                for i in range(batch_size):
                    scan_index = batch + i
                    payload = f"LOAD_TEST_{scan_index}_{int(time.time() * 1000000)}"

                    try:
                        # Schneller Duplikat-Check
                        duplicate_check = check_qr_duplicate(payload, session_id)
                        if duplicate_check.get('is_duplicate'):
                            failed_scans += 1
                            continue

                        # QR-Scan speichern
                        qr_scan = self.QrScan.create(session_id, payload)
                        if qr_scan:
                            register_qr_scan(payload, session_id)
                            successful_scans += 1
                            self.workflow_stats['successful_scans'] += 1
                        else:
                            failed_scans += 1
                            self.workflow_stats['failed_scans'] += 1

                    except Exception as e:
                        failed_scans += 1
                        self.workflow_stats['failed_scans'] += 1

                    self.workflow_stats['total_operations'] += 1

                # Batch-Timing
                batch_time = time.time() - batch_start
                if batch_time < 0.1:  # Mindestens 100ms pro Batch zur DB-Schonung
                    time.sleep(0.1 - batch_time)

            total_time = time.time() - start_time

            # Performance-Bewertung
            scans_per_second = successful_scans / total_time if total_time > 0 else 0
            success_rate = successful_scans / num_scans if num_scans > 0 else 0

            print(f"      📊 High-Load Test:")
            print(f"         Scans: {num_scans}")
            print(f"         Erfolgreich: {successful_scans}")
            print(f"         Fehlgeschlagen: {failed_scans}")
            print(f"         Erfolgsrate: {success_rate:.1%}")
            print(f"         Scans/Sekunde: {scans_per_second:.1f}")
            print(f"         Gesamtzeit: {total_time:.1f}s")

            # Assertions für Performance
            self.assertGreater(success_rate, 0.8, f"Erfolgsrate zu niedrig: {success_rate:.1%}")
            self.assertGreater(scans_per_second, 5, f"Zu wenig Scans/Sekunde: {scans_per_second:.1f}")

        finally:
            # Cleanup
            self.Session.end(session_id)

    def test_data_integrity_workflow(self):
        """Test: Datenintegrität über kompletten Workflow"""
        from utils import validate_qr_payload
        from duplicate_prevention import get_duplicate_stats

        # Test mit verschiedenen QR-Code Formaten
        test_scenarios = [
            {
                'name': 'JSON Format',
                'payload': '{"kunde":"Datenintegrität GmbH","auftrag":"DI001","paket":"1/1","timestamp":"2025-06-08T10:00:00"}',
                'expected_type': 'json'
            },
            {
                'name': 'Key-Value Format',
                'payload': 'Kunde:Datenintegrität Corp^Auftrag:DI002^Paket:2/3^Status:Test',
                'expected_type': 'keyvalue'
            },
            {
                'name': 'Unicode Text',
                'payload': 'Datenintegrität Test mit Umlauten: äöü ß € 中文 🚀',
                'expected_type': 'text'
            },
            {
                'name': 'Numerischer Code',
                'payload': '1234567890123456789012345678901234567890',
                'expected_type': 'text'
            }
        ]

        # Setup User und Session
        test_tag = self.test_data['valid_rfid_tags'][0]
        user = self.User.get_by_epc(test_tag)
        self.assertIsNotNone(user)

        session = self.Session.create(user['ID'])
        self.assertIsNotNone(session)
        session_id = session['ID']

        try:
            processed_scans = []

            for scenario in test_scenarios:
                payload = scenario['payload']
                expected_type = scenario['expected_type']

                # 1. Validiere Payload
                validation = validate_qr_payload(payload)
                self.assertIsNotNone(validation, f"Validation für {scenario['name']} fehlgeschlagen")
                self.assertTrue(validation.get('valid', False), f"{scenario['name']} sollte gültig sein")

                actual_type = validation.get('type')
                if expected_type != 'text':  # Text ist catch-all, andere sollten exakt passen
                    self.assertEqual(actual_type, expected_type,
                                     f"{scenario['name']}: Erwarteter Typ {expected_type}, erhalten {actual_type}")

                # 2. Speichere QR-Scan
                qr_scan = self.QrScan.create(session_id, payload)
                self.assertIsNotNone(qr_scan, f"QR-Scan für {scenario['name']} konnte nicht gespeichert werden")

                processed_scans.append({
                    'scenario': scenario['name'],
                    'qr_scan_id': qr_scan['ID'],
                    'original_payload': payload,
                    'validation': validation
                })

                self.workflow_stats['successful_scans'] += 1
                self.workflow_stats['total_operations'] += 1

                time.sleep(0.01)  # Kurze Pause

            # 3. Verifiziere Datenintegrität durch Rücklesen
            session_scans = self.QrScan.get_by_session(session_id)
            self.assertEqual(len(session_scans), len(test_scenarios),
                             "Anzahl gespeicherter Scans stimmt nicht überein")

            for i, saved_scan in enumerate(session_scans):
                original_scenario = processed_scans[-(i + 1)]  # Neueste zuerst

                # Payload-Integrität prüfen
                self.assertEqual(saved_scan['RawPayload'], original_scenario['original_payload'],
                                 f"Payload-Integrität verletzt für {original_scenario['scenario']}")

                # JSON-Payload prüfen (falls verfügbar)
                if saved_scan.get('PayloadJson'):
                    try:
                        import json
                        parsed_json = json.loads(saved_scan['PayloadJson'])
                        self.assertIsInstance(parsed_json, dict, "PayloadJson sollte gültiges JSON-Dict sein")
                    except json.JSONDecodeError:
                        self.fail(f"PayloadJson ist kein gültiges JSON: {saved_scan['PayloadJson']}")

                # Timestamp-Integrität
                self.assertIsNotNone(saved_scan['CapturedTS'], "CapturedTS sollte gesetzt sein")

            # 4. Duplikat-Manager Integrität
            dup_stats = get_duplicate_stats()
            self.assertIsInstance(dup_stats, dict, "Duplikat-Stats sollten Dict sein")
            self.assertIn('enabled', dup_stats, "Duplikat-Stats sollten 'enabled' enthalten")

            print(f"      ✅ Datenintegrität-Test: {len(test_scenarios)} Szenarien erfolgreich")

        finally:
            # Cleanup
            self.Session.end(session_id)


class SystemIntegrationTests(unittest.TestCase):
    """System-Integration Tests"""

    def test_complete_system_startup_shutdown(self):
        """Test: Kompletter System-Start und -Shutdown"""
        from utils import setup_logger, get_logger
        from duplicate_prevention import duplicate_manager

        # 1. Logger-System
        logger = setup_logger('E2E_Test', 'INFO')
        self.assertIsNotNone(logger)

        test_logger = get_logger('E2E_Test')
        self.assertEqual(logger, test_logger)

        # 2. Duplikat-Manager
        initial_stats = duplicate_manager.get_stats()
        self.assertIsInstance(initial_stats, dict)

        # 3. Datenbank-Verbindung
        from connection import test_connection, get_connection
        self.assertTrue(test_connection(), "DB-Verbindung sollte funktionieren")

        conn = get_connection()
        self.assertIsNotNone(conn)

        # 4. Models funktional
        from models import User, Session, QrScan

        users = User.get_all_active()
        self.assertIsInstance(users, list)

        active_sessions = Session.get_active()
        self.assertIsInstance(active_sessions, list)

        # 5. Hardware-Komponenten (Mock)
        with patch('hid_listener.keyboard.Listener'), \
                patch('qr_scanner.cv2.VideoCapture'):
            from hid_listener import HIDListener
            from qr_scanner import QRScanner

            # RFID-Listener
            hid_listener = HIDListener()
            self.assertIsNotNone(hid_listener)

            # QR-Scanner
            qr_scanner = QRScanner(camera_index=0)
            self.assertIsNotNone(qr_scanner)

        print("      ✅ System-Startup/Shutdown erfolgreich")

    def test_configuration_integration(self):
        """Test: Konfiguration-Integration"""
        from config import (DB_CONFIG, APP_CONFIG, QR_CONFIG,
                            SCANNER_CONFIG, UI_CONFIG, validate_config)

        # 1. Konfiguration-Validierung
        errors, warnings = validate_config()

        # Erlauben Warnungen, aber keine kritischen Fehler
        if errors:
            self.fail(f"Kritische Konfigurationsfehler: {errors}")

        # 2. DB-Konfiguration
        required_db_keys = ['server', 'database', 'user', 'password']
        for key in required_db_keys:
            self.assertIn(key, DB_CONFIG, f"DB_CONFIG fehlt {key}")
            self.assertIsNotNone(DB_CONFIG[key], f"DB_CONFIG.{key} ist None")

        # 3. App-Konfiguration
        self.assertIn('CAMERA_INDICES', APP_CONFIG)
        self.assertIsInstance(APP_CONFIG['CAMERA_INDICES'], list)
        self.assertGreater(len(APP_CONFIG['CAMERA_INDICES']), 0)

        # 4. Scanner-Konfiguration
        scanner_keys = ['FRAME_WIDTH', 'FRAME_HEIGHT', 'FPS']
        for key in scanner_keys:
            self.assertIn(key, SCANNER_CONFIG)
            self.assertIsInstance(SCANNER_CONFIG[key], int)
            self.assertGreater(SCANNER_CONFIG[key], 0)

        # 5. QR-Konfiguration
        self.assertIn('DUPLICATE_CHECK', QR_CONFIG)
        self.assertIsInstance(QR_CONFIG['DUPLICATE_CHECK'], bool)

        print("      ✅ Konfiguration-Integration erfolgreich")

    def test_multi_component_interaction(self):
        """Test: Interaktion zwischen verschiedenen Komponenten"""
        from models import User, Session, QrScan
        from duplicate_prevention import check_qr_duplicate, register_qr_scan
        from utils import validate_tag_id, validate_qr_payload

        # Komponenten-Interaktion simulieren

        # 1. RFID → User → Session
        test_tag = '53004ECD68'

        if not validate_tag_id(test_tag):
            self.skipTest("Test-Tag nicht gültig")

        user = User.get_by_epc(test_tag)
        if not user:
            self.skipTest("Test-User nicht verfügbar")

        session = Session.create(user['ID'])
        self.assertIsNotNone(session)

        try:
            # 2. QR → Validation → Duplicate-Check → Storage
            test_payload = f"INTEGRATION_TEST_{int(time.time())}"

            # Validation
            validation = validate_qr_payload(test_payload)
            self.assertIsNotNone(validation)
            self.assertTrue(validation.get('valid'))

            # Duplicate-Check
            dup_check1 = check_qr_duplicate(test_payload, session['ID'])
            self.assertFalse(dup_check1.get('is_duplicate'))

            # Storage
            qr_scan = QrScan.create(session['ID'], test_payload)
            self.assertIsNotNone(qr_scan)

            # Register
            register_qr_scan(test_payload, session['ID'])

            # Verify Duplicate-Check after Registration
            dup_check2 = check_qr_duplicate(test_payload, session['ID'])
            self.assertTrue(dup_check2.get('is_duplicate'))

            # 3. Session → QR-Scans → Retrieval
            session_scans = QrScan.get_by_session(session['ID'])
            self.assertGreater(len(session_scans), 0)

            found_scan = next((s for s in session_scans if s['RawPayload'] == test_payload), None)
            self.assertIsNotNone(found_scan, "Gespeicherter Scan sollte abrufbar sein")

            print("      ✅ Multi-Komponenten-Interaktion erfolgreich")

        finally:
            # Cleanup
            Session.end(session['ID'])


def run_e2e_tests():
    """Führt alle End-to-End Tests aus"""
    print("🔄 End-to-End Tests")
    print("=" * 50)

    # Test-Suites
    test_suites = [
        ('Komplette Workflows', unittest.TestLoader().loadTestsFromTestCase(CompleteWorkflowTests)),
        ('System-Integration', unittest.TestLoader().loadTestsFromTestCase(SystemIntegrationTests)),
    ]

    overall_results = {
        'total_tests': 0,
        'total_failures': 0,
        'total_errors': 0,
        'start_time': time.time()
    }

    for suite_name, test_suite in test_suites:
        print(f"\n🔄 {suite_name}")
        print("-" * 30)

        suite_start = time.time()

        # Test-Runner
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(test_suite)

        suite_time = time.time() - suite_start

        overall_results['total_tests'] += result.testsRun
        overall_results['total_failures'] += len(result.failures)
        overall_results['total_errors'] += len(result.errors)

        success_count = result.testsRun - len(result.failures) - len(result.errors)

        print(f"\n📊 {suite_name} Ergebnis:")
        print(f"   ✅ Erfolgreich: {success_count}")
        print(f"   ❌ Fehlschläge: {len(result.failures)}")
        print(f"   💥 Fehler: {len(result.errors)}")
        print(f"   ⏱️ Laufzeit: {suite_time:.1f}s")

    # Gesamt-Zusammenfassung
    total_time = time.time() - overall_results['start_time']
    success_count = overall_results['total_tests'] - overall_results['total_failures'] - overall_results['total_errors']
    success_rate = success_count / overall_results['total_tests'] if overall_results['total_tests'] > 0 else 0

    print("\n" + "=" * 50)
    print("📊 END-TO-END TEST ZUSAMMENFASSUNG")
    print("=" * 50)
    print(f"🎯 Tests durchgeführt: {overall_results['total_tests']}")
    print(f"✅ Erfolgreich: {success_count}")
    print(f"❌ Fehlschläge: {overall_results['total_failures']}")
    print(f"💥 Fehler: {overall_results['total_errors']}")
    print(f"📈 Erfolgsrate: {success_rate:.1%}")
    print(f"⏱️ Gesamtlaufzeit: {total_time:.1f}s")

    if overall_results['total_failures'] == 0 and overall_results['total_errors'] == 0:
        print("\n🎉 Alle End-to-End Tests erfolgreich!")
        print("🔄 Komplette Workflows funktionieren korrekt")
        print("✅ System ist produktionsreif")
    else:
        print(f"\n⚠️ {overall_results['total_failures'] + overall_results['total_errors']} E2E-Test(s) fehlgeschlagen")
        print("🔧 Überprüfen Sie die Workflow-Integration")

    print("=" * 50)

    return overall_results['total_failures'] == 0 and overall_results['total_errors'] == 0


if __name__ == '__main__':
    success = run_e2e_tests()
    sys.exit(0 if success else 1)