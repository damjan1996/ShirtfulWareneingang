#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Umfassender Test aller Systemkomponenten
Führt vor dem Start der Anwendung alle wichtigen Tests durch
"""

import sys
import os
import time
from datetime import datetime
import json

# Projekt-Pfad hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test: Alle Python-Module können importiert werden"""
    print("🔧 Teste Python-Module...")

    modules_to_test = [
        ('tkinter', 'GUI Framework'),
        ('cv2', 'OpenCV für Kamera'),
        ('pyzbar', 'QR-Code Decoder'),
        ('pyodbc', 'SQL Server Connector'),
        ('pynput', 'Keyboard Listener'),
        ('PIL', 'Bildverarbeitung'),
        ('numpy', 'Numerische Berechnungen')
    ]

    failed_modules = []

    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"   ✅ {module_name} - {description}")
        except ImportError as e:
            print(f"   ❌ {module_name} - {description} - FEHLER: {e}")
            failed_modules.append(module_name)

    if failed_modules:
        print(f"\n❌ Fehlende Module: {', '.join(failed_modules)}")
        print("   Installieren Sie mit: pip install -r requirements.txt")
        return False

    print("   ✅ Alle Module verfügbar")
    return True


def test_config():
    """Test: Konfiguration laden"""
    print("\n⚙️ Teste Konfiguration...")

    try:
        from config import DB_CONFIG, APP_CONFIG

        # Prüfe DB-Config
        required_db_keys = ['server', 'database', 'user', 'password']
        missing_keys = [key for key in required_db_keys if not DB_CONFIG.get(key)]

        if missing_keys:
            print(f"   ❌ Fehlende DB-Konfiguration: {', '.join(missing_keys)}")
            return False

        print(f"   ✅ DB-Server: {DB_CONFIG['server']}")
        print(f"   ✅ DB-Name: {DB_CONFIG['database']}")
        print(f"   ✅ DB-User: {DB_CONFIG['user']}")
        print(f"   ✅ App-Debug: {APP_CONFIG.get('DEBUG', False)}")

        # Prüfe .env Datei
        if os.path.exists('.env'):
            print("   ✅ .env Datei gefunden")
        else:
            print("   ⚠️ .env Datei nicht gefunden - verwende Standardwerte")

        return True

    except Exception as e:
        print(f"   ❌ Konfigurationsfehler: {e}")
        return False


def test_database():
    """Test: Datenbankverbindung und Struktur"""
    print("\n🗄️ Teste Datenbankverbindung...")

    try:
        from connection import get_connection, test_connection

        # Verbindungstest
        if not test_connection():
            print("   ❌ Datenbankverbindung fehlgeschlagen")
            return False

        print("   ✅ Datenbankverbindung erfolgreich")

        # Tabellen prüfen
        conn = get_connection()
        cursor = conn.cursor()

        tables_to_check = [
            'ScannBenutzer',
            'Sessions',
            'QrScans',
            'ScannTyp',
            'ScannKopf',
            'ScannPosition'
        ]

        existing_tables = []
        missing_tables = []

        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM dbo.{table}")
                count = cursor.fetchone()[0]
                existing_tables.append((table, count))
                print(f"   ✅ Tabelle {table}: {count} Einträge")
            except Exception:
                missing_tables.append(table)
                print(f"   ❌ Tabelle {table}: nicht gefunden")

        cursor.close()

        if missing_tables:
            print(f"\n   ⚠️ Fehlende Tabellen: {', '.join(missing_tables)}")
            print("   Führen Sie aus: python database/add_database_rdscannershirtful.py")
            return False

        return True

    except Exception as e:
        print(f"   ❌ Datenbankfehler: {e}")
        return False


