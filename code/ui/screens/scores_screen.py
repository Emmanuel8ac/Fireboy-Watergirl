from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ScoresScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_layout.setSpacing(20)

        self.lbl_title = QLabel("PUNTUACIONES")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 18, QFont.Bold))

        self.list_scores = QListWidget()

        # Datos de prueba (estáticos)
        scores = [
            ("Fireboy & Watergirl", 100),
            ("Jugador1 & Jugador2", 85),
            ("Equipo X", 70),
            ("Equipo Y", 60)
        ]

        for name, score in scores:
            item = QListWidgetItem(f"{name} - {score} pts")
            self.list_scores.addItem(item)

        self.btn_back = QPushButton("REGRESAR")
        self.btn_back.setFixedWidth(150)

        self.main_layout.addWidget(self.lbl_title)
        self.main_layout.addWidget(self.list_scores)
        self.main_layout.addWidget(self.btn_back, alignment=Qt.AlignCenter)

        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QListWidget {
                background-color: #f2e3c6;
                border: 2px solid black;
                padding: 5px;
            }

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