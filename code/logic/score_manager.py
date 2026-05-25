import json
from datetime import datetime
from config import MAX_SCORES_SAVED, SCORES_FILE


class ScoreManager:
    def __init__(self):
        self._scores = []
        self._load()

    def _load(self):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._scores = data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            self._scores = []

    def _save(self):
        try:
            with open(SCORES_FILE, "w", encoding="utf-8") as f:
                json.dump(self._scores, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"[ScoreManager] No se pudo guardar: {e}")

    def add_score(self, players: str, score: int, duration: int):
        self._scores.append({
            "players": players,
            "score": int(score),
            "duration": int(duration),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self._scores.sort(key=lambda x: (x.get("score", 0), -x.get("duration", 0)), reverse=True)
        self._scores = self._scores[:MAX_SCORES_SAVED]
        self._save()

    def get_scores(self) -> list:
        return list(self._scores)

    def clear(self):
        self._scores = []
        self._save()
