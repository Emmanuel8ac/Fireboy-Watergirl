from PySide6.QtWidgets import QMainWindow, QStackedWidget

from ui.screens.home_screen import HomeScreen
from ui.screens.player_setup_screen import PlayerSetupScreen
from ui.screens.connection_screen import ConnectionScreen
from ui.screens.game_screen import GameScreen
from ui.screens.scores_screen import ScoresScreen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Juego")
        self.resize(800, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home = HomeScreen()
        self.player_setup = PlayerSetupScreen()
        self.connection = ConnectionScreen()
        self.game = GameScreen()
        self.scores = ScoresScreen()

        self.stack.addWidget(self.home)
        self.stack.addWidget(self.player_setup)
        self.stack.addWidget(self.connection)
        self.stack.addWidget(self.game)
        self.stack.addWidget(self.scores)

        self.connect_signals()

        self.stack.setCurrentWidget(self.home)

    def connect_signals(self):

        # home screen
        self.home.btn_play.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.player_setup)
        )
        self.home.btn_scores.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.scores)
        )
        self.home.btn_exit.clicked.connect(self.close)

        # player setup screen
        self.player_setup.btn_ready.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.connection)
        )

        # connection screen
        self.connection.btn_back.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.player_setup)
        )
        self.connection.btn_create.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.game)
        )
        self.connection.btn_join.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.game)
        )

        # game screen
        self.game.btn_exit.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.home)
        )

        # scores screen
        self.scores.btn_back.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.home)
        )