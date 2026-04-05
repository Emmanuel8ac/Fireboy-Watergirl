from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QStackedLayout
from PySide6.QtGui import QMovie, QFont
from PySide6.QtCore import Qt


class HomeScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Layout principal
        self.stack = QStackedLayout()
        self.setLayout(self.stack)

        # FONDO ANIMADO

        self.background = QLabel()
        self.background.setScaledContents(True)

        self.movie = QMovie("resources/images/background.gif")
        self.background.setMovie(self.movie)
        self.movie.start()

        # CONTENEDOR DE BOTONES

        self.overlay = QWidget()
        self.overlay_layout = QVBoxLayout()
        self.overlay.setLayout(self.overlay_layout)

        # Fondo
        self.background_label = QLabel(self)
        pixmap = QPixmap("resources/images/portada.png")

        # TÍTULO

        self.lbl_title = QLabel("MI JUEGO")
        self.lbl_title.setAlignment(Qt.AlignCenter)

        font_title = QFont("Times New Roman", 32, QFont.Bold)
        self.lbl_title.setFont(font_title)

        # BOTONES

        self.btn_play = QPushButton("JUGAR")
        self.btn_scores = QPushButton("PUNTUACIONES")
        self.btn_exit = QPushButton("SALIR")

        # Estilo botones
        for btn in [self.btn_play, self.btn_scores, self.btn_exit]:
            btn.setFixedWidth(250)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 0, 0, 180);
                    color: gold;
                    border: 2px solid gold;
                    padding: 10px;
                    font-size: 18px;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 215, 0, 120);
                    color: black;
                }
            """)

        # AGREGAR AL LAYOUT

        self.overlay_layout.addWidget(self.lbl_title)
        self.overlay_layout.addWidget(self.btn_play)
        self.overlay_layout.addWidget(self.btn_scores)
        self.overlay_layout.addWidget(self.btn_exit)

        # STACK FINAL

        self.stack.addWidget(self.background)
        self.stack.addWidget(self.overlay)