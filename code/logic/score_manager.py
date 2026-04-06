import json
import os
from config import MAX_SCORES_SAVED

_SCORES_FILE = os.path.join(
    os.path.dirname(__file__), "..", "scores.json"
)


class ScoreManager:

    def __init__(self):
        self._scores: list = []
        self._load()

    def _load(self):
        try:
            with open(_SCORES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._scores = data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            self._scores = self._default_scores()

    def _save(self):
        try:
            with open(_SCORES_FILE, "w", encoding="utf-8") as f:
                json.dump(self._scores, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"[ScoreManager] No se pudo guardar: {e}")

    @staticmethod
    def _default_scores() -> list:
        return [
            {"players": "Fireboy & Watergirl", "score": 100, "duration": 45},
            {"players": "Jugador1 & Jugador2", "score": 85, "duration": 52},
            {"players": "Equipo X", "score": 70, "duration": 60},
            {"players": "Equipo Y", "score": 60, "duration": 58},
        ]

    def add_score(self, players: str, score: int, duration: int):
        self._scores.append(
            {"players": players, "score": score, "duration": duration}
        )
        self._scores.sort(key=lambda x: x["score"], reverse=True)
        self._scores = self._scores[:MAX_SCORES_SAVED]
        self._save()

    def get_scores(self) -> list:
        return list(self._scores)

    def clear(self):
        self._scores = []
        self._save()