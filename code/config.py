"""Configuración global del proyecto."""
from pathlib import Path

# Rutas principales del proyecto
BASE_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = BASE_DIR / "resources"
IMAGES_DIR = RESOURCES_DIR / "images"
AUDIO_DIR = RESOURCES_DIR / "audio"
STYLES_DIR = RESOURCES_DIR / "styles"
ORIGINAL_DIR = RESOURCES_DIR / "original"

# Carpetas usadas por la interfaz y el juego
SOUNDS_DIR = AUDIO_DIR
UI_DIR = IMAGES_DIR / "ui"
CHARACTERS_DIR = IMAGES_DIR / "characters"
LEVELS_DIR = IMAGES_DIR / "levels"
TEXTURES_DIR = IMAGES_DIR / "textures"
ELEMENTS_DIR = IMAGES_DIR / "elements"
SCORES_FILE = BASE_DIR / "scores.json"

# Tamaño de la ventana
WINDOW_TITLE = "Fireboy & Watergirl"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 850

# Reglas de partida y conexión
GAME_DURATION_SECONDS = 180
MAX_SCORES_SAVED = 20

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5050

# Volumen del audio
MUSIC_VOLUME = 0.35
EFFECT_VOLUME = 0.75