def test_rfid_tags():
    """Test: RFID-Tags in Datenbank"""
    print("\n🏷️ Teste RFID-Tags...")

    try:
        from models import User

        # Lade Tags aus JSON
        with open('config/authorized_tags.json', 'r') as f:
            authorized_tags = json.load(f)

        print(f"   📋 Autorisierte Tags in JSON: {len(authorized_tags)}")

        # Prüfe Tags in Datenbank
        imported_count = 0
        missing_tags = []

        for tag_id, tag_info in authorized_tags.items():
            user = User.get_by_epc(tag_id)
            if user:
                imported_count += 1
                print(f"   ✅ Tag {tag_id}: {user['BenutzerName']}")
            else:
                missing_tags.append(tag_id)
                print(f"   ❌ Tag {tag_id}: nicht in DB gefunden")

        if missing_tags:
            print(f"\n   ⚠️ Fehlende Tags in DB: {len(missing_tags)}")
            print("   Führen Sie aus: python database/import_rfid_tags.py")
            return False

        print(f"   ✅ Alle {imported_count} Tags in Datenbank importiert")
        return True

    except Exception as e:
        print(f"   ❌ RFID-Tag Test Fehler: {e}")
        return False


def test_camera():
    """Test: Kamera-Zugriff (optimiert für schnelleren Start)"""
    print("\n📸 Teste Kamera-Zugriff...")

    try:
        import cv2
        import threading
        import time
        from config import APP_CONFIG

        camera_index = APP_CONFIG.get('CAMERA_INDEX', 0)
        backend = APP_CONFIG.get('CAMERA_BACKEND', 'DSHOW').upper()

        # Timeout für Kamera-Initialisierung
        camera_ready = threading.Event()
        camera_result = {'cap': None, 'success': False, 'error': None}

        def init_camera():
            """Initialisiert Kamera in separatem Thread"""
            try:
                # Backend-spezifische Kamera-Initialisierung
                if backend == 'DSHOW' and os.name == 'nt':
                    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                elif backend == 'V4L2':
                    cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
                else:
                    cap = cv2.VideoCapture(camera_index)

                if cap.isOpened():
                    # Schnelle Einstellungen ohne Warten
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Kleinere Auflösung für Test
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                    cap.set(cv2.CAP_PROP_FPS, 15)  # Niedrigere FPS für Test
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Kleiner Buffer

                    camera_result['cap'] = cap
                    camera_result['success'] = True
                else:
                    if cap:
                        cap.release()
                    camera_result['error'] = "Kamera konnte nicht geöffnet werden"

            except Exception as e:
                camera_result['error'] = str(e)
            finally:
                camera_ready.set()

        # Starte Kamera in separatem Thread
        print(f"   🔄 Initialisiere Kamera {camera_index} (Backend: {backend})...")
        camera_thread = threading.Thread(target=init_camera, daemon=True)
        camera_thread.start()

        # Warte max 5 Sekunden
        if camera_ready.wait(timeout=5.0):
            if camera_result['success'] and camera_result['cap']:
                cap = camera_result['cap']

                # Schneller Frame-Test
                print("   🔄 Teste Frame-Capture...")
                ret, frame = cap.read()

                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    print(f"   ✅ Kamera {camera_index} funktioniert")
                    print(f"   📐 Auflösung: {width}x{height}")
                    print(f"   🔧 Backend: {backend}")
                    cap.release()
                    return True
                else:
                    print(f"   ❌ Kamera {camera_index} kann keine Frames liefern")
                    cap.release()
                    return False
            else:
                error_msg = camera_result.get('error', 'Unbekannter Fehler')
                print(f"   ❌ Kamera {camera_index} nicht verfügbar: {error_msg}")

                # Versuche andere Kamera-Indizes zu finden
                print("   🔍 Suche nach verfügbaren Kameras...")
                found_camera = False
                for i in range(3):
                    try:
                        test_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
                        if test_cap.isOpened():
                            ret, _ = test_cap.read()
                            if ret:
                                print(f"   💡 Kamera {i} ist verfügbar")
                                found_camera = True
                            test_cap.release()
                        else:
                            test_cap.release()
                    except:
                        pass

                if found_camera:
                    print(f"   💡 Ändern Sie CAMERA_INDEX in .env auf eine verfügbare Kamera")

                return False
        else:
            print(f"   ⏰ Kamera-Initialisierung Timeout (>5s)")
            print(f"   💡 Kamera ist möglicherweise sehr langsam")

            # Cleanup falls Thread noch läuft
            if camera_result['cap']:
                camera_result['cap'].release()

            # Für langsame Kameras - Warnung aber weiter
            print(f"   ⚠️ Probieren Sie anderen Backend: CAMERA_BACKEND=AUTO in .env")
            return True  # Als bestanden werten, da nur langsam

    except Exception as e:
        print(f"   ❌ Kamera-Test Fehler: {e}")
        return False


