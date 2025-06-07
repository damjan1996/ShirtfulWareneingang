#!/usr/bin/env python3
"""
Angepasste TS-HRW380 RFID-Anwendung
Speziell für Ihren Reader im HID-Modus optimiert

Installation: pip install pynput
"""

from pynput import keyboard
from datetime import datetime
import json
import os
import threading
import time


class CustomRFIDApp:
    def __init__(self):
        self.hid_data = ""
        self.listener = None
        self.is_running = False
        self.tag_log_file = "rfid_tags.json"
        self.authorized_tags = self.load_authorized_tags()

    def load_authorized_tags(self):
        """Autorisierte Tags aus Datei laden"""
        authorized_file = "authorized_tags.json"
        if os.path.exists(authorized_file):
            try:
                with open(authorized_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        # Standard-autorisierte Tags (können Sie anpassen)
        default_tags = {
            "53004ECD68": {"name": "Damjan", "access_level": "user"},
            "53004E114B": {"name": "Ana", "access_level": "user"},
        }
        self.save_authorized_tags(default_tags)
        return default_tags

    def save_authorized_tags(self, tags):
        """Autorisierte Tags speichern"""
        with open("authorized_tags.json", 'w') as f:
            json.dump(tags, f, indent=2)

    def log_tag_access(self, tag_id, timestamp, authorized):
        """Tag-Zugriff protokollieren"""
        log_entry = {
            "timestamp": timestamp,
            "tag_id": tag_id,
            "authorized": authorized,
            "tag_info": self.authorized_tags.get(tag_id, {"name": "Unbekannt"})
        }

        # In JSON-Datei speichern
        log_data = []
        if os.path.exists(self.tag_log_file):
            try:
                with open(self.tag_log_file, 'r') as f:
                    log_data = json.load(f)
            except:
                pass

        log_data.append(log_entry)

        # Nur die letzten 1000 Einträge behalten
        if len(log_data) > 1000:
            log_data = log_data[-1000:]

        with open(self.tag_log_file, 'w') as f:
            json.dump(log_data, f, indent=2)

    def process_tag(self, tag_id):
        """Tag verarbeiten und Aktionen ausführen"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prüfen ob Tag autorisiert ist
        if tag_id in self.authorized_tags:
            tag_info = self.authorized_tags[tag_id]
            print(f"✅ [{timestamp}] ZUGRIFF GEWÄHRT")
            print(f"   Tag: {tag_id}")
            print(f"   Name: {tag_info.get('name', 'Unbekannt')}")
            print(f"   Level: {tag_info.get('access_level', 'user')}")

            # Hier können Sie Aktionen für autorisierten Zugriff hinzufügen:
            self.grant_access(tag_info)

            self.log_tag_access(tag_id, timestamp, True)

        else:
            print(f"❌ [{timestamp}] ZUGRIFF VERWEIGERT")
            print(f"   Unbekannter Tag: {tag_id}")

            # Aktion für unautorisierten Zugriff
            self.deny_access()

            self.log_tag_access(tag_id, timestamp, False)

        print("-" * 50)

    def grant_access(self, tag_info):
        """Aktionen bei autorisiertem Zugriff"""
        access_level = tag_info.get('access_level', 'user')

        if access_level == 'admin':
            print("🔓 Administrator-Zugriff gewährt")
            # Hier Admin-spezifische Aktionen
        elif access_level == 'user':
            print("🔓 Benutzer-Zugriff gewährt")
            # Hier Benutzer-spezifische Aktionen

        # Beispiel-Aktionen (anpassen nach Bedarf):
        # - Türschloss öffnen
        # - LED anschalten
        # - Email senden
        # - API-Aufruf
        # - etc.

    def deny_access(self):
        """Aktionen bei verweigertem Zugriff"""
        print("🔒 Zugriff verweigert - Sicherheitsprotokoll aktiviert")

        # Beispiel-Aktionen:
        # - Alarm auslösen
        # - Sicherheitspersonal benachrichtigen
        # - Foto aufnehmen
        # - etc.

    def add_new_tag(self, tag_id, name, access_level="user"):
        """Neuen autorisierten Tag hinzufügen"""
        self.authorized_tags[tag_id] = {
            "name": name,
            "access_level": access_level,
            "added_date": datetime.now().isoformat()
        }
        self.save_authorized_tags(self.authorized_tags)
        print(f"✅ Tag {tag_id} als '{name}' hinzugefügt")

    def remove_tag(self, tag_id):
        """Tag aus autorisierten Tags entfernen"""
        if tag_id in self.authorized_tags:
            removed_tag = self.authorized_tags.pop(tag_id)
            self.save_authorized_tags(self.authorized_tags)
            print(f"🗑️ Tag {tag_id} ({removed_tag.get('name')}) entfernt")
            return True
        return False

    def show_statistics(self):
        """Zugriffs-Statistiken anzeigen"""
        if not os.path.exists(self.tag_log_file):
            print("📊 Keine Zugriffsdaten verfügbar")
            return

        try:
            with open(self.tag_log_file, 'r') as f:
                log_data = json.load(f)

            total_access = len(log_data)
            authorized_access = sum(1 for entry in log_data if entry['authorized'])
            unauthorized_access = total_access - authorized_access

            print("📊 Zugriffs-Statistiken:")
            print(f"   Gesamt: {total_access}")
            print(f"   Autorisiert: {authorized_access}")
            print(f"   Verweigert: {unauthorized_access}")

            # Letzte 5 Zugriffe
            print("\n🕒 Letzte 5 Zugriffe:")
            for entry in log_data[-5:]:
                status = "✅" if entry['authorized'] else "❌"
                print(
                    f"   {status} {entry['timestamp']} - {entry['tag_id']} ({entry['tag_info'].get('name', 'Unbekannt')})")

        except Exception as e:
            print(f"❌ Fehler beim Laden der Statistiken: {e}")

    def start_monitoring(self):
        """RFID-Monitoring starten"""
        self.is_running = True

        def on_key_press(key):
            if not self.is_running:
                return False

            try:
                if hasattr(key, 'char') and key.char:
                    self.hid_data += key.char
                elif key == keyboard.Key.enter:
                    if self.hid_data.strip():
                        self.process_tag(self.hid_data.strip())
                        self.hid_data = ""
            except:
                pass

        self.listener = keyboard.Listener(on_press=on_key_press)
        self.listener.start()

        print("🎯 RFID-Monitoring aktiv!")
        print("📱 Halten Sie RFID-Tags an den Reader...")
        print("⏹️ Drücken Sie 'q' + Enter zum Beenden")

        # Warten auf Benutzer-Input zum Beenden
        while self.is_running:
            try:
                user_input = input().strip().lower()
                if user_input == 'q':
                    self.stop_monitoring()
                    break
                elif user_input == 'stats':
                    self.show_statistics()
                elif user_input == 'help':
                    self.show_help()
            except KeyboardInterrupt:
                self.stop_monitoring()
                break

    def stop_monitoring(self):
        """RFID-Monitoring stoppen"""
        self.is_running = False
        if self.listener:
            self.listener.stop()
        print("⏹️ Monitoring gestoppt")

    def show_help(self):
        """Hilfe anzeigen"""
        print("\n💡 Verfügbare Befehle während des Monitorings:")
        print("   'q' + Enter: Beenden")
        print("   'stats' + Enter: Statistiken anzeigen")
        print("   'help' + Enter: Diese Hilfe anzeigen")
        print()


def main():
    app = CustomRFIDApp()

    print("=" * 60)
    print("🔷 Angepasste RFID-Zugriffskontrolle")
    print("🏷️ Ihr Tag wurde erkannt: 53004ECD68")
    print("=" * 60)

    while True:
        print("\n📋 Optionen:")
        print("1. RFID-Monitoring starten")
        print("2. Autorisierten Tag hinzufügen")
        print("3. Tag entfernen")
        print("4. Autorisierte Tags anzeigen")
        print("5. Zugriffs-Statistiken")
        print("6. Beenden")

        choice = input("\n🔹 Wählen Sie eine Option (1-6): ").strip()

        if choice == "1":
            app.start_monitoring()

        elif choice == "2":
            tag_id = input("🏷️ Tag-ID eingeben: ").strip()
            name = input("👤 Name eingeben: ").strip()
            level = input("🔐 Access Level (user/admin) [user]: ").strip() or "user"
            app.add_new_tag(tag_id, name, level)

        elif choice == "3":
            tag_id = input("🏷️ Zu entfernende Tag-ID: ").strip()
            if not app.remove_tag(tag_id):
                print("❌ Tag nicht gefunden")

        elif choice == "4":
            print("\n👥 Autorisierte Tags:")
            for tag_id, info in app.authorized_tags.items():
                print(f"   🏷️ {tag_id}: {info.get('name')} ({info.get('access_level')})")

        elif choice == "5":
            app.show_statistics()

        elif choice == "6":
            print("👋 Programm beendet")
            break

        else:
            print("❌ Ungültige Auswahl!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Programm beendet")
