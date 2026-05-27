from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from logic.score_manager import ScoreManager


class ScoresScreen(QWidget):
    def __init__(self, score_mgr: ScoreManager):
        super().__init__()
        self._score_mgr = score_mgr
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        self.lbl_title = QLabel("HISTORIAL DE PUNTAJES")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 22, QFont.Bold))

        self.list_scores = QListWidget()
        self.list_scores.setAlternatingRowColors(True)
        self.list_scores.setFont(QFont("Courier New", 11))

        row = QHBoxLayout()
        self.btn_back = QPushButton("REGRESAR")
        self.btn_clear = QPushButton("LIMPIAR HISTORIAL")
        self.btn_back.setFixedWidth(170)
        self.btn_clear.setFixedWidth(210)
        self.btn_clear.clicked.connect(self._clear)
        row.addStretch()
        row.addWidget(self.btn_back)
        row.addWidget(self.btn_clear)
        row.addStretch()

        layout.addWidget(self.lbl_title)
        layout.addWidget(QLabel("    #   Jugador              Personaje      Puntos   Tiempo"))
        layout.addWidget(self.list_scores)
        layout.addLayout(row)
        self.refresh()
        self._apply_styles()

    def refresh(self):
        self.list_scores.clear()
        scores = self._score_mgr.get_scores()
        if not scores:
            self.list_scores.addItem("  Todavía no hay partidas guardadas")
            return
        for index, entry in enumerate(scores, start=1):
            name = entry.get("player_name") or entry.get("players", "-")
            character = entry.get("character", "Partida anterior")
            text = f"  {index:>2}. {name:<20} {character:<14} {entry.get('score', 0):>5} pts   {entry.get('duration', 0):>3}s"
            self.list_scores.addItem(QListWidgetItem(text))

    def _clear(self):
        self._score_mgr.clear()
        self.refresh()

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b1b12; color: #f6dfb4; }
            QListWidget { background-color: #f2e3c6; color: #21160e; border: 2px solid #4a2c19; padding: 6px; }
            QListWidget::item:alternate { background-color: #e6d0a5; }
            QPushButton { background-color: #d9b38c; border: 2px solid #2f1b0e; color: #21160e; padding: 8px; border-radius: 7px; font-weight: bold; }
            QPushButton:hover { background-color: #efc58b; }
        """)