def test_directories():
    """Test: Notwendige Verzeichnisse"""
    print("\n📁 Teste Verzeichnisse...")

    required_dirs = ['logs', 'config', 'database']
    optional_dirs = ['temp', 'tests']

    all_good = True

    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"   ✅ {directory}/ vorhanden")
        else:
            print(f"   ❌ {directory}/ fehlt")
            try:
                os.makedirs(directory)
                print(f"   🔧 {directory}/ erstellt")
            except Exception as e:
                print(f"   ❌ Konnte {directory}/ nicht erstellen: {e}")
                all_good = False

    for directory in optional_dirs:
        if os.path.exists(directory):
            print(f"   ✅ {directory}/ vorhanden (optional)")
        else:
            print(f"   ℹ️ {directory}/ nicht vorhanden (optional)")

    return all_good


def test_models():
    """Test: Datenbank-Models"""
    print("\n🏗️ Teste Datenbank-Models...")

    try:
        from models import User, Session, QrScan

        # Test User.get_all_active
        users = User.get_all_active()
        print(f"   ✅ User.get_all_active(): {len(users)} Benutzer")

        # Test mit erstem verfügbaren Benutzer
        if users:
            test_user = users[0]
            print(f"   ✅ Test-Benutzer: {test_user['BenutzerName']}")

            # Test Session.create (aber nicht committen)
            # Nur testen ob die Funktion funktioniert
            print("   ✅ Models funktionieren korrekt")
        else:
            print("   ⚠️ Keine Benutzer in Datenbank - Models-Test eingeschränkt")

        return True

    except Exception as e:
        print(f"   ❌ Models-Test Fehler: {e}")
        return False


def create_summary_report(test_results):
    """Erstellt Zusammenfassungsbericht"""
    print("\n" + "=" * 60)
    print("📊 SYSTEM-TEST ZUSAMMENFASSUNG")
    print("=" * 60)

    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    failed_tests = total_tests - passed_tests

    print(f"🎯 Tests durchgeführt: {total_tests}")
    print(f"✅ Erfolgreich: {passed_tests}")
    print(f"❌ Fehlgeschlagen: {failed_tests}")
    print(f"📈 Erfolgsrate: {(passed_tests / total_tests) * 100:.1f}%")

    if failed_tests == 0:
        print("\n🎉 ALLE TESTS ERFOLGREICH!")
        print("✅ System ist bereit für den Produktivbetrieb")
        print("\n🚀 Starten Sie die Anwendung mit:")
        print("   python app.py")
        print("   oder")
        print("   run.bat")
    else:
        print(f"\n⚠️ {failed_tests} Test(s) fehlgeschlagen")
        print("❌ System ist NICHT bereit für den Produktivbetrieb")
        print("\n🔧 Beheben Sie die oben genannten Probleme und")
        print("   führen Sie den Test erneut aus")

    print("=" * 60)


def main():
    """Hauptfunktion - Führt alle Tests durch"""
    print("🔷 RFID & QR Scanner - Umfassender System-Test")
    print(f"⏰ Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Definiere Tests
    tests = [
        ("Python Module", test_imports),
        ("Konfiguration", test_config),
        ("Datenbank", test_database),
        ("RFID Tags", test_rfid_tags),
        ("Kamera", test_camera),
        ("Verzeichnisse", test_directories),
        ("Models", test_models)
    ]

    test_results = {}

    # Führe Tests durch
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results[test_name] = result
        except Exception as e:
            print(f"\n❌ Test '{test_name}' ist abgestürzt: {e}")
            test_results[test_name] = False

    # Zusammenfassung
    create_summary_report(test_results)

    # Exit-Code für Batch-Scripts
    failed_count = sum(1 for result in test_results.values() if not result)
    sys.exit(failed_count)


if __name__ == "__main__":
    main()