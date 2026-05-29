from pathlib import Path
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout

from config import UI_DIR


class LevelSelectScreen(QWidget):

    level_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #151515; color: #f7d35c; }
            QLabel#title { font-size: 34px; font-weight: bold; color: #ffd84a; }
            QPushButton#level {
                background-color: #2b2b2b;
                border: 3px solid #d7aa25;
                color: #f7d35c;
                border-radius: 16px;
                font-size: 24px;
                font-weight: bold;
                min-width: 150px;
                min-height: 95px;
            }
            QPushButton#level:hover { background-color: #3d3420; border-color: #fff06a; }
            QPushButton#back {
                background-color: #d8aa62;
                border: 2px solid #2f1b0e;
                color: #21160e;
                padding: 9px 18px;
                border-radius: 8px;
                font-weight: bold;
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(45, 35, 45, 35)
        main.setSpacing(20)

        title = QLabel("Selecciona un nivel")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(22)
        grid.setVerticalSpacing(22)

        for i in range(1, 7):
            btn = QPushButton(f"Nivel {i}")
            btn.setObjectName("level")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, n=i: self.level_selected.emit(n))
            grid.addWidget(btn, (i - 1) // 3, (i - 1) % 3)

        main.addLayout(grid)
        hint = QLabel("Los niveles ya no son capturas pegadas: se generan con estructuras, colisiones, botones, compuertas, palancas, charcos, diamantes y portales.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 14px; color: #e8d29b;")
        main.addWidget(hint)

        bottom = QHBoxLayout()
        self.btn_back = QPushButton("REGRESAR")
        self.btn_back.setObjectName("back")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        bottom.addStretch()
        bottom.addWidget(self.btn_back)
        bottom.addStretch()
        main.addLayout(bottom)
