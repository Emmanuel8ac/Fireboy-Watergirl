import os
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class HomeScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Inicio")

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Fondo
        self.background_label = QLabel(self)
        pixmap = QPixmap("resources/images/portada.png")

        self.background_label.setPixmap(pixmap)
        self.background_label.setScaledContents(True)
        self.background_label.setGeometry(0, 0, 800, 600)

        # Layout para botones
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.setSpacing(20)

        # Botones
        self.btn_play = QPushButton("Jugar")
        self.btn_scores = QPushButton("Puntuaciones")
        self.btn_exit = QPushButton("Salir")

        # Estilo simple
        for btn in [self.btn_play, self.btn_scores, self.btn_exit]:
            btn.setFixedWidth(200)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 0, 0, 150);
                    color: white;
                    font-size: 16px;
                    padding: 10px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 200);
                }
            """)

        button_layout.addWidget(self.btn_play)
        button_layout.addWidget(self.btn_scores)
        button_layout.addWidget(self.btn_exit)

        main_layout.addStretch()
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

    def resizeEvent(self, event):
        self.background_label.setGeometry(0, 0, self.width(), self.height())