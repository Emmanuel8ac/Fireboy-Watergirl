"""Score data model."""

from datetime import datetime


class Score:
    def __init__(self, players: str, score: int, duration: int, date: str):
        self.players = players
        self.score = int(score)
        self.duration = int(duration)
        self.date = date

    @classmethod
    def create(cls, players: str, score: int, duration: int):
        return cls(
            players=players,
            score=int(score),
            duration=int(duration),
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

    def to_dict(self) -> dict:
        return {
            "players": self.players,
            "score": self.score,
            "duration": self.duration,
            "date": self.date,
        }