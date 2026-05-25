"""Configuración global del proyecto."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = BASE_DIR / "resources"
SOUNDS_DIR = RESOURCES_DIR / "sounds"
UI_DIR = RESOURCES_DIR / "ui"
CHARACTERS_DIR = RESOURCES_DIR / "characters"
SCORES_FILE = BASE_DIR / "scores.json"

WINDOW_TITLE = "Fireboy & Watergirl"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 850

GAME_DURATION_SECONDS = 180
MAX_SCORES_SAVED = 10

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5050

MUSIC_VOLUME = 0.35
EFFECT_VOLUME = 0.75
