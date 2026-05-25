from PySide6.QtWidgets import QMainWindow, QStackedWidget

from ui.screens.home_screen import HomeScreen
from ui.screens.player_setup_screen import PlayerSetupScreen
from ui.screens.level_select_screen import LevelSelectScreen
from ui.screens.connection_screen import ConnectionScreen
from ui.screens.game_screen import GameScreen
from ui.screens.scores_screen import ScoresScreen

from logic.game_manager import GameManager
from logic.audio_manager import AudioManager
from logic.score_manager import ScoreManager
from logic.network_manager import NetworkManager
from config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.audio = AudioManager()
        self.score_mgr = ScoreManager()
        self.network = NetworkManager()
        self.game_mgr = GameManager(self)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home = HomeScreen(self.audio)
        self.level_select = LevelSelectScreen()
        self.player_setup = PlayerSetupScreen()
        self.connection = ConnectionScreen(self.network)
        self.game = GameScreen(self.game_mgr, self.audio, self.network)
        self.scores = ScoresScreen(self.score_mgr)

        for screen in (self.home, self.level_select, self.player_setup, self.connection, self.game, self.scores):
            self.stack.addWidget(screen)

        self._connect_signals()
        self.stack.setCurrentWidget(self.home)
        self.audio.play_music("menu")

    def _connect_signals(self):
        self.home.btn_play.clicked.connect(self._go_to_setup)
        self.home.btn_scores.clicked.connect(self._show_scores)
        self.home.btn_exit.clicked.connect(self.close)

        self.level_select.level_selected.connect(self._on_level_selected)
        self.level_select.btn_back.clicked.connect(self._go_home)

        self.player_setup.btn_ready.clicked.connect(self._on_players_ready)
        self.player_setup.btn_back.clicked.connect(self._go_home)

        self.connection.btn_back.clicked.connect(lambda: self.stack.setCurrentWidget(self.player_setup))
        self.connection.btn_create.clicked.connect(self._on_create)
        self.connection.btn_join.clicked.connect(self._on_join)
        self.connection.btn_local.clicked.connect(self._start_local_game)
        self.network.status_changed.connect(self.connection.show_info)
        self.network.client_connected.connect(self._start_game)

        self.game.btn_exit.clicked.connect(self._on_game_exit)
        self.game_mgr.game_over.connect(self._on_game_over)

        self.scores.btn_back.clicked.connect(self._go_home)

    def _go_home(self):
        self.stack.setCurrentWidget(self.home)
        self.audio.stop_music()
        self.audio.play_music("menu")

    def _go_to_setup(self):
        self.audio.play_effect("click")
        self.stack.setCurrentWidget(self.level_select)

    def _on_level_selected(self, level_number: int):
        self.audio.play_effect("click")
        self.game.set_level(level_number)
        self.player_setup.reset_selection()
        self.stack.setCurrentWidget(self.player_setup)

    def _on_players_ready(self):
        self.game_mgr.setup(self.player_setup.j1, self.player_setup.j2)
        self.connection.reset()
        self.stack.setCurrentWidget(self.connection)

    def _on_create(self):
        code = self.network.create_room()
        self.connection.set_code(code)
        self.connection.show_info(f"Código generado: {code}. Compártelo con el otro jugador. La partida iniciará automáticamente cuando se conecte.")

    def _on_join(self):
        code = self.connection.input_code.text()
        if self.network.join_room(code):
            self._start_game()
        else:
            self.connection.show_error(self.network.last_error or "Código inválido: usa 6 letras o números.")

    def _start_local_game(self):
        self.network.disconnect()
        self._start_game()

    def _start_game(self):
        self.audio.stop_music()
        self.audio.play_music("game")
        self.game.reset()
        self.stack.setCurrentWidget(self.game)
        self.game_mgr.start()
        self.game.start_level()

    def _on_game_exit(self):
        self.game.stop_level()
        self.game_mgr.abort()
        self.network.disconnect()
        self._go_home()

    def _on_game_over(self, score1: int, score2: int):
        self.game.stop_level()
        players = f"{self.game_mgr.player1} & {self.game_mgr.player2}"
        self.score_mgr.add_score(players, score1 + score2, self.game_mgr.elapsed_time)
        self.audio.stop_music()
        self.audio.play_effect("door")
        self.game.show_game_over(score1, score2, self.game_mgr.winner())
        self._show_scores()

    def _show_scores(self):
        self.scores.refresh()
        self.stack.setCurrentWidget(self.scores)
