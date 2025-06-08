#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulation und Mock-Tests für RFID & QR Scanner
Ermöglicht Entwicklung und Tests ohne echte Hardware
"""

import sys
import os
import time
import threading
import unittest
import json
import random
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Projekt-Pfad hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class HardwareMockManager:
    """Verwaltet Mock-Hardware für Tests ohne echte Geräte"""

    def __init__(self):
        self.mock_rfid_tags = [
            '53004ECD68', '53004E114B', '53004E0D1B',
            '53004F3565', '53004F827A', '53004F3E37'
        ]

        self.mock_qr_codes = [
            '{"kunde":"Mock GmbH","auftrag":"SIM001","paket":"1/1"}',
            'Kunde:Simulation Corp^Auftrag:SIM002^Paket:1/2',
            'Test QR-Code für Simulation',
            '1^SIM003^MockData^Complete',
            'https://example.com/qr/SIM004',
            'Mock-Barcode: 1234567890123'
        ]

        self.simulation_active = False
        self.simulation_threads = []

    def create_mock_camera(self, camera_index=0):
        """Erstellt Mock-Kamera für OpenCV"""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 30.0  # FPS
        mock_cap.set.return_value = True

        # Mock-Frame erstellen
        def mock_read():
            if self.simulation_active:
                # Erstelle Mock-Frame (640x480x3)
                frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
                return True, frame
            else:
                return False, None

        mock_cap.read = mock_read
        mock_cap.release = Mock()

        return mock_cap

    def create_mock_hid_listener(self):
        """Erstellt Mock-HID-Listener für RFID"""
        mock_listener = Mock()
        mock_listener.running = False
        mock_listener.buffer = ""
        mock_listener.start = Mock()
        mock_listener.stop = Mock()

        def mock_start():
            mock_listener.running = True

        def mock_stop():
            mock_listener.running = False

        mock_listener.start.side_effect = mock_start
        mock_listener.stop.side_effect = mock_stop

        return mock_listener

    def simulate_rfid_scans(self, callback, interval=3.0, duration=30.0):
        """Simuliert RFID-Scans"""
        if not self.simulation_active:
            return

        def rfid_simulation():
            end_time = time.time() + duration

            while time.time() < end_time and self.simulation_active:
                # Zufälliger RFID-Tag
                tag = random.choice(self.mock_rfid_tags)

                if callback:
                    callback(tag)

                # Warte mit etwas Variation
                sleep_time = interval + random.uniform(-1.0, 1.0)
                time.sleep(max(0.5, sleep_time))

        thread = threading.Thread(target=rfid_simulation, daemon=True)
        self.simulation_threads.append(thread)
        thread.start()

    def simulate_qr_scans(self, callback, interval=5.0, duration=60.0):
        """Simuliert QR-Code-Scans"""
        if not self.simulation_active:
            return

        def qr_simulation():
            end_time = time.time() + duration

            while time.time() < end_time and self.simulation_active:
                # Zufälliger QR-Code
                qr_code = random.choice(self.mock_qr_codes)

                # Manchmal zufällige Codes generieren
                if random.random() < 0.3:
                    qr_code = f"Random_QR_{int(time.time())}_{random.randint(1000, 9999)}"

                if callback:
                    callback(qr_code)

                # Warte mit Variation
                sleep_time = interval + random.uniform(-2.0, 2.0)
                time.sleep(max(1.0, sleep_time))

        thread = threading.Thread(target=qr_simulation, daemon=True)
        self.simulation_threads.append(thread)
        thread.start()

    def start_simulation(self):
        """Startet Hardware-Simulation"""
        self.simulation_active = True
        print("🎭 Hardware-Simulation gestartet")

    def stop_simulation(self):
        """Stoppt Hardware-Simulation"""
        self.simulation_active = False

        # Warte auf alle Threads
        for thread in self.simulation_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)

        self.simulation_threads.clear()
        print("🎭 Hardware-Simulation gestoppt")


class SimulationTests(unittest.TestCase):
    """Tests mit simulierter Hardware"""

    def setUp(self):
        """Setup für Simulation-Tests"""
        self.mock_manager = HardwareMockManager()
        self.simulation_results = []

    def tearDown(self):
        """Cleanup nach Simulation-Tests"""
        self.mock_manager.stop_simulation()

        if self.simulation_results:
            print(f"\n📊 Simulation-Ergebnisse:")
            print(f"   Events verarbeitet: {len(self.simulation_results)}")

            event_types = {}
            for result in self.simulation_results:
                event_type = result.get('type', 'unknown')
                event_types[event_type] = event_types.get(event_type, 0) + 1

            for event_type, count in event_types.items():
                print(f"   {event_type}: {count}")

    def test_mock_camera_functionality(self):
        """Test: Mock-Kamera Funktionalität"""
        # Erstelle Mock-Kamera
        mock_camera = self.mock_manager.create_mock_camera(0)

        # Test isOpened
        self.assertTrue(mock_camera.isOpened())

        # Test Eigenschaften setzen/lesen
        mock_camera.set(3, 640)  # Width
        mock_camera.set(4, 480)  # Height

        self.assertEqual(mock_camera.get(5), 30.0)  # FPS

        # Test Frame-Capture
        self.mock_manager.start_simulation()

        ret, frame = mock_camera.read()
        self.assertTrue(ret)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (480, 640, 3))

        # Test ohne Simulation
        self.mock_manager.stop_simulation()

        ret, frame = mock_camera.read()
        self.assertFalse(ret)
        self.assertIsNone(frame)

        print("      ✅ Mock-Kamera funktioniert korrekt")

    def test_mock_rfid_listener(self):
        """Test: Mock-RFID-Listener"""
        mock_listener = self.mock_manager.create_mock_hid_listener()

        # Initial nicht aktiv
        self.assertFalse(mock_listener.running)

        # Test Start
        mock_listener.start()
        self.assertTrue(mock_listener.running)

        # Test Stop
        mock_listener.stop()
        self.assertFalse(mock_listener.running)

        print("      ✅ Mock-RFID-Listener funktioniert korrekt")

    def test_simulated_rfid_workflow(self):
        """Test: Simulierter RFID-Workflow"""
        from models import User, Session

        received_tags = []

        def rfid_callback(tag_id):
            received_tags.append({
                'type': 'rfid',
                'tag': tag_id,
                'timestamp': time.time()
            })
            self.simulation_results.append(received_tags[-1])

        # Starte Simulation
        self.mock_manager.start_simulation()
        self.mock_manager.simulate_rfid_scans(rfid_callback, interval=1.0, duration=5.0)

        # Warte auf Events
        time.sleep(6.0)

        # Prüfe Ergebnisse
        self.assertGreater(len(received_tags), 2, "Sollte mehrere RFID-Events erhalten")

        # Prüfe Tag-Validität
        for event in received_tags:
            tag = event['tag']
            self.assertIn(tag, self.mock_manager.mock_rfid_tags, f"Tag {tag} sollte aus Mock-Liste stammen")

        print(f"      ✅ {len(received_tags)} RFID-Events simuliert")

    def test_simulated_qr_workflow(self):
        """Test: Simulierter QR-Workflow"""
        from utils import validate_qr_payload

        received_qr_codes = []

        def qr_callback(payload):
            validation = validate_qr_payload(payload)

            received_qr_codes.append({
                'type': 'qr',
                'payload': payload,
                'validation': validation,
                'timestamp': time.time()
            })
            self.simulation_results.append(received_qr_codes[-1])

        # Starte Simulation
        self.mock_manager.start_simulation()
        self.mock_manager.simulate_qr_scans(qr_callback, interval=2.0, duration=8.0)

        # Warte auf Events
        time.sleep(10.0)

        # Prüfe Ergebnisse
        self.assertGreater(len(received_qr_codes), 2, "Sollte mehrere QR-Events erhalten")

        # Prüfe Validierung
        valid_count = sum(1 for event in received_qr_codes
                          if event['validation'] and event['validation'].get('valid'))

        self.assertGreater(valid_count, 0, "Mindestens ein QR-Code sollte gültig sein")

        print(f"      ✅ {len(received_qr_codes)} QR-Events simuliert ({valid_count} gültig)")

    def test_combined_simulation_workflow(self):
        """Test: Kombinierte RFID + QR Simulation"""
        from models import User, Session, QrScan

        # Events sammeln
        all_events = []
        active_sessions = {}

        def rfid_handler(tag_id):
            # Simuliere Login/Logout
            user = User.get_by_epc(tag_id)
            if user:
                user_id = user['ID']

                if user_id in active_sessions:
                    # Logout
                    Session.end(active_sessions[user_id]['ID'])
                    del active_sessions[user_id]
                    event_type = 'logout'
                else:
                    # Login
                    session = Session.create(user_id)
                    if session:
                        active_sessions[user_id] = session
                        event_type = 'login'
                    else:
                        event_type = 'login_failed'

                all_events.append({
                    'type': 'rfid',
                    'action': event_type,
                    'tag': tag_id,
                    'user_id': user_id,
                    'timestamp': time.time()
                })

        def qr_handler(payload):
            # Simuliere QR-Scan für erste aktive Session
            if active_sessions:
                session_id = list(active_sessions.values())[0]['ID']

                qr_scan = QrScan.create(session_id, payload)
                result = 'success' if qr_scan else 'failed'

                all_events.append({
                    'type': 'qr',
                    'action': result,
                    'payload': payload[:50],
                    'session_id': session_id,
                    'timestamp': time.time()
                })

        # Starte kombinierte Simulation
        self.mock_manager.start_simulation()
        self.mock_manager.simulate_rfid_scans(rfid_handler, interval=3.0, duration=15.0)
        self.mock_manager.simulate_qr_scans(qr_handler, interval=4.0, duration=15.0)

        # Warte auf Events
        time.sleep(17.0)

        # Cleanup: Alle aktiven Sessions beenden
        for session in active_sessions.values():
            try:
                Session.end(session['ID'])
            except:
                pass

        # Analysiere Ergebnisse
        self.simulation_results.extend(all_events)

        rfid_events = [e for e in all_events if e['type'] == 'rfid']
        qr_events = [e for e in all_events if e['type'] == 'qr']

        self.assertGreater(len(rfid_events), 2, "Sollte mehrere RFID-Events haben")
        self.assertGreater(len(qr_events), 0, "Sollte QR-Events haben")

        # Statistiken
        login_count = sum(1 for e in rfid_events if e['action'] == 'login')
        logout_count = sum(1 for e in rfid_events if e['action'] == 'logout')
        successful_qr = sum(1 for e in qr_events if e['action'] == 'success')

        print(f"      ✅ Kombinierte Simulation:")
        print(f"         RFID-Events: {len(rfid_events)} (Logins: {login_count}, Logouts: {logout_count})")
        print(f"         QR-Events: {len(qr_events)} (Erfolgreich: {successful_qr})")


class MockIntegrationTests(unittest.TestCase):
    """Integration-Tests mit Mocks"""

    def setUp(self):
        """Setup für Mock-Integration Tests"""
        self.mock_manager = HardwareMockManager()

    def tearDown(self):
        """Cleanup"""
        self.mock_manager.stop_simulation()

    def test_app_with_mocked_hardware(self):
        """Test: App mit gemockter Hardware"""
        with patch('app.HIDListener') as mock_hid_class, \
                patch('app.QRScanner') as mock_qr_class, \
                patch('app.setup_logger'), \
                patch('tkinter.Tk'):
            # Setup Mocks
            mock_hid_instance = self.mock_manager.create_mock_hid_listener()
            mock_hid_class.return_value = mock_hid_instance

            mock_qr_instance = Mock()
            mock_qr_instance.start = Mock()
            mock_qr_instance.stop = Mock()
            mock_qr_class.return_value = mock_qr_instance

            # Mock Root
            mock_root = Mock()

            # Teste App-Erstellung
            from app import ParallelMultiUserApp

            app = ParallelMultiUserApp(mock_root)

            # Prüfe dass Mocks verwendet werden
            mock_hid_class.assert_called_once()
            mock_hid_instance.start.assert_called_once()

            # Teste RFID-Callback
            test_tag = '53004ECD68'

            with patch.object(app, 'show_message') as mock_show_message:
                # Simuliere User nicht gefunden
                with patch('app.User.get_by_epc', return_value=None):
                    app.on_rfid_scan(test_tag)
                    mock_show_message.assert_called()

            print("      ✅ App mit Mocked Hardware funktioniert")

    def test_qr_scanner_with_mock_camera(self):
        """Test: QR-Scanner mit Mock-Kamera"""
        with patch('qr_scanner.cv2.VideoCapture') as mock_cv2:
            # Setup Mock-Kamera
            mock_camera = self.mock_manager.create_mock_camera()
            mock_cv2.return_value = mock_camera

            from qr_scanner import QRScanner

            received_qr_codes = []

            def qr_callback(payload):
                received_qr_codes.append(payload)

            # Erstelle Scanner
            scanner = QRScanner(camera_index=0, callback=qr_callback)

            # Prüfe Mock-Verwendung
            mock_cv2.assert_called_once_with(0)

            print("      ✅ QR-Scanner mit Mock-Kamera erstellt")

    def test_database_with_mock_data(self):
        """Test: Datenbank mit Mock-Daten"""
        from models import User, Session, QrScan

        # Teste mit echten Daten aber Mock-Events
        mock_events = [
            {'type': 'rfid', 'tag': '53004ECD68'},
            {'type': 'qr', 'payload': 'Mock QR Code 1'},
            {'type': 'qr', 'payload': 'Mock QR Code 2'},
            {'type': 'rfid', 'tag': '53004ECD68'},  # Logout
        ]

        session_id = None

        try:
            for event in mock_events:
                if event['type'] == 'rfid':
                    tag = event['tag']
                    user = User.get_by_epc(tag)

                    if user:
                        if session_id:
                            # Logout
                            Session.end(session_id)
                            session_id = None
                        else:
                            # Login
                            session = Session.create(user['ID'])
                            if session:
                                session_id = session['ID']

                elif event['type'] == 'qr' and session_id:
                    payload = event['payload']
                    QrScan.create(session_id, payload)

            print("      ✅ Mock-Events erfolgreich verarbeitet")

        finally:
            # Cleanup
            if session_id:
                Session.end(session_id)


class DevelopmentSimulationSuite:
    """Simulation-Suite für Entwicklung ohne Hardware"""

    def __init__(self):
        self.mock_manager = HardwareMockManager()
        self.simulation_running = False

    def run_interactive_simulation(self, duration=60):
        """Interaktive Simulation für Entwicklung"""
        print("🎭 Interaktive Hardware-Simulation")
        print("=" * 50)
        print(f"Dauer: {duration} Sekunden")
        print("Simuliert RFID-Tags und QR-Codes für Entwicklung")
        print()

        # Event-Handler
        def rfid_handler(tag_id):
            print(f"📟 RFID: {tag_id}")

        def qr_handler(payload):
            print(f"📱 QR: {payload[:50]}...")

        try:
            # Starte Simulation
            self.mock_manager.start_simulation()
            self.simulation_running = True

            self.mock_manager.simulate_rfid_scans(
                rfid_handler, interval=5.0, duration=duration
            )
            self.mock_manager.simulate_qr_scans(
                qr_handler, interval=3.0, duration=duration
            )

            print("✅ Simulation gestartet...")
            print("Drücken Sie Ctrl+C zum Beenden\n")

            # Warte
            start_time = time.time()
            while time.time() - start_time < duration and self.simulation_running:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n⏹️ Simulation durch Benutzer beendet")

        finally:
            self.mock_manager.stop_simulation()
            self.simulation_running = False
            print("🎭 Simulation beendet")

    def create_test_data_file(self, filename='test_data.json'):
        """Erstellt Test-Daten-Datei für Simulation"""
        test_data = {
            'rfid_tags': self.mock_manager.mock_rfid_tags,
            'qr_codes': self.mock_manager.mock_qr_codes,
            'simulation_scenarios': [
                {
                    'name': 'Single User Workflow',
                    'description': 'Ein Benutzer meldet sich an und scannt QR-Codes',
                    'events': [
                        {'type': 'rfid', 'tag': '53004ECD68', 'delay': 0},
                        {'type': 'qr', 'payload': '{"test": "data1"}', 'delay': 2},
                        {'type': 'qr', 'payload': '{"test": "data2"}', 'delay': 3},
                        {'type': 'rfid', 'tag': '53004ECD68', 'delay': 5}  # Logout
                    ]
                },
                {
                    'name': 'Multi User Workflow',
                    'description': 'Mehrere Benutzer arbeiten parallel',
                    'events': [
                        {'type': 'rfid', 'tag': '53004ECD68', 'delay': 0},
                        {'type': 'rfid', 'tag': '53004E114B', 'delay': 1},
                        {'type': 'qr', 'payload': 'User1 QR Code', 'delay': 2},
                        {'type': 'qr', 'payload': 'User2 QR Code', 'delay': 3},
                        {'type': 'rfid', 'tag': '53004ECD68', 'delay': 8},  # User1 Logout
                        {'type': 'rfid', 'tag': '53004E114B', 'delay': 10}  # User2 Logout
                    ]
                }
            ]
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2, ensure_ascii=False)
            print(f"📄 Test-Daten erstellt: {filename}")
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Test-Daten: {e}")


def run_simulation_tests():
    """Führt alle Simulation-Tests aus"""
    print("🎭 Hardware-Simulation Tests")
    print("=" * 50)

    # Test-Suites
    test_suites = [
        ('Hardware-Simulation', unittest.TestLoader().loadTestsFromTestCase(SimulationTests)),
        ('Mock-Integration', unittest.TestLoader().loadTestsFromTestCase(MockIntegrationTests)),
    ]

    overall_results = {
        'total_tests': 0,
        'total_failures': 0,
        'total_errors': 0,
        'start_time': time.time()
    }

    for suite_name, test_suite in test_suites:
        print(f"\n🎭 {suite_name}")
        print("-" * 30)

        # Test-Runner
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(test_suite)

        overall_results['total_tests'] += result.testsRun
        overall_results['total_failures'] += len(result.failures)
        overall_results['total_errors'] += len(result.errors)

    # Zusammenfassung
    total_time = time.time() - overall_results['start_time']
    success_count = overall_results['total_tests'] - overall_results['total_failures'] - overall_results['total_errors']
    success_rate = success_count / overall_results['total_tests'] if overall_results['total_tests'] > 0 else 0

    print("\n" + "=" * 50)
    print("📊 SIMULATION-TEST ZUSAMMENFASSUNG")
    print("=" * 50)
    print(f"🎯 Tests durchgeführt: {overall_results['total_tests']}")
    print(f"✅ Erfolgreich: {success_count}")
    print(f"❌ Fehlschläge: {overall_results['total_failures']}")
    print(f"💥 Fehler: {overall_results['total_errors']}")
    print(f"📈 Erfolgsrate: {success_rate:.1%}")
    print(f"⏱️ Laufzeit: {total_time:.1f}s")

    if overall_results['total_failures'] == 0 and overall_results['total_errors'] == 0:
        print("\n🎉 Alle Simulation-Tests erfolgreich!")
        print("🎭 Mock-Hardware funktioniert korrekt")
        print("💻 Entwicklung ohne echte Hardware möglich")
    else:
        print(
            f"\n⚠️ {overall_results['total_failures'] + overall_results['total_errors']} Simulation-Test(s) fehlgeschlagen")
        print("🔧 Überprüfen Sie die Mock-Implementierungen")

    print("=" * 50)

    return overall_results['total_failures'] == 0 and overall_results['total_errors'] == 0


def main():
    """Hauptfunktion für Simulation-Tests"""
    import argparse

    parser = argparse.ArgumentParser(description='Hardware-Simulation für RFID & QR Scanner')
    parser.add_argument('--test', action='store_true', help='Führe Simulation-Tests aus')
    parser.add_argument('--interactive', action='store_true', help='Interaktive Simulation')
    parser.add_argument('--duration', type=int, default=60, help='Simulation-Dauer in Sekunden')
    parser.add_argument('--create-data', action='store_true', help='Erstelle Test-Daten-Datei')

    args = parser.parse_args()

    if args.test:
        success = run_simulation_tests()
        sys.exit(0 if success else 1)

    elif args.interactive:
        sim_suite = DevelopmentSimulationSuite()
        sim_suite.run_interactive_simulation(args.duration)

    elif args.create_data:
        sim_suite = DevelopmentSimulationSuite()
        sim_suite.create_test_data_file()

    else:
        print("🎭 Hardware-Simulation für RFID & QR Scanner")
        print("=" * 50)
        print("Verwendung:")
        print("  python test_simulation.py --test         # Simulation-Tests ausführen")
        print("  python test_simulation.py --interactive  # Interaktive Simulation")
        print("  python test_simulation.py --create-data  # Test-Daten erstellen")
        print()
        print("Simulation ermöglicht Entwicklung und Tests ohne echte Hardware")


if __name__ == '__main__':
    main()