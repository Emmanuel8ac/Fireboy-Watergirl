from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from logic.game_manager  import GameManager
from logic.audio_manager import AudioManager
from config import GAME_DURATION_SECONDS


class GameScreen(QWidget):

    def __init__(self, game_mgr: GameManager, audio: AudioManager):
        super().__init__()
        self._gm    = game_mgr
        self._audio = audio
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        top = QHBoxLayout()
        self.lbl_title = QLabel("⚡ PARTIDA EN CURSO ⚡")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 16, QFont.Bold))

        self.lbl_timer = QLabel(f"⏱ {GAME_DURATION_SECONDS}s")
        self.lbl_timer.setFont(QFont("Arial", 16, QFont.Bold))
        self.lbl_timer.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        top.addWidget(self.lbl_title, stretch=3)
        top.addWidget(self.lbl_timer, stretch=1)

        players_row = QHBoxLayout()
        self.lbl_player1 = QLabel("J1: —")
        self.lbl_player2 = QLabel("J2: —")
        for lbl in (self.lbl_player1, self.lbl_player2):
            lbl.setFont(QFont("Arial", 13))
        self.lbl_player2.setAlignment(Qt.AlignRight)
        players_row.addWidget(self.lbl_player1)
        players_row.addWidget(self.lbl_player2)

        self.game_area = QFrame()
        self.game_area.setMinimumHeight(220)
        area_layout = QVBoxLayout(self.game_area)

        hint = QLabel("Simula puntos con los botones de abajo")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #666; font-size: 12px;")

        sim_row = QHBoxLayout()
        self.btn_point1 = QPushButton("🔥  +10 pts")
        self.btn_point2 = QPushButton("💧  +10 pts")
        for btn in (self.btn_point1, self.btn_point2):
            btn.setFixedHeight(55)
            btn.setFont(QFont("Arial", 13))
        sim_row.addWidget(self.btn_point1)
        sim_row.addWidget(self.btn_point2)

        area_layout.addWidget(hint)
        area_layout.addStretch()
        area_layout.addLayout(sim_row)
        area_layout.addStretch()

        score_row = QHBoxLayout()
        self.lbl_score1 = QLabel("0")
        self.lbl_score2 = QLabel("0")
        vs_lbl          = QLabel("VS")
        for lbl in (self.lbl_score1, self.lbl_score2):
            lbl.setFont(QFont("Arial", 26, QFont.Bold))
            lbl.setAlignment(Qt.AlignCenter)
        vs_lbl.setAlignment(Qt.AlignCenter)
        vs_lbl.setFont(QFont("Arial", 14))
        score_row.addWidget(self.lbl_score1)
        score_row.addWidget(vs_lbl)
        score_row.addWidget(self.lbl_score2)

        self.btn_exit = QPushButton("TERMINAR PARTIDA")
        self.btn_exit.setFixedWidth(200)

        layout.addLayout(top)
        layout.addLayout(players_row)
        layout.addWidget(self.game_area)
        layout.addLayout(score_row)
        layout.addWidget(self.btn_exit, alignment=Qt.AlignCenter)

        self._apply_styles()

    def _connect_signals(self):
        self._gm.tick.connect(self._on_tick)
        self._gm.score_changed.connect(self._on_score_changed)
        self.btn_point1.clicked.connect(lambda: self._give_point(1))
        self.btn_point2.clicked.connect(lambda: self._give_point(2))

    def reset(self):
        self.lbl_player1.setText(f"J1: {self._gm.player1}")
        self.lbl_player2.setText(f"J2: {self._gm.player2}")
        self.btn_point1.setText(f"🔥  +10 pts  ({self._gm.player1})")
        self.btn_point2.setText(f"💧  +10 pts  ({self._gm.player2})")
        self.lbl_score1.setText("0")
        self.lbl_score2.setText("0")
        self.lbl_timer.setText(f"⏱ {GAME_DURATION_SECONDS}s")
        self.lbl_timer.setStyleSheet("")

    def show_game_over(self, score1: int, score2: int, winner: str):
        msg = QMessageBox(self)
        msg.setWindowTitle("¡Fin de la partida!")
        msg.setText(
            f"<b>Resultado final</b><br><br>"
            f"{self._gm.player1}: <b>{score1}</b> pts<br>"
            f"{self._gm.player2}: <b>{score2}</b> pts<br><br>"
            f"🏆 Ganador: <b>{winner}</b>"
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def _on_tick(self, seconds: int):
        self.lbl_timer.setText(f"⏱ {seconds}s")
        self.lbl_timer.setStyleSheet(
            "color: red; font-weight: bold;" if seconds <= 10 else ""
        )

    def _on_score_changed(self, s1: int, s2: int):
        self.lbl_score1.setText(str(s1))
        self.lbl_score2.setText(str(s2))

    def _give_point(self, player: int):
        self._gm.add_point(player)
        self._audio.play_effect("point")

    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame {
                border: 2px solid black;
                background-color: #e6d3a3;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #d9b38c;
                border: 2px solid black;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #c69c6d; }
            QLabel { font-size: 14px; }
        """)
