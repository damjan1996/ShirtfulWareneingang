#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance-Tests für RFID & QR Scanner
Detaillierte Performance-Messungen und Stress-Tests
"""

import sys
import os
import time
import threading
import unittest
import json
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Projekt-Pfad hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class DatabasePerformanceTests(unittest.TestCase):
    """Performance-Tests für Datenbank-Operationen"""

    def setUp(self):
        """Setup für DB-Performance Tests"""
        from models import User, Session, QrScan
        from connection import execute_query

        self.User = User
        self.Session = Session
        self.QrScan = QrScan
        self.execute_query = execute_query

        # Performance-Ziele (in Millisekunden)
        self.performance_targets = {
            'single_query': 50,  # Einzelne Abfrage < 50ms
            'user_lookup': 30,  # User-Lookup < 30ms
            'session_create': 100,  # Session erstellen < 100ms
            'qr_scan_insert': 50,  # QR-Insert < 50ms
            'bulk_insert': 200,  # 10 Inserts < 200ms
        }

        self.test_results = {}

    def tearDown(self):
        """Cleanup nach Tests"""
        # Performance-Ergebnisse ausgeben
        print(f"\n📊 DB-Performance Ergebnisse:")
        for test_name, times in self.test_results.items():
            if times:
                avg_time = statistics.mean(times)
                target = self.performance_targets.get(test_name, float('inf'))
                status = "✅" if avg_time < target else "⚠️"
                print(f"   {status} {test_name}: {avg_time:.1f}ms (Ziel: {target}ms)")

    def test_single_query_performance(self):
        """Test: Einzelne DB-Abfragen Performance"""
        query_times = []

        # Teste verschiedene Standard-Abfragen
        test_queries = [
            "SELECT COUNT(*) FROM dbo.ScannBenutzer",
            "SELECT COUNT(*) FROM dbo.Sessions",
            "SELECT COUNT(*) FROM dbo.QrScans",
            "SELECT TOP 1 * FROM dbo.ScannBenutzer WHERE xStatus = 0",
            "SELECT * FROM dbo.Sessions WHERE Active = 1",
        ]

        for query in test_queries:
            for _ in range(10):  # 10 Wiederholungen pro Query
                start_time = time.time()

                try:
                    if "TOP 1" in query or "Active = 1" in query:
                        self.execute_query(query, fetch_all=True)
                    else:
                        self.execute_query(query, fetch_one=True)

                    elapsed = (time.time() - start_time) * 1000  # ms
                    query_times.append(elapsed)

                except Exception as e:
                    self.fail(f"Query failed: {query} - {e}")

        self.test_results['single_query'] = query_times

        # Bewertung
        avg_time = statistics.mean(query_times)
        max_time = max(query_times)

        self.assertLess(avg_time, self.performance_targets['single_query'],
                        f"Durchschnittliche Query-Zeit zu hoch: {avg_time:.1f}ms")
        self.assertLess(max_time, self.performance_targets['single_query'] * 3,
                        f"Maximale Query-Zeit zu hoch: {max_time:.1f}ms")

    def test_user_lookup_performance(self):
        """Test: User-Lookup Performance"""
        # Hole verfügbare User
        users = self.User.get_all_active()
        if not users:
            self.skipTest("Keine User für Performance-Test verfügbar")

        lookup_times = []

        # Teste User-Lookup mit verschiedenen EPCs
        for user in users[:5]:  # Maximal 5 User
            user_epc = user.get('EPC')
            if user_epc:
                # Konvertiere zu Hex
                hex_epc = f"{user_epc:X}"

                for _ in range(20):  # 20 Lookups pro User
                    start_time = time.time()

                    found_user = self.User.get_by_epc(hex_epc)

                    elapsed = (time.time() - start_time) * 1000  # ms
                    lookup_times.append(elapsed)

                    self.assertIsNotNone(found_user, f"User mit EPC {hex_epc} sollte gefunden werden")
                    self.assertEqual(found_user['ID'], user['ID'])

        self.test_results['user_lookup'] = lookup_times

        avg_time = statistics.mean(lookup_times)
        self.assertLess(avg_time, self.performance_targets['user_lookup'],
                        f"User-Lookup zu langsam: {avg_time:.1f}ms")

    def test_session_create_performance(self):
        """Test: Session-Erstellung Performance"""
        users = self.User.get_all_active()
        if not users:
            self.skipTest("Keine User für Performance-Test verfügbar")

        create_times = []
        created_sessions = []

        try:
            test_user = users[0]

            for i in range(50):  # 50 Session-Erstellungen
                start_time = time.time()

                session = self.Session.create(test_user['ID'])

                elapsed = (time.time() - start_time) * 1000  # ms
                create_times.append(elapsed)

                self.assertIsNotNone(session, f"Session {i} konnte nicht erstellt werden")
                created_sessions.append(session['ID'])

        finally:
            # Cleanup: Alle Test-Sessions beenden
            for session_id in created_sessions:
                try:
                    self.Session.end(session_id)
                except:
                    pass

        self.test_results['session_create'] = create_times

        avg_time = statistics.mean(create_times)
        self.assertLess(avg_time, self.performance_targets['session_create'],
                        f"Session-Erstellung zu langsam: {avg_time:.1f}ms")

    def test_qr_scan_insert_performance(self):
        """Test: QR-Scan Insert Performance"""
        users = self.User.get_all_active()
        if not users:
            self.skipTest("Keine User für Performance-Test verfügbar")

        # Erstelle Test-Session
        test_user = users[0]
        session = self.Session.create(test_user['ID'])
        self.assertIsNotNone(session)

        insert_times = []

        try:
            for i in range(100):  # 100 QR-Inserts
                test_payload = f"PERFORMANCE_TEST_{i}_{int(time.time())}"

                start_time = time.time()

                qr_scan = self.QrScan.create(session['ID'], test_payload)

                elapsed = (time.time() - start_time) * 1000  # ms
                insert_times.append(elapsed)

                self.assertIsNotNone(qr_scan, f"QR-Scan {i} konnte nicht erstellt werden")

        finally:
            # Cleanup
            self.Session.end(session['ID'])

        self.test_results['qr_scan_insert'] = insert_times

        avg_time = statistics.mean(insert_times)
        self.assertLess(avg_time, self.performance_targets['qr_scan_insert'],
                        f"QR-Insert zu langsam: {avg_time:.1f}ms")

    def test_bulk_operations_performance(self):
        """Test: Bulk-Operationen Performance"""
        users = self.User.get_all_active()
        if not users:
            self.skipTest("Keine User für Performance-Test verfügbar")

        test_user = users[0]

        # Test: 10 Sessions parallel erstellen
        bulk_times = []

        for batch in range(5):  # 5 Batches
            start_time = time.time()

            created_sessions = []

            try:
                # Erstelle 10 Sessions (eine nach der anderen, da Unique-Constraint)
                for i in range(10):
                    session = self.Session.create(test_user['ID'])
                    if session:
                        created_sessions.append(session['ID'])

                        # QR-Scans hinzufügen
                        for j in range(5):
                            payload = f"BULK_TEST_{batch}_{i}_{j}"
                            self.QrScan.create(session['ID'], payload)

                        # Session sofort beenden für nächste
                        self.Session.end(session['ID'])

                elapsed = (time.time() - start_time) * 1000  # ms
                bulk_times.append(elapsed)

            except Exception as e:
                self.fail(f"Bulk-Operation Batch {batch} fehlgeschlagen: {e}")

        self.test_results['bulk_insert'] = bulk_times

        avg_time = statistics.mean(bulk_times)
        self.assertLess(avg_time, self.performance_targets['bulk_insert'] * 10,  # 10x wegen 50 Ops
                        f"Bulk-Operation zu langsam: {avg_time:.1f}ms")

    def test_concurrent_database_access(self):
        """Test: Gleichzeitige DB-Zugriffe"""
        users = self.User.get_all_active()
        if len(users) < 3:
            self.skipTest("Nicht genug User für Concurrency-Test")

        # Test mit mehreren Threads
        num_threads = 5
        operations_per_thread = 20

        results = {'success': 0, 'errors': 0, 'times': []}
        results_lock = threading.Lock()

        def db_worker(worker_id):
            test_user = users[worker_id % len(users)]
            worker_times = []

            for i in range(operations_per_thread):
                try:
                    start_time = time.time()

                    # Session erstellen
                    session = self.Session.create(test_user['ID'])
                    if session:
                        # QR-Scan hinzufügen
                        payload = f"CONCURRENT_TEST_{worker_id}_{i}"
                        qr_scan = self.QrScan.create(session['ID'], payload)

                        if qr_scan:
                            # Session beenden
                            self.Session.end(session['ID'])

                            elapsed = (time.time() - start_time) * 1000
                            worker_times.append(elapsed)

                            with results_lock:
                                results['success'] += 1
                                results['times'].append(elapsed)
                        else:
                            with results_lock:
                                results['errors'] += 1
                    else:
                        with results_lock:
                            results['errors'] += 1

                except Exception as e:
                    with results_lock:
                        results['errors'] += 1

        # Starte Worker-Threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=db_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Warte auf alle Threads
        for thread in threads:
            thread.join(timeout=30)

        # Bewerte Ergebnisse
        total_ops = num_threads * operations_per_thread
        success_rate = results['success'] / total_ops if total_ops > 0 else 0

        print(f"\n📊 Concurrent DB Access:")
        print(f"   Threads: {num_threads}")
        print(f"   Ops/Thread: {operations_per_thread}")
        print(f"   Erfolgreiche Ops: {results['success']}")
        print(f"   Fehler: {results['errors']}")
        print(f"   Erfolgsrate: {success_rate:.1%}")

        if results['times']:
            avg_time = statistics.mean(results['times'])
            print(f"   Durchschnittliche Zeit: {avg_time:.1f}ms")

        self.assertGreater(success_rate, 0.9, f"Erfolgsrate zu niedrig: {success_rate:.1%}")


class ScannerPerformanceTests(unittest.TestCase):
    """Performance-Tests für Scanner-Komponenten"""

    def setUp(self):
        """Setup für Scanner-Performance Tests"""
        self.performance_results = {}

    def tearDown(self):
        """Performance-Ergebnisse ausgeben"""
        print(f"\n📊 Scanner-Performance Ergebnisse:")
        for test_name, metrics in self.performance_results.items():
            print(f"   {test_name}:")
            for metric, value in metrics.items():
                if isinstance(value, (int, float)):
                    print(f"     {metric}: {value:.2f}")
                else:
                    print(f"     {metric}: {value}")

    def test_qr_validation_performance(self):
        """Test: QR-Validierung Performance"""
        from utils import validate_qr_payload

        # Teste verschiedene Payload-Typen
        test_payloads = [
            '{"kunde":"ABC","auftrag":"12345"}',  # JSON
            'Kunde:XYZ^Auftrag:67890',  # Key-Value
            'Simple text payload',  # Text
            'A' * 1000,  # Langer Text
            '1^2^3^4^5^6^7^8^9^10',  # Delimited
        ]

        validation_times = []

        # Teste jedes Payload 1000x
        for payload in test_payloads:
            payload_times = []

            for _ in range(1000):
                start_time = time.time()

                result = validate_qr_payload(payload)

                elapsed = (time.time() - start_time) * 1000000  # µs
                payload_times.append(elapsed)

                self.assertIsNotNone(result)

            validation_times.extend(payload_times)

        avg_time = statistics.mean(validation_times)
        max_time = max(validation_times)
        min_time = min(validation_times)

        self.performance_results['qr_validation'] = {
            'avg_time_us': avg_time,
            'max_time_us': max_time,
            'min_time_us': min_time,
            'total_validations': len(validation_times)
        }

        # QR-Validierung sollte sehr schnell sein (< 1ms)
        self.assertLess(avg_time, 1000, f"QR-Validierung zu langsam: {avg_time:.1f}µs")

    def test_rfid_validation_performance(self):
        """Test: RFID-Validierung Performance"""
        from utils import validate_tag_id, hex_to_decimal

        # Test-Tags
        test_tags = [
            '53004ECD68',
            '53004E114B',
            '1234567890',
            'ABCDEF1234',
            'INVALID123',  # Ungültig
            '12345',  # Zu kurz
        ]

        validation_times = []
        conversion_times = []

        for tag in test_tags:
            # Teste Validierung
            for _ in range(10000):  # 10k pro Tag
                start_time = time.time()

                is_valid = validate_tag_id(tag)

                elapsed = (time.time() - start_time) * 1000000  # µs
                validation_times.append(elapsed)

            # Teste Hex-Konvertierung (nur gültige)
            if len(tag) == 10 and all(c in '0123456789ABCDEFabcdef' for c in tag):
                for _ in range(10000):
                    start_time = time.time()

                    decimal = hex_to_decimal(tag)

                    elapsed = (time.time() - start_time) * 1000000  # µs
                    conversion_times.append(elapsed)

                    self.assertIsNotNone(decimal)

        self.performance_results['rfid_validation'] = {
            'avg_validation_time_us': statistics.mean(validation_times),
            'avg_conversion_time_us': statistics.mean(conversion_times) if conversion_times else 0,
            'total_validations': len(validation_times),
            'total_conversions': len(conversion_times)
        }

        # RFID-Validierung sollte extrem schnell sein
        avg_validation = statistics.mean(validation_times)
        self.assertLess(avg_validation, 100, f"RFID-Validierung zu langsam: {avg_validation:.1f}µs")

    def test_duplicate_prevention_performance(self):
        """Test: Duplikat-Verhinderung Performance"""
        from duplicate_prevention import check_qr_duplicate, register_qr_scan, duplicate_manager

        # Reset Manager für sauberen Test
        duplicate_manager.recent_scans = {}
        duplicate_manager.session_scans = {}

        test_session_id = 999999
        check_times = []
        register_times = []

        # Erstelle verschiedene Payloads
        test_payloads = [f"PERF_TEST_{i}" for i in range(1000)]

        # Test Check-Performance (Cache leer)
        for payload in test_payloads:
            start_time = time.time()

            result = check_qr_duplicate(payload, test_session_id)

            elapsed = (time.time() - start_time) * 1000  # ms
            check_times.append(elapsed)

            self.assertIsInstance(result, dict)
            self.assertIn('is_duplicate', result)

        # Test Register-Performance
        for payload in test_payloads:
            start_time = time.time()

            register_qr_scan(payload, test_session_id)

            elapsed = (time.time() - start_time) * 1000  # ms
            register_times.append(elapsed)

        # Test Check-Performance (Cache gefüllt)
        check_times_cached = []
        for payload in test_payloads[:100]:  # Nur subset
            start_time = time.time()

            result = check_qr_duplicate(payload, test_session_id)

            elapsed = (time.time() - start_time) * 1000  # ms
            check_times_cached.append(elapsed)

            # Sollte als Duplikat erkannt werden
            self.assertTrue(result.get('is_duplicate'))

        self.performance_results['duplicate_prevention'] = {
            'avg_check_time_ms': statistics.mean(check_times),
            'avg_register_time_ms': statistics.mean(register_times),
            'avg_cached_check_time_ms': statistics.mean(check_times_cached),
            'cache_speedup_factor': statistics.mean(check_times) / statistics.mean(
                check_times_cached) if check_times_cached else 1
        }

        # Duplikat-Check sollte sehr schnell sein
        avg_check = statistics.mean(check_times)
        self.assertLess(avg_check, 10, f"Duplikat-Check zu langsam: {avg_check:.2f}ms")

    def test_camera_initialization_performance(self):
        """Test: Kamera-Initialisierung Performance"""
        import cv2

        camera_indices = [0, 1, 2]
        init_times = []

        for camera_index in camera_indices:
            start_time = time.time()

            try:
                cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)

                if cap.isOpened():
                    # Teste ersten Frame
                    ret, frame = cap.read()

                    init_time = (time.time() - start_time) * 1000  # ms
                    init_times.append(init_time)

                    if ret and frame is not None:
                        height, width = frame.shape[:2]
                        print(f"      ✅ Kamera {camera_index}: {init_time:.1f}ms ({width}x{height})")
                    else:
                        print(f"      ⚠️ Kamera {camera_index}: {init_time:.1f}ms (kein Frame)")

                cap.release()

            except Exception as e:
                print(f"      ❌ Kamera {camera_index}: Fehler - {e}")

        if init_times:
            self.performance_results['camera_initialization'] = {
                'avg_init_time_ms': statistics.mean(init_times),
                'max_init_time_ms': max(init_times),
                'min_init_time_ms': min(init_times),
                'cameras_tested': len(init_times)
            }

            avg_init = statistics.mean(init_times)
            self.assertLess(avg_init, 3000, f"Kamera-Initialisierung zu langsam: {avg_init:.1f}ms")
        else:
            self.skipTest("Keine Kameras für Performance-Test verfügbar")

    def test_memory_performance_scanner(self):
        """Test: Speicher-Performance von Scannern"""
        try:
            import psutil
            from qr_scanner import QRScanner
            from hid_listener import HIDListener

            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

            components = []
            memory_measurements = []

            try:
                # Baseline
                memory_measurements.append(('Baseline', baseline_memory))

                # RFID Listener
                rfid_listener = HIDListener()
                rfid_listener.start()
                components.append(rfid_listener)

                time.sleep(0.5)
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_measurements.append(('RFID Listener', current_memory))

                # QR Scanner (falls Kamera verfügbar)
                try:
                    qr_scanner = QRScanner(camera_index=0)
                    # Nicht starten um Kamera-Probleme zu vermeiden
                    components.append(qr_scanner)

                    time.sleep(0.5)
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_measurements.append(('QR Scanner', current_memory))
                except:
                    pass

                # Arbeits-Simulation
                time.sleep(2.0)
                final_memory = process.memory_info().rss / 1024 / 1024
                memory_measurements.append(('Nach Simulation', final_memory))

            finally:
                # Cleanup
                for component in components:
                    if hasattr(component, 'stop'):
                        try:
                            component.stop()
                        except:
                            pass

                time.sleep(0.5)
                cleanup_memory = process.memory_info().rss / 1024 / 1024
                memory_measurements.append(('Nach Cleanup', cleanup_memory))

            # Analyse
            max_memory = max(mem for _, mem in memory_measurements)
            memory_increase = max_memory - baseline_memory
            memory_after_cleanup = memory_measurements[-1][1] - baseline_memory

            self.performance_results['memory_performance'] = {
                'baseline_mb': baseline_memory,
                'max_memory_mb': max_memory,
                'memory_increase_mb': memory_increase,
                'memory_after_cleanup_mb': memory_after_cleanup,
                'measurements': memory_measurements
            }

            print(f"\n📊 Memory Performance:")
            for phase, memory in memory_measurements:
                print(f"   {phase}: {memory:.1f} MB")

            # Memory sollte unter 100MB Increase bleiben
            self.assertLess(memory_increase, 100, f"Memory-Increase zu hoch: {memory_increase:.1f}MB")

        except ImportError:
            self.skipTest("psutil nicht verfügbar")


class StressTests(unittest.TestCase):
    """Stress-Tests für System-Belastung"""

    def test_high_frequency_qr_scans(self):
        """Test: Hochfrequente QR-Scans"""
        from models import User, Session, QrScan

        users = User.get_all_active()
        if not users:
            self.skipTest("Keine User für Stress-Test")

        test_user = users[0]
        session = Session.create(test_user['ID'])
        self.assertIsNotNone(session)

        num_scans = 1000
        scan_times = []

        try:
            start_time = time.time()

            for i in range(num_scans):
                scan_start = time.time()

                payload = f"STRESS_TEST_{i}_{int(time.time() * 1000000)}"  # Unique mit Mikrosekunden

                qr_scan = QrScan.create(session['ID'], payload)

                scan_time = (time.time() - scan_start) * 1000  # ms
                scan_times.append(scan_time)

                self.assertIsNotNone(qr_scan, f"QR-Scan {i} fehlgeschlagen")

                # Kurze Pause um DB nicht zu überlasten
                if i % 100 == 0:
                    time.sleep(0.01)

            total_time = time.time() - start_time

            # Statistiken
            avg_scan_time = statistics.mean(scan_times)
            max_scan_time = max(scan_times)
            scans_per_second = num_scans / total_time

            print(f"\n📊 High-Frequency QR-Scan Stress-Test:")
            print(f"   Scans: {num_scans}")
            print(f"   Total Zeit: {total_time:.1f}s")
            print(f"   Scans/Sekunde: {scans_per_second:.1f}")
            print(f"   Durchschnittliche Scan-Zeit: {avg_scan_time:.1f}ms")
            print(f"   Maximale Scan-Zeit: {max_scan_time:.1f}ms")

            # Performance-Kriterien
            self.assertGreater(scans_per_second, 10, f"Zu wenig Scans/Sekunde: {scans_per_second:.1f}")
            self.assertLess(avg_scan_time, 100, f"Durchschnittliche Scan-Zeit zu hoch: {avg_scan_time:.1f}ms")

        finally:
            Session.end(session['ID'])

    def test_concurrent_users_stress(self):
        """Test: Viele gleichzeitige Benutzer"""
        from models import User, Session, QrScan

        users = User.get_all_active()
        if len(users) < 3:
            self.skipTest("Nicht genug User für Concurrent-Stress-Test")

        num_concurrent_users = min(10, len(users))
        scans_per_user = 50

        results = {
            'successful_sessions': 0,
            'successful_scans': 0,
            'errors': 0,
            'times': []
        }
        results_lock = threading.Lock()

        def user_simulation(user_index):
            """Simuliert einen Benutzer"""
            test_user = users[user_index % len(users)]

            try:
                # Session erstellen
                session_start = time.time()
                session = Session.create(test_user['ID'])

                if not session:
                    with results_lock:
                        results['errors'] += 1
                    return

                with results_lock:
                    results['successful_sessions'] += 1

                # QR-Scans durchführen
                for i in range(scans_per_user):
                    scan_start = time.time()

                    payload = f"CONCURRENT_{user_index}_{i}_{int(time.time() * 1000000)}"

                    qr_scan = QrScan.create(session['ID'], payload)

                    if qr_scan:
                        with results_lock:
                            results['successful_scans'] += 1
                            results['times'].append(time.time() - scan_start)
                    else:
                        with results_lock:
                            results['errors'] += 1

                    # Realistische Pause zwischen Scans
                    time.sleep(0.1)

                # Session beenden
                Session.end(session['ID'])

            except Exception as e:
                with results_lock:
                    results['errors'] += 1

        # Starte alle User-Threads gleichzeitig
        with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
            futures = [executor.submit(user_simulation, i) for i in range(num_concurrent_users)]

            # Warte auf alle
            for future in as_completed(futures, timeout=120):  # 2 Minuten Timeout
                try:
                    future.result()
                except Exception as e:
                    with results_lock:
                        results['errors'] += 1

        # Bewerte Ergebnisse
        total_expected_sessions = num_concurrent_users
        total_expected_scans = num_concurrent_users * scans_per_user

        session_success_rate = results['successful_sessions'] / total_expected_sessions
        scan_success_rate = results['successful_scans'] / total_expected_scans

        avg_scan_time = statistics.mean(results['times']) if results['times'] else 0

        print(f"\n📊 Concurrent Users Stress-Test:")
        print(f"   Gleichzeitige User: {num_concurrent_users}")
        print(f"   Scans pro User: {scans_per_user}")
        print(
            f"   Erfolgreiche Sessions: {results['successful_sessions']}/{total_expected_sessions} ({session_success_rate:.1%})")
        print(f"   Erfolgreiche Scans: {results['successful_scans']}/{total_expected_scans} ({scan_success_rate:.1%})")
        print(f"   Fehler: {results['errors']}")
        print(f"   Durchschnittliche Scan-Zeit: {avg_scan_time:.3f}s")

        # Mindestens 80% Erfolgsrate
        self.assertGreater(session_success_rate, 0.8, f"Session-Erfolgsrate zu niedrig: {session_success_rate:.1%}")
        self.assertGreater(scan_success_rate, 0.8, f"Scan-Erfolgsrate zu niedrig: {scan_success_rate:.1%}")

    def test_long_running_stability(self):
        """Test: Langzeit-Stabilität"""
        from models import User, Session, QrScan
        from duplicate_prevention import get_duplicate_stats

        users = User.get_all_active()
        if not users:
            self.skipTest("Keine User für Langzeit-Test")

        test_user = users[0]

        # Langzeit-Test: 5 Minuten kontinuierliche Aktivität
        test_duration = 10  # 10 Sekunden für schnellen Test (normalerweise 300s)
        operations_per_second = 2

        start_time = time.time()
        end_time = start_time + test_duration

        stats = {
            'sessions_created': 0,
            'scans_created': 0,
            'errors': 0,
            'memory_samples': []
        }

        try:
            import psutil
            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024
        except ImportError:
            process = None
            baseline_memory = 0

        operation_count = 0

        while time.time() < end_time:
            cycle_start = time.time()

            try:
                # Session erstellen
                session = Session.create(test_user['ID'])
                if session:
                    stats['sessions_created'] += 1

                    # QR-Scans hinzufügen
                    for i in range(operations_per_second):
                        payload = f"LONGRUN_{operation_count}_{i}"
                        qr_scan = QrScan.create(session['ID'], payload)

                        if qr_scan:
                            stats['scans_created'] += 1
                        else:
                            stats['errors'] += 1

                    # Session beenden
                    Session.end(session['ID'])
                else:
                    stats['errors'] += 1

                # Memory-Sampling alle 10 Operationen
                if process and operation_count % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    stats['memory_samples'].append(current_memory)

                operation_count += 1

                # Timing für gewünschte Operationen/Sekunde
                cycle_time = time.time() - cycle_start
                sleep_time = max(0, (1.0 / operations_per_second) - cycle_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                stats['errors'] += 1

        total_runtime = time.time() - start_time

        # Memory-Analyse
        if stats['memory_samples']:
            max_memory = max(stats['memory_samples'])
            memory_growth = max_memory - baseline_memory
        else:
            max_memory = baseline_memory
            memory_growth = 0

        # Duplikat-Manager Stats
        dup_stats = get_duplicate_stats()

        print(f"\n📊 Long-Running Stability Test:")
        print(f"   Laufzeit: {total_runtime:.1f}s")
        print(f"   Sessions erstellt: {stats['sessions_created']}")
        print(f"   Scans erstellt: {stats['scans_created']}")
        print(f"   Fehler: {stats['errors']}")
        print(f"   Operationen/Sekunde: {(stats['sessions_created'] + stats['scans_created']) / total_runtime:.1f}")

        if process:
            print(f"   Memory Baseline: {baseline_memory:.1f} MB")
            print(f"   Memory Max: {max_memory:.1f} MB")
            print(f"   Memory Growth: {memory_growth:.1f} MB")

        print(f"   Duplikat-Cache: {dup_stats}")

        # Bewertung
        error_rate = stats['errors'] / (stats['sessions_created'] + stats['scans_created'] + stats['errors'])
        self.assertLess(error_rate, 0.05, f"Fehlerrate zu hoch: {error_rate:.1%}")

        if process:
            self.assertLess(memory_growth, 50, f"Memory-Growth zu hoch: {memory_growth:.1f} MB")


def run_performance_tests():
    """Führt alle Performance-Tests aus"""
    print("⚡ Performance-Tests für RFID & QR Scanner")
    print("=" * 60)

    # Test-Suites
    test_suites = [
        ('Datenbank Performance', unittest.TestLoader().loadTestsFromTestCase(DatabasePerformanceTests)),
        ('Scanner Performance', unittest.TestLoader().loadTestsFromTestCase(ScannerPerformanceTests)),
        ('Stress Tests', unittest.TestLoader().loadTestsFromTestCase(StressTests)),
    ]

    overall_results = {
        'total_tests': 0,
        'total_failures': 0,
        'total_errors': 0,
        'start_time': time.time()
    }

    for suite_name, test_suite in test_suites:
        print(f"\n⚡ {suite_name}")
        print("-" * 40)

        suite_start = time.time()

        # Test-Runner
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(test_suite)

        suite_time = time.time() - suite_start

        overall_results['total_tests'] += result.testsRun
        overall_results['total_failures'] += len(result.failures)
        overall_results['total_errors'] += len(result.errors)

        print(f"\n📊 {suite_name} Zusammenfassung:")
        print(f"   Tests: {result.testsRun}")
        print(f"   Erfolgreich: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"   Fehlschläge: {len(result.failures)}")
        print(f"   Fehler: {len(result.errors)}")
        print(f"   Laufzeit: {suite_time:.1f}s")

    # Gesamt-Zusammenfassung
    total_time = time.time() - overall_results['start_time']
    success_count = overall_results['total_tests'] - overall_results['total_failures'] - overall_results['total_errors']
    success_rate = success_count / overall_results['total_tests'] if overall_results['total_tests'] > 0 else 0

    print("\n" + "=" * 60)
    print("📊 PERFORMANCE-TEST GESAMTERGEBNIS")
    print("=" * 60)
    print(f"🎯 Tests durchgeführt: {overall_results['total_tests']}")
    print(f"✅ Erfolgreich: {success_count}")
    print(f"❌ Fehlschläge: {overall_results['total_failures']}")
    print(f"💥 Fehler: {overall_results['total_errors']}")
    print(f"📈 Erfolgsrate: {success_rate:.1%}")
    print(f"⏱️ Gesamtlaufzeit: {total_time:.1f}s")

    if overall_results['total_failures'] == 0 and overall_results['total_errors'] == 0:
        print("\n🎉 Alle Performance-Tests erfolgreich!")
        print("⚡ System zeigt gute Performance-Charakteristiken")
        print("✅ Bereit für Produktiv-Einsatz")
    else:
        print(
            f"\n⚠️ {overall_results['total_failures'] + overall_results['total_errors']} Performance-Test(s) fehlgeschlagen")
        print("🔧 Optimieren Sie die Performance-kritischen Bereiche")

    print("=" * 60)

    return overall_results['total_failures'] == 0 and overall_results['total_errors'] == 0


if __name__ == '__main__':
    success = run_performance_tests()
    sys.exit(0 if success else 1)