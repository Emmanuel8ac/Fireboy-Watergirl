"""
ui/main_window.py
-----------------
Ventana principal.
Crea los managers (lógica) y las pantallas (UI),
los conecta mediante señales/slots de Qt y controla
la navegación entre pantallas con QStackedWidget.
"""

from PySide6.QtWidgets import QMainWindow, QStackedWidget

from ui.screens.home_screen         import HomeScreen
from ui.screens.player_setup_screen import PlayerSetupScreen
from ui.screens.connection_screen   import ConnectionScreen
from ui.screens.game_screen         import GameScreen
from ui.screens.scores_screen       import ScoresScreen

from logic.game_manager    import GameManager
from logic.audio_manager   import AudioManager
from logic.score_manager   import ScoreManager
from logic.network_manager import NetworkManager

from config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # ── Managers (lógica, sin UI) ──────────────────────
        self.audio   = AudioManager()
        self.score_mgr  = ScoreManager()
        self.network = NetworkManager()
        self.game_mgr   = GameManager(self)

        # ── Pantallas ──────────────────────────────────────
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home         = HomeScreen()
        self.player_setup = PlayerSetupScreen()
        self.connection   = ConnectionScreen(self.network)
        self.game         = GameScreen(self.game_mgr, self.audio)
        self.scores       = ScoresScreen(self.score_mgr)

        for screen in (self.home, self.player_setup,
                       self.connection, self.game, self.scores):
            self.stack.addWidget(screen)

        self._connect_signals()

        # Pantalla inicial + música de menú
        self.stack.setCurrentWidget(self.home)
        self.audio.play_music("menu")

    # ── Señales ────────────────────────────────────────────
    def _connect_signals(self):

        # Home
        self.home.btn_play.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.player_setup))
        self.home.btn_scores.clicked.connect(self._show_scores)
        self.home.btn_exit.clicked.connect(self.close)

        # Player setup
        self.player_setup.btn_ready.clicked.connect(self._on_players_ready)

        # Connection
        self.connection.btn_back.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.player_setup))
        self.connection.btn_create.clicked.connect(self._on_create)
        self.connection.btn_join.clicked.connect(self._on_join)

        # Game
        self.game.btn_exit.clicked.connect(self._on_game_exit)
        self.game_mgr.game_over.connect(self._on_game_over)

        # Scores
        self.scores.btn_back.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.home))

    # ── Handlers ───────────────────────────────────────────
    def _on_players_ready(self):
        self.game_mgr.setup(self.player_setup.j1, self.player_setup.j2)
        self.stack.setCurrentWidget(self.connection)

    def _on_create(self):
        self.network.create_room()
        self._start_game()

    def _on_join(self):
        code = self.connection.input_code.text()
        if self.network.join_room(code):
            self._start_game()
        else:
            self.connection.show_error("Código inválido — debe tener 6 caracteres")

    def _start_game(self):
        self.audio.stop_music()
        self.audio.play_music("game")
        self.game.reset()              # actualiza nombres / marcador
        self.stack.setCurrentWidget(self.game)
        self.game_mgr.start()

    def _on_game_exit(self):
        self.game_mgr.end()            # detiene timer si corría
        self.network.disconnect()
        self.audio.stop_music()
        self.audio.play_music("menu")
        self.stack.setCurrentWidget(self.home)

    def _on_game_over(self, score1: int, score2: int):
        """Guarda puntuación y muestra diálogo de fin de partida."""
        players  = f"{self.game_mgr.player1} & {self.game_mgr.player2}"
        duration = 60 - self.game_mgr.time_left
        self.score_mgr.add_score(players, score1 + score2, duration)
        self.game.show_game_over(score1, score2, self.game_mgr.winner())

    def _show_scores(self):
        self.scores.refresh()
        self.stack.setCurrentWidget(self.scores)
