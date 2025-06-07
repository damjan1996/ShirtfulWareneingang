#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Player für Feedback-Sounds
================================

Spielt Audio-Feedback für verschiedene Ereignisse ab.
"""

import os
import logging
import threading
from typing import Dict, Optional
import winsound  # Windows-spezifisch

logger = logging.getLogger(__name__)


class AudioPlayer:
    """
    Verwaltet und spielt Audio-Feedback

    Features:
    - Vordefinierte System-Sounds
    - Benutzerdefinierte WAV-Dateien
    - Asynchrone Wiedergabe
    - Volume-Kontrolle über System
    """

    # Standard Windows System-Sounds
    SYSTEM_SOUNDS = {
        'success': winsound.MB_OK,
        'error': winsound.MB_ICONHAND,
        'warning': winsound.MB_ICONEXCLAMATION,
        'question': winsound.MB_ICONQUESTION,
        'info': winsound.MB_ICONASTERISK
    }

    def __init__(self, assets_dir: Optional[str] = None):
        """
        Initialisiert den Audio Player

        Args:
            assets_dir: Verzeichnis mit benutzerdefinierten Sounds
        """
        self.assets_dir = assets_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'assets', 'sounds'
        )

        # Benutzerdefinierte Sounds laden
        self.custom_sounds = self._load_custom_sounds()

        # Sound-Einstellungen
        self.enabled = True
        self.use_system_sounds = True

        logger.info(f"Audio Player initialisiert (Assets: {self.assets_dir})")

    def _load_custom_sounds(self) -> Dict[str, str]:
        """
        Lädt benutzerdefinierte Sound-Dateien

        Returns:
            Dict mit Sound-Namen und Dateipfaden
        """
        sounds = {}

        if os.path.exists(self.assets_dir):
            for filename in os.listdir(self.assets_dir):
                if filename.endswith('.wav'):
                    sound_name = filename[:-4]  # Ohne .wav
                    sounds[sound_name] = os.path.join(self.assets_dir, filename)
                    logger.debug(f"Sound geladen: {sound_name}")

        return sounds

    def play(self, sound_name: str, async_play: bool = True):
        """
        Spielt einen Sound ab

        Args:
            sound_name: Name des Sounds
            async_play: Asynchron abspielen (nicht blockierend)
        """
        if not self.enabled:
            return

        if async_play:
            threading.Thread(
                target=self._play_sound,
                args=(sound_name,),
                daemon=True
            ).start()
        else:
            self._play_sound(sound_name)

    def _play_sound(self, sound_name: str):
        """
        Interne Methode zum Abspielen eines Sounds

        Args:
            sound_name: Name des Sounds
        """
        try:
            # 1. Benutzerdefinierte Sounds prüfen
            if sound_name in self.custom_sounds:
                winsound.PlaySound(
                    self.custom_sounds[sound_name],
                    winsound.SND_FILENAME
                )
                logger.debug(f"Custom sound gespielt: {sound_name}")
                return

            # 2. System-Sounds prüfen
            if self.use_system_sounds and sound_name in self.SYSTEM_SOUNDS:
                winsound.MessageBeep(self.SYSTEM_SOUNDS[sound_name])
                logger.debug(f"System sound gespielt: {sound_name}")
                return

            # 3. Standard-Beep als Fallback
            if sound_name == 'beep':
                winsound.Beep(800, 200)  # 800Hz, 200ms
                return

            logger.warning(f"Sound nicht gefunden: {sound_name}")

        except Exception as e:
            logger.error(f"Fehler beim Abspielen von {sound_name}: {e}")

    def play_success(self):
        """Spielt Success-Sound"""
        self.play('success')

    def play_error(self):
        """Spielt Error-Sound"""
        self.play('error')

    def play_warning(self):
        """Spielt Warning-Sound"""
        self.play('warning')

    def play_scan(self):
        """Spielt Scan-Sound"""
        # Zuerst custom 'scan' sound, dann 'success' als Fallback
        if 'scan' in self.custom_sounds:
            self.play('scan')
        else:
            self.play('success')

    def play_login(self):
        """Spielt Login-Sound"""
        if 'login' in self.custom_sounds:
            self.play('login')
        else:
            self.play('info')

    def play_logout(self):
        """Spielt Logout-Sound"""
        if 'logout' in self.custom_sounds:
            self.play('logout')
        else:
            self.play('info')

    def beep(self, frequency: int = 800, duration: int = 200):
        """
        Spielt einen benutzerdefinierten Beep

        Args:
            frequency: Frequenz in Hz
            duration: Dauer in Millisekunden
        """
        if not self.enabled:
            return

        try:
            winsound.Beep(frequency, duration)
        except Exception as e:
            logger.error(f"Fehler beim Beep: {e}")

    def enable(self):
        """Aktiviert Audio-Feedback"""
        self.enabled = True
        logger.info("Audio-Feedback aktiviert")

    def disable(self):
        """Deaktiviert Audio-Feedback"""
        self.enabled = False
        logger.info("Audio-Feedback deaktiviert")

    def set_use_system_sounds(self, use: bool):
        """
        Aktiviert/Deaktiviert System-Sounds

        Args:
            use: True für System-Sounds
        """
        self.use_system_sounds = use
        logger.debug(f"System-Sounds: {'aktiviert' if use else 'deaktiviert'}")

    def add_custom_sound(self, name: str, file_path: str) -> bool:
        """
        Fügt einen benutzerdefinierten Sound hinzu

        Args:
            name: Name des Sounds
            file_path: Pfad zur WAV-Datei

        Returns:
            bool: True wenn erfolgreich
        """
        if not os.path.exists(file_path):
            logger.error(f"Sound-Datei nicht gefunden: {file_path}")
            return False

        if not file_path.endswith('.wav'):
            logger.error(f"Nur WAV-Dateien unterstützt: {file_path}")
            return False

        self.custom_sounds[name] = file_path
        logger.info(f"Custom Sound hinzugefügt: {name}")
        return True

    def get_available_sounds(self) -> list:
        """
        Gibt eine Liste aller verfügbaren Sounds zurück

        Returns:
            Liste mit Sound-Namen
        """
        sounds = list(self.custom_sounds.keys())
        if self.use_system_sounds:
            sounds.extend(self.SYSTEM_SOUNDS.keys())
        sounds.append('beep')
        return sorted(set(sounds))


# Globale Instanz für einfachen Zugriff
_audio_player = None


def get_audio_player() -> AudioPlayer:
    """
    Gibt die globale AudioPlayer-Instanz zurück

    Returns:
        AudioPlayer-Instanz
    """
    global _audio_player
    if _audio_player is None:
        _audio_player = AudioPlayer()
    return _audio_player


# Test-Funktion
if __name__ == "__main__":
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("🔊 Audio Player Test")
    print("=" * 40)

    player = AudioPlayer()

    # Verfügbare Sounds anzeigen
    print(f"Verfügbare Sounds: {player.get_available_sounds()}")
    print()

    # Test-Sounds abspielen
    tests = [
        ("Success", lambda: player.play_success()),
        ("Error", lambda: player.play_error()),
        ("Warning", lambda: player.play_warning()),
        ("Scan", lambda: player.play_scan()),
        ("Login", lambda: player.play_login()),
        ("Logout", lambda: player.play_logout()),
        ("Beep 400Hz", lambda: player.beep(400, 300)),
        ("Beep 800Hz", lambda: player.beep(800, 300)),
        ("Beep 1200Hz", lambda: player.beep(1200, 300)),
    ]

    import time

    for name, play_func in tests:
        print(f"▶️ Spiele: {name}")
        play_func()
        time.sleep(1)

    print("\n✅ Test abgeschlossen")