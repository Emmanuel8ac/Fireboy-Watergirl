from pathlib import Path
from typing import Dict, List, Optional

from config import SOUNDS_DIR, MUSIC_VOLUME, EFFECT_VOLUME

# Rutas de archivos de audio
def _first_existing(*names: str) -> str:
    for name in names:
        path = Path(SOUNDS_DIR) / name
        if path.exists():
            return str(path)
    return ""


TRACKS: Dict[str, str] = {
    "menu": _first_existing("Menu_Sound.mp3", "menu_music.wav"),
    "intro": _first_existing("Menu_Sound.mp3", "menu_music.wav"),
    "game": _first_existing("898_Adv_Sound.mp3", "game_music.wav", "Menu_Sound.mp3"),
}

EFFECTS: Dict[str, str] = {
    "click": _first_existing("Navis_Sound.wav", "click.wav"),
    "jump_fire": _first_existing("Jump1_Sound.wav", "901_Jump2_Sound.wav"),
    "jump_water": _first_existing("901_Jump2_Sound.wav", "Jump1_Sound.wav"),
    "jump": _first_existing("Jump1_Sound.wav", "901_Jump2_Sound.wav"),
    "diamond": _first_existing("911_Diamond_Sound.mp3", "point.wav"),
    "point": _first_existing("911_Diamond_Sound.mp3", "point.wav"),
    "lever": _first_existing("908_Lever_Sound.mp3", "Navis_Sound.wav", "click.wav"),
    "platform": _first_existing("907_Platform_Sound.wav", "137_Pusher_Sound.mp3"),
    "pusher": _first_existing("137_Pusher_Sound.mp3", "907_Platform_Sound.wav"),
    "door": _first_existing("906_Door_Sound.flv", "899_Finish1.mp3", "900_Finish2.mp3"),
    "finish": _first_existing("899_Finish1.mp3", "900_Finish2.mp3"),
    "game_over": _first_existing("909_Over_Sound.mp3"),
    "over": _first_existing("909_Over_Sound.mp3"),
    "wind": _first_existing("910_Wind_Sound.flv"),
    "speed": _first_existing("Speed_Sound.mp3"),
}

FALLBACKS: Dict[str, List[str]] = {
    "door": ["899_Finish1.mp3", "900_Finish2.mp3"],
    "wind": ["898_Adv_Sound.mp3"],
}


class AudioManager:
    # Inicio y configuración
    def __init__(self):
        self._backend = "silent"
        self._music_vol = max(0.0, min(1.0, float(MUSIC_VOLUME)))
        self._effect_vol = max(0.0, min(1.0, float(EFFECT_VOLUME)))
        self._enabled = True
        self._current_track: Optional[str] = None
        self._current_loop = True
        self._effect_players: List[object] = []
        self._effect_outputs: List[object] = []
        self._effect_cache: Dict[str, object] = {}
        self._init_backend()

    def _init_backend(self):
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QSoundEffect
        except Exception:
            self._backend = "silent"
            return

        self._QUrl = QUrl
        self._QAudioOutput = QAudioOutput
        self._QMediaPlayer = QMediaPlayer
        self._QSoundEffect = QSoundEffect
        self._music_player = QMediaPlayer()
        self._music_output = QAudioOutput()
        self._music_player.setAudioOutput(self._music_output)
        self._music_output.setVolume(self._music_vol)
        self._backend = "qt"

    def _resolve_effect(self, effect_name: str) -> str:
        path = EFFECTS.get(effect_name, "")
        if path and Path(path).is_file() and Path(path).suffix.lower() != ".flv":
            return path

        for name in FALLBACKS.get(effect_name, []):
            alt = Path(SOUNDS_DIR) / name
            if alt.exists():
                return str(alt)
        return path if path and Path(path).is_file() else ""

    # Estado del audio
    def toggle_audio(self) -> bool:
        self._enabled = not self._enabled
        if self._enabled and self._current_track:
            self.play_music(self._current_track, self._current_loop)
        else:
            self.stop_all()
        return self._enabled

    def set_enabled(self, enabled: bool):
        if self._enabled != enabled:
            self.toggle_audio()

    def is_enabled(self) -> bool:
        return self._enabled

    # Música de fondo
    def play_music(self, track_name: str, loop: bool = True):
        self._current_track = track_name
        self._current_loop = loop
        path = TRACKS.get(track_name, "")
        if not self._enabled or self._backend != "qt" or not Path(path).is_file():
            return

        self._music_player.setSource(self._QUrl.fromLocalFile(str(Path(path).resolve())))
        try:
            self._music_player.setLoops(-1 if loop else 1)
        except Exception:
            pass
        self._music_output.setVolume(self._music_vol)
        self._music_player.play()

    def stop_music(self):
        if self._backend == "qt":
            self._music_player.stop()

    def pause_music(self):
        if self._backend == "qt":
            self._music_player.pause()

    def resume_music(self):
        if self._enabled and self._backend == "qt":
            self._music_player.play()

    def stop_all(self):
        self.stop_music()
        for player in self._effect_players:
            try:
                player.stop()
            except Exception:
                pass

    # Volumen y efectos
    def set_music_volume(self, vol: float):
        self._music_vol = max(0.0, min(1.0, float(vol)))
        if self._backend == "qt":
            self._music_output.setVolume(self._music_vol if self._enabled else 0.0)

    def set_effect_volume(self, vol: float):
        self._effect_vol = max(0.0, min(1.0, float(vol)))

    def play_effect(self, effect_name: str):
        path = self._resolve_effect(effect_name)
        if not self._enabled or self._backend != "qt" or not path:
            return

        suffix = Path(path).suffix.lower()
        if suffix == ".wav":
            self._play_wav_effect(path)
        else:
            self._play_media_effect(path)

    def _play_wav_effect(self, path: str):
        effect = self._effect_cache.get(path)
        if effect is None:
            effect = self._QSoundEffect()
            effect.setSource(self._QUrl.fromLocalFile(str(Path(path).resolve())))
            self._effect_cache[path] = effect
        effect.setVolume(self._effect_vol)
        effect.play()

    def _play_media_effect(self, path: str):
        player = self._QMediaPlayer()
        output = self._QAudioOutput()
        output.setVolume(self._effect_vol)
        player.setAudioOutput(output)
        player.setSource(self._QUrl.fromLocalFile(str(Path(path).resolve())))
        player.play()

        self._effect_players.append(player)
        self._effect_outputs.append(output)
        self._effect_players = self._effect_players[-10:]
        self._effect_outputs = self._effect_outputs[-10:]
