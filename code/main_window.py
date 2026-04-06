from PySide6.QtWidgets import QMainWindow, QStackedWidget

from ui.screens.home_screen import HomeScreen
from ui.screens.player_setup_screen import PlayerSetupScreen
from ui.screens.connection_screen import ConnectionScreen
from ui.screens.game_screen import GameScreen
from ui.screens.scores_screen import ScoresScreen

from logic.network_manager import NetworkManager
from logic.game_manager import GameManager
from logic.audio_manager import AudioManager
from logic.score_manager import ScoreManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Juego")
        self.resize(800, 600)

        self.network = NetworkManager()
        self.game_mgr = GameManager()
        self.audio = AudioManager()
        self.score_mgr = ScoreManager()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home = HomeScreen(self.audio)

        self.player_setup = PlayerSetupScreen()
        self.connection = ConnectionScreen(self.network)
        self.game = GameScreen(self.game_mgr, self.audio)
        self.scores = ScoresScreen(self.score_mgr)

        self.stack.addWidget(self.home)
        self.stack.addWidget(self.player_setup)
        self.stack.addWidget(self.connection)
        self.stack.addWidget(self.game)
        self.stack.addWidget(self.scores)

        self.connect_signals()

        self.stack.setCurrentWidget(self.home)

        if self.audio.is_enabled():
            self.audio.play_music("menu")

    def connect_signals(self):
        self.home.btn_play.clicked.connect(self._go_to_player_setup)
        self.home.btn_scores.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.scores)
        )
        self.home.btn_exit.clicked.connect(self.close)

        self.player_setup.btn_ready.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.connection)
        )

        self.connection.btn_back.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.player_setup)
        )
        self.connection.btn_create.clicked.connect(self._start_game)
        self.connection.btn_join.clicked.connect(self._start_game)

        self.game.btn_exit.clicked.connect(self._end_game)

        self.scores.btn_back.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.home)
        )

    def _go_to_player_setup(self):
        self.audio.play_effect("click")
        self.stack.setCurrentWidget(self.player_setup)

    def _start_game(self):
        if self.audio.is_enabled():
            self.audio.play_music("game")

        self.game.reset()
        self.stack.setCurrentWidget(self.game)

    def _end_game(self):
        if self.audio.is_enabled():
            self.audio.play_music("menu")

        self.stack.setCurrentWidget(self.home)