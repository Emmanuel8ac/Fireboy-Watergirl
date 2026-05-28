from PySide6.QtCore import QObject, QTimer, Signal
from config import GAME_DURATION_SECONDS


# Controla el tiempo y los puntos de la partida
class GameManager(QObject):
    # Señales usadas por las pantallas
    tick = Signal(int)
    score_changed = Signal(int, int)
    game_over = Signal(int, int)
    level_completed = Signal(int, int)

    # Datos iniciales de la partida
    def __init__(self, parent=None):
        super().__init__(parent)
        self._player1 = "Fireboy"
        self._player2 = "Watergirl"
        self._name1 = "Jugador 1"
        self._name2 = "Jugador 2"
        self._score1 = 0
        self._score2 = 0
        self._time_left = GAME_DURATION_SECONDS
        self._running = False

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)

    # Asigna nombres y personajes
    def setup(self, player1: str, player2: str, name1: str = "Jugador 1", name2: str = "Jugador 2"):
        self._player1 = player1 or "Fireboy"
        self._player2 = player2 or "Watergirl"
        self._name1 = name1 or "Jugador 1"
        self._name2 = name2 or "Jugador 2"

    # Inicia el nivel
    def start(self):
        self._score1 = 0
        self._score2 = 0
        self._time_left = GAME_DURATION_SECONDS
        self._running = True
        self._timer.start()
        self.score_changed.emit(self._score1, self._score2)
        self.tick.emit(self._time_left)

    # Termina la partida por tiempo
    def finish(self):
        if not self._running:
            return
        self._running = False
        self._timer.stop()
        self.game_over.emit(self._score1, self._score2)

    # Termina el nivel al llegar a las puertas
    def complete_level(self):
        if not self._running:
            return
        self._running = False
        self._timer.stop()
        self.level_completed.emit(self._score1, self._score2)

    # Cancela la partida actual
    def abort(self):
        self._running = False
        self._timer.stop()

    # Pausa el reloj
    def pause(self):
        if self._running:
            self._timer.stop()

    # Reanuda el reloj
    def resume(self):
        if self._running:
            self._timer.start()

    # Suma puntos al jugador que recoge un diamante
    def add_point(self, player_index: int, points: int = 10):
        if not self._running:
            return
        if player_index == 1:
            self._score1 += points
        elif player_index == 2:
            self._score2 += points
        self.score_changed.emit(self._score1, self._score2)

    # Datos consultados por la interfaz
    @property
    def score1(self) -> int:
        return self._score1

    # Devuelve los puntos del segundo jugador
    @property
    def score2(self) -> int:
        return self._score2

    # Devuelve el personaje del primer jugador
    @property
    def player1(self) -> str:
        return self._player1

    # Devuelve el personaje del segundo jugador
    @property
    def player2(self) -> str:
        return self._player2

    # Devuelve el nombre del primer jugador
    @property
    def name1(self) -> str:
        return self._name1

    # Devuelve el nombre del segundo jugador
    @property
    def name2(self) -> str:
        return self._name2

    # Devuelve el tiempo restante
    @property
    def time_left(self) -> int:
        return self._time_left

    # Devuelve el tiempo utilizado
    @property
    def elapsed_time(self) -> int:
        return GAME_DURATION_SECONDS - self._time_left

    # Comprueba el estado actual
    @property
    def is_running(self) -> bool:
        return self._running

    # Calcula el resultado final
    def winner(self) -> str:
        if self._score1 > self._score2:
            return self._name1
        if self._score2 > self._score1:
            return self._name2
        return "Empate"

    # Actualiza el reloj cada segundo
    def _on_tick(self):
        self._time_left -= 1
        self.tick.emit(self._time_left)
        if self._time_left <= 0:
            self.finish()
