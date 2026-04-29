import os
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt


class HomeScreen(QWidget):

    def __init__(self, audio):
        super().__init__()
        self._audio = audio
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        # ===== FONDO =====
        self.background_label = QLabel(self)
        bg_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "resources", "ui", "menu", "background_menu.png"
        )
        pixmap = QPixmap(bg_path)
        self.background_label.setPixmap(pixmap)
        self.background_label.setScaledContents(True)

        # ===== TÍTULO =====
        self.lbl_title = QLabel()
        title_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "resources", "ui", "menu", "title.png"
        )
        self.lbl_title.setPixmap(QPixmap(title_path))
        self.lbl_title.setAlignment(Qt.AlignCenter)

        # ===== BOTONES IMÁGENES =====
        self.btn_play = QPushButton()
        self.btn_scores = QPushButton()
        self.btn_credits = QPushButton()
        self.btn_exit = QPushButton()


        self._set_button_icon(self.btn_play, "btn_play", "1_up.png", scale=1.4)
        self._set_button_icon(self.btn_scores, "btn_highscores", "1_up.png", scale=0.9)
        self._set_button_icon(self.btn_credits, "btn_credits", "1_up.png", scale=0.9)
        self._set_button_icon(self.btn_exit, "", "exit.png", scale=0.9)

        # Layout botones
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.setSpacing(8)  # menos espacio

        button_layout.addWidget(self.btn_play, alignment=Qt.AlignCenter)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.btn_scores, alignment=Qt.AlignCenter)
        button_layout.addWidget(self.btn_credits, alignment=Qt.AlignCenter)
        button_layout.addSpacing(5)
        button_layout.addWidget(self.btn_exit, alignment=Qt.AlignCenter)

        # ===== AUDIO =====
        self.btn_audio = QPushButton(self)
        self.btn_audio.setFixedSize(50, 50)
        self.btn_audio.setStyleSheet("border: none;")
        self.btn_audio.clicked.connect(self._toggle_audio)

        self._update_audio_button()

        # ===== MAIN LAYOUT =====
        main_layout.addSpacing(40)  # espacio arriba
        main_layout.addWidget(self.lbl_title)
        main_layout.addSpacing(20)  # separación título-play
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

    # ===== BOTONES CON IMAGEN =====
    def _set_button_icon(self, button, dirname, filename, scale=1.0):
        path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "resources", "ui", "buttons", dirname, filename
        )

        pixmap = QPixmap(path)

        #Escalar imagen
        size = pixmap.size() * scale
        button.setIcon(QIcon(pixmap))
        button.setIconSize(size)

        #área clickeable más pequeña
        button.setFixedSize(size)

        button.setStyleSheet("border: none;")
        button.setCursor(Qt.PointingHandCursor)

    # ===== AUDIO =====
    def _toggle_audio(self):
        estado = self._audio.toggle_audio()

        if estado:
            self._audio.play_music("menu")
        else:
            self._audio.stop_music()

        self._update_audio_button()

    def _update_audio_button(self):
        icon = "1.png" if self._audio.is_enabled() else "1.png"

        path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "resources", "ui", "buttons", "btn_muter", icon
        )

        self.btn_audio.setIcon(QIcon(path))
        self.btn_audio.setIconSize(QPixmap(path).size())

    # ===== EVENTOS =====
    def showEvent(self, event):
        if self._audio.is_enabled():
            self._audio.play_music("menu")

    def resizeEvent(self, event):
        self.background_label.setGeometry(0, 0, self.width(), self.height())

        # posicionar botón audio abajo derecha
        self.btn_audio.move(self.width() - 60, self.height() - 60)