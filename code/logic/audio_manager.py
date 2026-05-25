from pathlib import Path
from config import SOUNDS_DIR, MUSIC_VOLUME, EFFECT_VOLUME


def _first_existing(*names: str) -> str:
    for name in names:
        path = Path(SOUNDS_DIR) / name
        if path.exists():
            return str(path)
    return ""


TRACKS = {
    "menu": _first_existing("Menu_Sound.mp3", "menu_music.wav", "menu_sound.mp3"),
    "intro": _first_existing("Menu_Sound.mp3", "menu_music.wav", "menu_sound.mp3"),
    "game": _first_existing("game_music.wav", "898_Adv_Sound.mp3", "Menu_Sound.mp3"),
}

EFFECTS = {
    "click": _first_existing("click.wav", "Navis_Sound.wav"),
    "point": _first_existing("point.wav", "911_Diamond_Sound.mp3", "Diamond_Sound.mp3"),
    "jump": _first_existing("Jump1_Sound.wav", "901_Jump2_Sound.wav"),
    "door": _first_existing("899_Finish1.mp3", "900_Finish2.mp3"),
    "over": _first_existing("909_Over_Sound.mp3"),
}


class AudioManager:
    def __init__(self):
        self._backend = "silent"
        self._music_vol = MUSIC_VOLUME
        self._effect_vol = EFFECT_VOLUME
        self._enabled = True
        self._effects_cache = []
        self._init_backend()

    def _init_backend(self):
        try:
            from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QSoundEffect
            from PySide6.QtCore import QUrl
            self._QMediaPlayer = QMediaPlayer
            self._QAudioOutput = QAudioOutput
            self._QSoundEffect = QSoundEffect
            self._QUrl = QUrl
            self._player = QMediaPlayer()
            self._audio_out = QAudioOutput()
            self._player.setAudioOutput(self._audio_out)
            self._audio_out.setVolume(self._music_vol)
            self._backend = "qt"
            return
        except Exception:
            pass

        try:
            import pygame
            pygame.mixer.init()
            self._pygame = pygame
            self._backend = "pygame"
            return
        except Exception:
            pass

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
        if not path or not Path(path).is_file():
            return
        if self._backend == "qt":
            self._player.setSource(self._QUrl.fromLocalFile(str(Path(path).resolve())))
            try:
                self._player.setLoops(-1 if loop else 1)
            except Exception:
                pass
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
        self._music_vol = max(0.0, min(1.0, float(vol)))
        if self._backend == "qt":
            self._audio_out.setVolume(self._music_vol)
        elif self._backend == "pygame":
            self._pygame.mixer.music.set_volume(self._music_vol)

    def play_effect(self, effect_name: str):
        if not self._enabled:
            return
        path = EFFECTS.get(effect_name, "")
        if not path or not Path(path).is_file():
            return
        if self._backend == "qt":
            fx = self._QSoundEffect()
            fx.setSource(self._QUrl.fromLocalFile(str(Path(path).resolve())))
            fx.setVolume(self._effect_vol)
            fx.play()
            self._effects_cache.append(fx)
            if len(self._effects_cache) > 12:
                self._effects_cache = self._effects_cache[-12:]
        elif self._backend == "pygame":
            try:
                snd = self._pygame.mixer.Sound(path)
                snd.set_volume(self._effect_vol)
                snd.play()
            except Exception:
                pass
