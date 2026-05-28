import json
from config import MAX_SCORES_SAVED, SCORES_FILE
from models.score import Score


# Guarda el historial individual de puntajes
class ScoreManager:
    # Inicializa los datos necesarios
    def __init__(self):
        self._scores = []
        self._load()

    # Lee los puntajes guardados
    def _load(self):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            self._scores = data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            self._scores = []

    # Guarda los puntajes en el archivo JSON
    def _save(self):
        try:
            with open(SCORES_FILE, "w", encoding="utf-8") as file:
                json.dump(self._scores, file, ensure_ascii=False, indent=2)
        except OSError as error:
            print(f"No se pudo guardar el historial: {error}")

    # Registra el resultado de un jugador
    def add_score(self, player_name: str, character: str, score: int, duration: int):
        result = Score.create(player_name, character, score, duration).to_dict()
        self._scores.append(result)
        self._scores.sort(key=lambda entry: (entry.get("score", 0), -entry.get("duration", 0)), reverse=True)
        self._scores = self._scores[:MAX_SCORES_SAVED]
        self._save()

    # Devuelve el historial
    def get_scores(self) -> list:
        return list(self._scores)

    # Limpia los puntajes guardados
    def clear(self):
        self._scores = []
        self._save()
