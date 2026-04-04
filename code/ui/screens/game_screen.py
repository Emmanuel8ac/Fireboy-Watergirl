from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class GameScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_layout.setSpacing(20)

        self.lbl_title = QLabel("PANTALLA DE JUEGO")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 18, QFont.Bold))

        self.players_layout = QHBoxLayout()

        self.lbl_player1 = QLabel("J1: Fireboy")
        self.lbl_player2 = QLabel("J2: Watergirl")

        self.lbl_player1.setAlignment(Qt.AlignLeft)
        self.lbl_player2.setAlignment(Qt.AlignRight)

        self.players_layout.addWidget(self.lbl_player1)
        self.players_layout.addWidget(self.lbl_player2)

        self.game_area = QFrame()
        self.game_area.setMinimumHeight(250)

        self.game_area.setStyleSheet("""
            QFrame {
                border: 2px solid black;
                background-color: #e6d3a3;
            }
        """)

        self.lbl_game_placeholder = QLabel("Área de juego (simulación)")
        self.lbl_game_placeholder.setAlignment(Qt.AlignCenter)

        game_layout = QVBoxLayout()
        self.game_area.setLayout(game_layout)
        game_layout.addWidget(self.lbl_game_placeholder)

        self.score_layout = QHBoxLayout()

        self.lbl_score1 = QLabel("J1: 0")
        self.lbl_score2 = QLabel("J2: 0")

        self.score_layout.addWidget(self.lbl_score1)
        self.score_layout.addWidget(self.lbl_score2)

        self.btn_exit = QPushButton("TERMINAR PARTIDA")
        self.btn_exit.setFixedWidth(200)

        self.main_layout.addWidget(self.lbl_title)
        self.main_layout.addLayout(self.players_layout)
        self.main_layout.addWidget(self.game_area)
        self.main_layout.addLayout(self.score_layout)
        self.main_layout.addWidget(self.btn_exit, alignment=Qt.AlignCenter)

        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
            }

            QPushButton {
                background-color: #d9b38c;
                border: 2px solid black;
                padding: 8px;
                border-radius: 6px;
            }

            QPushButton:hover {
                background-color: #c69c6d;
            }
        """)