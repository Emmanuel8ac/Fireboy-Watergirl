from datetime import datetime

# Resultado individual de un jugador
class Score:
    # Inicializa los datos necesarios
    def __init__(self, player_name: str, character: str, score: int, duration: int, date: str):
        self.player_name = player_name
        self.character = character
        self.score = int(score)
        self.duration = int(duration)
        self.date = date

    # Crea un registro con la fecha actual
    @classmethod
    def create(cls, player_name: str, character: str, score: int, duration: int):
        return cls(
            player_name=player_name,
            character=character,
            score=int(score),
            duration=int(duration),
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

    # Convierte el resultado para guardarlo
    def to_dict(self) -> dict:
        return {
            "player_name": self.player_name,
            "character": self.character,
            "score": self.score,
            "duration": self.duration,
            "date": self.date,
        }