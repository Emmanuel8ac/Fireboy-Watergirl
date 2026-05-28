from PySide6.QtWidgets import QMainWindow, QStackedWidget

from config import WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH
from logic.audio_manager import AudioManager
from logic.game_manager import GameManager
from logic.network_manager import NetworkManager
from logic.score_manager import ScoreManager
from ui.screens.connection_screen import ConnectionScreen
from ui.screens.game_screen import GameScreen
from ui.screens.home_screen import HomeScreen
from ui.screens.level_select_screen import LevelSelectScreen
from ui.screens.player_setup_screen import PlayerSetupScreen
from ui.screens.scores_screen import ScoresScreen


# Controla el cambio entre pantallas
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.audio = AudioManager()
        self.score_mgr = ScoreManager()
        self.network = NetworkManager()
        self.game_mgr = GameManager(self)
        self.local_test_mode = False

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.home = HomeScreen(self.audio)
        self.connection = ConnectionScreen(self.network)
        self.player_setup = PlayerSetupScreen()
        self.level_select = LevelSelectScreen()
        self.game = GameScreen(self.game_mgr, self.audio, self.network)
        self.scores = ScoresScreen(self.score_mgr)

        for screen in (self.home, self.connection, self.player_setup, self.level_select, self.game, self.scores):
            self.stack.addWidget(screen)

        self._connect_signals()
        self.stack.setCurrentWidget(self.home)
        self.audio.play_music("menu")

    # Conecta botones y eventos de red
    def _connect_signals(self):
        self.home.btn_play.clicked.connect(self._open_connection)
        self.home.btn_scores.clicked.connect(self._show_scores)
        self.home.btn_exit.clicked.connect(self.close)

        self.connection.btn_back.clicked.connect(self._leave_connection)
        self.connection.btn_local_test.clicked.connect(self._start_local_test)
        self.connection.btn_create.clicked.connect(self._on_create)
        self.connection.btn_join.clicked.connect(self._on_join)
        self.network.status_changed.connect(self.connection.show_info)
        self.network.client_connected.connect(self._on_host_player_connected)
        self.network.remote_name_received.connect(self._on_remote_name_received)
        self.network.remote_character_selected.connect(self._on_remote_character_selected)
        self.network.session_ready.connect(self._on_remote_session_ready)

        self.player_setup.btn_back.clicked.connect(self._back_from_characters)
        self.player_setup.selection_changed.connect(self._send_character_selection)
        self.player_setup.continue_requested.connect(self._show_level_select)
        self.level_select.level_selected.connect(self._on_level_selected)
        self.level_select.btn_back.clicked.connect(self._back_from_level_select)

        self.game.btn_menu.clicked.connect(self._return_from_game_to_menu)
        self.game_mgr.level_completed.connect(self._on_level_completed)
        self.game_mgr.game_over.connect(self._on_game_over)
        self.scores.btn_back.clicked.connect(self._go_home)

    def _go_home(self):
        self.stack.setCurrentWidget(self.home)
        self.audio.stop_music()
        self.audio.play_music("menu")

    # Abre la creación o unión a sala
    def _open_connection(self):
        self.audio.play_effect("click")
        self.local_test_mode = False
        self.game.set_local_test_mode(False)
        self.network.disconnect(clear_name=True)
        self.connection.reset()
        self.stack.setCurrentWidget(self.connection)

    # Abre la selección de niveles para probar en local
    def _start_local_test(self):
        self.audio.play_effect("click")
        self.local_test_mode = True
        self.network.disconnect(clear_name=True)
        self.game.set_local_test_mode(True)
        self.game_mgr.setup("Fireboy", "Watergirl", "Fireboy", "Watergirl")
        self.level_select.configure_selection(True, local_test=True)
        self.stack.setCurrentWidget(self.level_select)

    def _leave_connection(self):
        self.network.disconnect(clear_name=True)
        self._go_home()

    def _name_is_valid(self) -> bool:
        name = self.connection.player_name()
        if len(name) < 2:
            self.connection.show_error("Escribe un nombre de al menos 2 caracteres para continuar.")
            return False
        self.network.set_local_name(name)
        return True

    def _on_create(self):
        if not self._name_is_valid():
            return
        code = self.network.create_room()
        if not code:
            self.connection.show_error(self.network.last_error or "No pude crear la sala.")
            return
        self.connection.set_code(code)
        self.connection.show_info(
            f"Sala de {self.network.local_name}: {code}. Esperando al segundo jugador."
        )

    def _on_join(self):
        if not self._name_is_valid():
            return
        code = self.connection.input_code.text()
        if self.network.join_room(code):
            self._open_online_characters()
        else:
            self.connection.show_error(
                self.network.last_error or "Código inválido: usa 6 letras o números."
            )

    def _on_host_player_connected(self):
        if self.network.is_host():
            self._open_online_characters()

    # Abre la elección de personajes
    def _open_online_characters(self):
        self.local_test_mode = False
        self.game.set_local_test_mode(False)
        self.network.send_player_name()
        self.player_setup.configure_online(
            self.network.is_host(), self.network.local_name, self.network.remote_name
        )
        if self.network.remote_character:
            self.player_setup.set_remote_character(
                self.network.remote_character, self.network.remote_name
            )
        self.stack.setCurrentWidget(self.player_setup)

    def _back_from_characters(self):
        self.network.disconnect()
        self.connection.reset()
        self.stack.setCurrentWidget(self.connection)

    def _on_remote_name_received(self, player_name: str):
        self.player_setup.set_remote_name(player_name)

    def _send_character_selection(self, character: str):
        self.network.send_character_choice(character)

    def _on_remote_character_selected(self, character: str, player_name: str):
        conflict = self.player_setup.set_remote_character(character, player_name)
        if conflict and self.network.is_host():
            self.network.send_character_choice(self.player_setup.my_character or "")

    # Permite al anfitrión escoger nivel
    def _show_level_select(self):
        if self.network.is_client():
            return
        self.audio.play_effect("click")
        self.level_select.configure_selection(True)
        self.stack.setCurrentWidget(self.level_select)

    # Regresa según el tipo de partida activa
    def _back_from_level_select(self):
        if self.local_test_mode:
            self.local_test_mode = False
            self.game.set_local_test_mode(False)
            self.stack.setCurrentWidget(self.connection)
            return
        self.stack.setCurrentWidget(self.player_setup)

    def _on_level_selected(self, level_number: int):
        if self.local_test_mode:
            self.audio.play_effect("click")
            self.game.set_level(level_number)
            self.game_mgr.setup("Fireboy", "Watergirl", "Fireboy", "Watergirl")
            self._start_game()
            return
        if self.network.is_client():
            return
        player1, player2 = self.player_setup.chosen_players()
        if not player1 or not player2:
            return
        self.audio.play_effect("click")
        self.game.set_level(level_number)
        self.game_mgr.setup(player1, player2, self.network.local_name, self.network.remote_name)
        if self.network.is_host() and self.network.is_connected():
            self.network.send_session_setup(level_number, player1, player2)
        self._start_game()

    def _on_remote_session_ready(self, setup: dict):
        if not self.network.is_client():
            return
        level_number = int(setup.get("level", 1))
        player1 = str(setup.get("player1", "Fireboy"))
        player2 = str(setup.get("player2", "Watergirl"))
        name1 = str(setup.get("player1_name", self.network.remote_name or "Jugador 1"))
        name2 = str(setup.get("player2_name", self.network.local_name or "Jugador 2"))
        self.game.set_level(level_number)
        self.game_mgr.setup(player1, player2, name1, name2)
        self._start_game()

    # Inicia la partida seleccionada
    def _start_game(self):
        self.audio.stop_music()
        self.audio.play_music("game")
        self.game.reset()
        self.stack.setCurrentWidget(self.game)
        self.game_mgr.start()
        self.game.start_level()

    def _return_from_game_to_menu(self):
        self.game.stop_level()
        self.game_mgr.abort()
        self.local_test_mode = False
        self.game.set_local_test_mode(False)
        self.network.disconnect(clear_name=True)
        self.connection.reset()
        self._go_home()

    # Guarda los puntos de ambos jugadores
    def _save_player_scores(self, score1: int, score2: int):
        if self.local_test_mode:
            return
        duration = self.game_mgr.elapsed_time
        self.score_mgr.add_score(self.game_mgr.name1, self.game_mgr.player1, score1, duration)
        self.score_mgr.add_score(self.game_mgr.name2, self.game_mgr.player2, score2, duration)

    # Regresa a niveles al completar el mapa
    def _on_level_completed(self, score1: int, score2: int):
        self.game.stop_level()
        self._save_player_scores(score1, score2)
        self.audio.stop_music()
        self.audio.play_effect("finish")
        self.audio.play_music("menu")
        self.level_select.configure_selection(not self.network.is_client(), local_test=self.local_test_mode)
        self.stack.setCurrentWidget(self.level_select)

    def _on_game_over(self, score1: int, score2: int):
        self.game.stop_level()
        self._save_player_scores(score1, score2)
        self.audio.stop_music()
        self.audio.play_effect("finish")
        self.game.show_game_over(score1, score2, self.game_mgr.winner())
        if self.local_test_mode:
            self.audio.play_music("menu")
            self.level_select.configure_selection(True, local_test=True)
            self.stack.setCurrentWidget(self.level_select)
            return
        self.network.disconnect(clear_name=True)
        self._show_scores()

    def _show_scores(self):
        self.scores.refresh()
        self.stack.setCurrentWidget(self.scores)

