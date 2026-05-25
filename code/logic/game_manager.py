from PySide6.QtCore import QObject, QTimer, Signal
from config import GAME_DURATION_SECONDS


class GameManager(QObject):
    tick = Signal(int)
    score_changed = Signal(int, int)
    game_over = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player1 = "Fireboy"
        self._player2 = "Watergirl"
        self._score1 = 0
        self._score2 = 0
        self._time_left = GAME_DURATION_SECONDS
        self._running = False

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)

    def setup(self, player1: str, player2: str):
        self._player1 = player1 or "Fireboy"
        self._player2 = player2 or "Watergirl"

    def start(self):
        self._score1 = 0
        self._score2 = 0
        self._time_left = GAME_DURATION_SECONDS
        self._running = True
        self._timer.start()
        self.score_changed.emit(self._score1, self._score2)
        self.tick.emit(self._time_left)

    def finish(self):
        if not self._running:
            return
        self._running = False
        self._timer.stop()
        self.game_over.emit(self._score1, self._score2)

    def abort(self):
        self._running = False
        self._timer.stop()

    def pause(self):
        if self._running:
            self._timer.stop()

    def resume(self):
        if self._running:
            self._timer.start()

    def add_point(self, player_index: int, points: int = 10):
        if not self._running:
            return
        if player_index == 1:
            self._score1 += points
        elif player_index == 2:
            self._score2 += points
        self.score_changed.emit(self._score1, self._score2)

    @property
    def score1(self) -> int:
        return self._score1

    @property
    def score2(self) -> int:
        return self._score2

    @property
    def player1(self) -> str:
        return self._player1

    @property
    def player2(self) -> str:
        return self._player2

    @property
    def time_left(self) -> int:
        return self._time_left

    @property
    def elapsed_time(self) -> int:
        return GAME_DURATION_SECONDS - self._time_left

    @property
    def is_running(self) -> bool:
        return self._running

    def winner(self) -> str:
        if self._score1 > self._score2:
            return self._player1
        if self._score2 > self._score1:
            return self._player2
        return "Empate"

    def _on_tick(self):
        self._time_left -= 1
        self.tick.emit(self._time_left)
        if self._time_left <= 0:
            self.finish()
