import os

MUSIC_VOLUME = 0.5
EFFECT_VOLUME = 0.7

_SOUNDS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "resources", "sounds"
)

TRACKS = {
    "menu": os.path.join(_SOUNDS_DIR, "menu_sound.mp3"),
    "game": os.path.join(_SOUNDS_DIR, "game_music.wav"),
    "game": os.path.join(_SOUNDS_DIR, "game_music.wav"),
}

EFFECTS = {
    "click": os.path.join(_SOUNDS_DIR, "click.wav"),
    "point": os.path.join(_SOUNDS_DIR, "point.wav"),
}


class AudioManager:

    def __init__(self):
        self._backend    = "silent"
        self._music_vol  = MUSIC_VOLUME
        self._effect_vol = EFFECT_VOLUME
        self._enabled    = True
        self._init_backend()

    def _init_backend(self):
        try:
            from PySide6.QtMultimedia import (
                QMediaPlayer, QAudioOutput, QSoundEffect
            )
            from PySide6.QtCore import QUrl

            self._QMediaPlayer = QMediaPlayer
            self._QAudioOutput = QAudioOutput
            self._QSoundEffect = QSoundEffect
            self._QUrl         = QUrl

            self._player    = QMediaPlayer()
            self._audio_out = QAudioOutput()
            self._player.setAudioOutput(self._audio_out)
            self._audio_out.setVolume(self._music_vol)

            self._backend = "qt"
            print("[Audio] Backend: PySide6.QtMultimedia")
            return
        except Exception:
            pass

        try:
            import pygame
            pygame.mixer.init()
            self._pygame  = pygame
            self._backend = "pygame"
            print("[Audio] Backend: pygame.mixer")
            return
        except Exception:
            pass

        print("[Audio] Sin backend — modo silencioso")

    def toggle_audio(self):
        self._enabled = not self._enabled

        if not self._enabled:
            self.stop_music()

        return self._enabled

    def is_enabled(self):
        return self._enabled

    def play_music(self, track_name: str, loop: bool = True):
        if not self._enabled:
            return

        path = TRACKS.get(track_name, "")
        if not os.path.isfile(path):
            print(f"[Audio] No se encontró música: {track_name}")
            return

        if self._backend == "qt":
            self._player.setSource(
                self._QUrl.fromLocalFile(os.path.abspath(path))
            )
            self._player.setLoops(-1 if loop else 1)
            self._player.play()

        elif self._backend == "pygame":
            self._pygame.mixer.music.load(path)
            self._pygame.mixer.music.set_volume(self._music_vol)
            self._pygame.mixer.music.play(-1 if loop else 0)

    def stop_music(self):
        if self._backend == "qt":
            self._player.stop()
        elif self._backend == "pygame":
            self._pygame.mixer.music.stop()

    def pause_music(self):
        if self._backend == "qt":
            self._player.pause()
        elif self._backend == "pygame":
            self._pygame.mixer.music.pause()

    def resume_music(self):
        if not self._enabled:
            return

        if self._backend == "qt":
            self._player.play()
        elif self._backend == "pygame":
            self._pygame.mixer.music.unpause()

    def set_music_volume(self, vol: float):
        self._music_vol = max(0.0, min(1.0, vol))
        if self._backend == "qt":
            self._audio_out.setVolume(self._music_vol)
        elif self._backend == "pygame":
            self._pygame.mixer.music.set_volume(self._music_vol)

    def play_effect(self, effect_name: str):
        if not self._enabled:
            return

        path = EFFECTS.get(effect_name, "")
        if not os.path.isfile(path):
            print(f"[Audio] No se encontró efecto: {effect_name}")
            return

        if self._backend == "qt":
            fx = self._QSoundEffect()
            fx.setSource(self._QUrl.fromLocalFile(os.path.abspath(path)))
            fx.setVolume(self._effect_vol)
            fx.play()

        elif self._backend == "pygame":
            try:
                snd = self._pygame.mixer.Sound(path)
                snd.set_volume(self._effect_vol)
                snd.play()
            except Exception as e:
                print(f"[Audio] Error efecto: {e}")