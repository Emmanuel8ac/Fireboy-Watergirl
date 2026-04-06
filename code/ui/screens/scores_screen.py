from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from logic.score_manager import ScoreManager


class ScoresScreen(QWidget):

    def __init__(self, score_mgr: ScoreManager):
        super().__init__()
        self._score_mgr = score_mgr
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        self.lbl_title = QLabel("🏆  PUNTUACIONES")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 18, QFont.Bold))

        header = QHBoxLayout()
        for text in ("#", "Jugadores", "Puntos", "Duración"):
            lbl = QLabel(text)
            lbl.setFont(QFont("Arial", 11, QFont.Bold))
            header.addWidget(lbl)

        self.list_scores = QListWidget()
        self.list_scores.setAlternatingRowColors(True)
        self.list_scores.setFont(QFont("Courier New", 12))

        btn_row = QHBoxLayout()
        self.btn_back  = QPushButton("REGRESAR")
        self.btn_clear = QPushButton("LIMPIAR HISTORIAL")
        self.btn_back.setFixedWidth(160)
        self.btn_clear.setFixedWidth(180)
        self.btn_clear.clicked.connect(self._clear)
        btn_row.addWidget(self.btn_back)
        btn_row.addWidget(self.btn_clear)

        layout.addWidget(self.lbl_title)
        layout.addLayout(header)
        layout.addWidget(self.list_scores)
        layout.addLayout(btn_row)

        self.refresh()
        self._apply_styles()

    def refresh(self):
        self.list_scores.clear()
        scores = self._score_mgr.get_scores()

        if not scores:
            self.list_scores.addItem("  Sin partidas registradas aún")
            return

        for i, entry in enumerate(scores, start=1):
            text = (
                f"  {i:>2}.  "
                f"{entry['players']:<28}"
                f"{entry['score']:>5} pts   "
                f"{entry['duration']} s"
            )
            self.list_scores.addItem(QListWidgetItem(text))

    def _clear(self):
        self._score_mgr.clear()
        self.refresh()

    def _apply_styles(self):
        self.setStyleSheet("""
            QListWidget {
                background-color: #f2e3c6;
                border: 2px solid black;
                padding: 5px;
            }
            QListWidget::item:alternate { background-color: #e8d5b0; }
            QLabel { font-size: 14px; }
            QPushButton {
                background-color: #d9b38c;
                border: 2px solid black;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #c69c6d; }
        """)